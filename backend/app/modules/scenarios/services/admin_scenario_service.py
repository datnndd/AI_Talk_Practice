from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from itertools import cycle
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.db.session import AsyncSessionLocal
from app.modules.scenarios.models import Scenario, ScenarioVariation
from app.modules.sessions.models.session import Session
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.scenarios.schemas import (
    BulkScenarioActionRequest,
    GenerateVariationsRequest,
    GenerationTaskRead,
    PromptQualityAssessment,
    ScenarioAdminCreate,
    ScenarioAdminUpdate,
    ScenarioVariationAdminCreate,
    ScenarioVariationAdminUpdate,
)
from app.services.base import Message
from app.infra.factory import create_llm
from app.modules.scenarios.services.variation_service import VariationService

logger = logging.getLogger(__name__)

SKILL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "pronunciation": ("pronunciation", "speak", "sounds", "accent", "clarity"),
    "fluency": ("fluency", "flow", "speak naturally", "hesitation", "confidence"),
    "grammar": ("grammar", "tense", "sentence", "correctly", "structure"),
    "vocabulary": ("vocabulary", "word choice", "phrase", "expressions", "terms"),
    "listening": ("listening", "understand", "follow", "respond quickly", "audio"),
    "negotiation": ("negotiate", "deal", "pricing", "convince", "persuade"),
    "small_talk": ("small talk", "casual", "introduce yourself", "social"),
    "presentation": ("present", "pitch", "explain clearly", "audience"),
}

CATEGORY_SKILL_HINTS: dict[str, list[str]] = {
    "travel": ["fluency", "vocabulary", "listening"],
    "business": ["negotiation", "presentation", "grammar"],
    "social": ["small_talk", "fluency", "pronunciation"],
    "interview": ["presentation", "grammar", "fluency"],
}


@dataclass
class GenerationTaskState:
    task_id: str
    status: str = "queued"
    scenario_ids: list[int] = field(default_factory=list)
    created_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


class AdminScenarioService:
    _tasks: dict[str, GenerationTaskState] = {}

    @classmethod
    def suggest_target_skills(cls, description: str, category: str | None = None) -> list[str]:
        haystack = f"{category or ''} {description}".lower()
        matches = set(CATEGORY_SKILL_HINTS.get((category or "").lower(), []))
        for skill, keywords in SKILL_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                matches.add(skill)
        if not matches:
            matches.update(["fluency", "vocabulary"])
        return sorted(matches)

    @classmethod
    def assess_prompt_quality(
        cls,
        *,
        prompt: str,
        description: str,
        target_skills: list[str] | None,
    ) -> PromptQualityAssessment:
        normalized = (prompt or "").strip()
        warnings: list[str] = []
        suggestions: list[str] = []
        score = 25

        if len(normalized) >= 80:
            score += 15
        else:
            warnings.append("System prompt is too short for a reusable teaching scenario.")
            suggestions.append("Add role, constraints, and coaching behavior details.")

        if any(marker in normalized.lower() for marker in ("you are", "your role", "act as")):
            score += 15
        else:
            warnings.append("Prompt should explicitly define the AI partner's role.")

        if any(marker in normalized.lower() for marker in ("ask follow-up", "follow-up", "clarify")):
            score += 10
        else:
            suggestions.append("Tell the AI when to ask follow-up questions.")

        if any(marker in normalized.lower() for marker in ("stay in character", "tone", "persona")):
            score += 10
        else:
            suggestions.append("Specify tone or persona constraints so variations stay consistent.")

        if any(marker in normalized.lower() for marker in ("correct", "feedback", "coach", "encourage")):
            score += 10
        else:
            suggestions.append("Include correction or coaching behavior for the learner.")

        if description and description.lower() in normalized.lower():
            score += 5

        skills = target_skills or []
        if skills and any(skill.replace("_", " ") in normalized.lower() for skill in skills):
            score += 10
        elif skills:
            suggestions.append("Reference the target skills directly in the prompt.")

        if any(marker in normalized.lower() for marker in ("avoid", "do not", "never")):
            score += 5
        else:
            suggestions.append("Add at least one negative constraint to reduce prompt drift.")

        if len(normalized.split()) >= 35:
            score += 10

        score = max(0, min(score, 100))
        if score < 70 and "System prompt is too short for a reusable teaching scenario." not in warnings:
            warnings.append("Prompt quality is below the admin threshold.")

        return PromptQualityAssessment(
            score=score,
            is_acceptable=score >= 70,
            warnings=warnings,
            suggestions=suggestions,
            recommended_target_skills=cls.suggest_target_skills(description, None),
        )

    @staticmethod
    async def _scenario_usage_counts(db: AsyncSession, scenario_ids: list[int]) -> dict[int, int]:
        if not scenario_ids:
            return {}
        stmt = (
            select(Session.scenario_id, func.count(Session.id))
            .where(Session.scenario_id.in_(scenario_ids), Session.deleted_at.is_(None))
            .group_by(Session.scenario_id)
        )
        rows = (await db.execute(stmt)).all()
        return {scenario_id: int(count) for scenario_id, count in rows}

    @classmethod
    async def get_scenario_usage_count(cls, db: AsyncSession, scenario_id: int) -> int:
        return (await cls._scenario_usage_counts(db, [scenario_id])).get(scenario_id, 0)

    @classmethod
    async def list_scenarios(
        cls,
        db: AsyncSession,
        *,
        search: str | None,
        category: str | None,
        difficulty: str | None,
        tag: str | None,
        include_deleted: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Scenario], dict[int, int], int]:
        scenarios, total = await ScenarioRepository.list_admin_scenarios(
            db,
            search=search,
            category=category,
            difficulty=difficulty,
            tag=tag,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )
        usage_counts = await cls._scenario_usage_counts(db, [scenario.id for scenario in scenarios])
        return scenarios, usage_counts, total

    @staticmethod
    async def get_scenario(db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True)
        if scenario is None:
            raise NotFoundError("Scenario not found")
        return scenario

    @classmethod
    async def create_scenario(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        body: ScenarioAdminCreate,
    ) -> Scenario:
        target_skills = body.target_skills or cls.suggest_target_skills(body.description, body.category)
        quality = cls.assess_prompt_quality(
            prompt=body.ai_system_prompt,
            description=body.description,
            target_skills=target_skills,
        )
        if not quality.is_acceptable:
            raise BadRequestError(
                "Prompt quality is below the admin threshold",
                extra=quality.model_dump(),
            )

        scenario = await ScenarioRepository.create(
            db,
            title=body.title,
            description=body.description,
            learning_objectives=body.learning_objectives,
            ai_system_prompt=body.ai_system_prompt,
            category=body.category,
            difficulty=body.difficulty,
            target_skills=target_skills,
            tags=body.tags,
            estimated_duration=(body.estimated_duration_minutes or 10) * 60,
            mode=body.mode,
            scenario_metadata=body.metadata,
            is_active=body.is_active,
            is_pre_generated=body.is_pre_generated,
            pre_gen_count=body.pre_gen_count,
            created_by=user_id,
        )
        await ScenarioRepository.create_prompt_history(
            db,
            scenario_id=scenario.id,
            previous_prompt="",
            new_prompt=body.ai_system_prompt,
            change_note=body.change_note or "Initial prompt",
            quality_score=quality.score,
            changed_by=user_id,
        )
        await db.commit()
        return await cls.get_scenario(db, scenario.id)

    @classmethod
    async def update_scenario(
        cls,
        db: AsyncSession,
        *,
        scenario_id: int,
        user_id: int,
        body: ScenarioAdminUpdate,
    ) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        update_data = body.model_dump(exclude_unset=True)

        if "metadata" in update_data:
            update_data["scenario_metadata"] = update_data.pop("metadata")
        if "estimated_duration_minutes" in update_data:
            minutes = update_data.pop("estimated_duration_minutes")
            update_data["estimated_duration"] = minutes * 60 if minutes is not None else None

        if (
            ("description" in update_data or "category" in update_data)
            and "target_skills" not in update_data
            and not scenario.target_skills
        ):
            update_data["target_skills"] = cls.suggest_target_skills(
                update_data.get("description", scenario.description),
                update_data.get("category", scenario.category),
            )

        prompt_quality: PromptQualityAssessment | None = None
        if "ai_system_prompt" in update_data:
            prompt_quality = cls.assess_prompt_quality(
                prompt=update_data["ai_system_prompt"],
                description=update_data.get("description", scenario.description),
                target_skills=update_data.get("target_skills", scenario.target_skills or []),
            )
            if not prompt_quality.is_acceptable:
                raise BadRequestError(
                    "Prompt quality is below the admin threshold",
                    extra=prompt_quality.model_dump(),
                )

        change_note = update_data.pop("change_note", None)
        previous_prompt = scenario.ai_system_prompt
        for key, value in update_data.items():
            setattr(scenario, key, value)

        if prompt_quality and previous_prompt != scenario.ai_system_prompt:
            await ScenarioRepository.create_prompt_history(
                db,
                scenario_id=scenario.id,
                previous_prompt=previous_prompt,
                new_prompt=scenario.ai_system_prompt,
                change_note=change_note or "Prompt updated",
                quality_score=prompt_quality.score,
                changed_by=user_id,
            )

        await db.commit()
        return await cls.get_scenario(db, scenario.id)

    @classmethod
    async def soft_delete_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = datetime.now(timezone.utc)
        scenario.is_active = False
        await db.commit()
        return scenario

    @classmethod
    async def restore_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = None
        scenario.is_active = True
        await db.commit()
        return scenario

    @classmethod
    async def toggle_scenario_active(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.is_active = not scenario.is_active
        await db.commit()
        return scenario

    @classmethod
    async def list_variations(
        cls,
        db: AsyncSession,
        *,
        scenario_id: int,
        search: str | None = None,
    ) -> list[ScenarioVariation]:
        await cls.get_scenario(db, scenario_id)
        return await ScenarioRepository.list_admin_variations(
            db,
            scenario_id=scenario_id,
            search=search,
            include_inactive=True,
        )

    @staticmethod
    async def get_variation(db: AsyncSession, variation_id: int) -> ScenarioVariation:
        variation = await ScenarioRepository.get_variation_by_id(db, variation_id)
        if variation is None:
            raise NotFoundError("Scenario variation not found")
        return variation

    @classmethod
    async def create_variation(
        cls,
        db: AsyncSession,
        *,
        body: ScenarioVariationAdminCreate,
    ) -> ScenarioVariation:
        scenario = await cls.get_scenario(db, body.scenario_id)
        variation_seed = body.variation_seed or VariationService.build_variation_seed(
            scenario_id=scenario.id,
            parameters=body.parameters,
            mode=scenario.mode,
        )
        existing = await ScenarioRepository.get_variation_by_seed(
            db,
            scenario_id=scenario.id,
            variation_seed=variation_seed,
        )
        if existing is not None:
            raise BadRequestError("A variation with the same parameters already exists")

        variation = await ScenarioRepository.create_variation(
            db,
            scenario_id=scenario.id,
            variation_seed=variation_seed,
            variation_name=body.variation_name,
            parameters=body.parameters,
            sample_prompt=body.sample_prompt,
            sample_conversation=body.sample_conversation,
            system_prompt_override=body.system_prompt_override
            or VariationService.build_system_prompt_override(
                scenario,
                mode=scenario.mode,
                parameters=body.parameters,
            ),
            is_active=body.is_active,
            is_pregenerated=body.is_pregenerated,
            is_approved=body.is_approved,
            generated_by_model=settings.llm_model if body.is_pregenerated else None,
        )
        await db.commit()
        await db.refresh(variation)
        return variation

    @classmethod
    async def update_variation(
        cls,
        db: AsyncSession,
        *,
        variation_id: int,
        body: ScenarioVariationAdminUpdate,
    ) -> ScenarioVariation:
        variation = await cls.get_variation(db, variation_id)
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(variation, key, value)
        await db.commit()
        await db.refresh(variation)
        return variation

    @classmethod
    async def soft_delete_variation(cls, db: AsyncSession, variation_id: int) -> ScenarioVariation:
        variation = await cls.get_variation(db, variation_id)
        variation.is_active = False
        await db.commit()
        return variation

    @classmethod
    async def bulk_action(
        cls,
        *,
        db: AsyncSession,
        user_id: int,
        body: BulkScenarioActionRequest,
    ) -> GenerationTaskRead | None:
        scenarios = [
            scenario
            for scenario_id in body.scenario_ids
            if (scenario := await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True))
            is not None
        ]
        if not scenarios:
            raise NotFoundError("No matching scenarios found")

        if body.action == "generate_variations":
            return cls.start_generation_task(
                scenario_ids=[scenario.id for scenario in scenarios],
                count=body.generation_count or 8,
                approve_generated=True,
            )

        for scenario in scenarios:
            if body.action == "activate":
                scenario.is_active = True
            elif body.action == "deactivate":
                scenario.is_active = False
            elif body.action == "soft_delete":
                scenario.deleted_at = datetime.now(timezone.utc)
                scenario.is_active = False
                await ScenarioRepository.create_prompt_history(
                    db,
                    scenario_id=scenario.id,
                    previous_prompt=scenario.ai_system_prompt,
                    new_prompt=scenario.ai_system_prompt,
                    change_note="Scenario soft deleted",
                    quality_score=None,
                    changed_by=user_id,
                )
        await db.commit()
        return None

    @classmethod
    def start_generation_task(
        cls,
        *,
        scenario_ids: list[int],
        count: int,
        approve_generated: bool,
        overwrite_existing: bool = False,
    ) -> GenerationTaskRead:
        task_id = str(uuid.uuid4())
        state = GenerationTaskState(task_id=task_id, scenario_ids=scenario_ids)
        cls._tasks[task_id] = state
        asyncio.create_task(
            cls._run_generation_task(
                task_id=task_id,
                scenario_ids=scenario_ids,
                count=count,
                approve_generated=approve_generated,
                overwrite_existing=overwrite_existing,
            )
        )
        return GenerationTaskRead(**asdict(state))

    @classmethod
    def get_task(cls, task_id: str) -> GenerationTaskRead:
        state = cls._tasks.get(task_id)
        if state is None:
            raise NotFoundError("Generation task not found")
        return GenerationTaskRead(**asdict(state))

    @classmethod
    async def start_generation_for_single_scenario(
        cls,
        *,
        scenario_id: int,
        body: GenerateVariationsRequest,
    ) -> GenerationTaskRead:
        return cls.start_generation_task(
            scenario_ids=[scenario_id],
            count=body.count,
            approve_generated=body.approve_generated,
            overwrite_existing=body.overwrite_existing,
        )

    @classmethod
    async def _run_generation_task(
        cls,
        *,
        task_id: str,
        scenario_ids: list[int],
        count: int,
        approve_generated: bool,
        overwrite_existing: bool,
    ) -> None:
        state = cls._tasks[task_id]
        state.status = "running"
        llm = None

        try:
            llm = create_llm(settings)
            async with AsyncSessionLocal() as db:
                for scenario_id in scenario_ids:
                    scenario = await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True)
                    if scenario is None:
                        state.errors.append(f"Scenario {scenario_id} was not found")
                        continue
                    blueprints = await cls._generate_variation_blueprints(scenario, count=count, llm=llm)
                    created, skipped = await cls._persist_generated_variations(
                        db=db,
                        scenario=scenario,
                        blueprints=blueprints,
                        approve_generated=approve_generated,
                        overwrite_existing=overwrite_existing,
                    )
                    state.created_count += created
                    state.skipped_count += skipped
                    await db.commit()
            state.status = "completed"
        except Exception as exc:
            logger.exception("Variation generation task failed")
            state.status = "failed"
            state.errors.append(str(exc))
        finally:
            state.finished_at = datetime.now(timezone.utc)
            if llm is not None:
                await llm.close()

    @classmethod
    async def _generate_variation_blueprints(
        cls,
        scenario: Scenario,
        *,
        count: int,
        llm: Any,
    ) -> list[dict[str, Any]]:
        prompt = cls._build_variation_generation_prompt(scenario, count)
        raw_output = ""
        try:
            async for chunk in llm.chat_stream(
                messages=[Message(role="user", content=prompt)],
                system_prompt="Return only valid JSON.",
            ):
                raw_output += chunk
        except Exception:
            logger.exception("LLM variation generation failed, using heuristic fallback")

        parsed = cls._parse_variation_blueprints(raw_output)
        if parsed:
            return parsed[:count]
        return cls._heuristic_variation_blueprints(scenario, count)

    @staticmethod
    def _build_variation_generation_prompt(scenario: Scenario, count: int) -> str:
        return (
            "Generate scenario variations for a language-learning admin panel.\n"
            f"Scenario title: {scenario.title}\n"
            f"Description: {scenario.description}\n"
            f"Category: {scenario.category}\n"
            f"Difficulty: {scenario.difficulty}\n"
            f"Target skills: {json.dumps(scenario.target_skills or [])}\n"
            f"Base prompt: {scenario.ai_system_prompt}\n"
            f"Return {count} JSON array items. "
            "Each item must include variation_name, parameters, sample_prompt, sample_conversation.\n"
            "sample_conversation must be a list of 2-4 objects with role and content.\n"
            "Do not include markdown."
        )

    @staticmethod
    def _parse_variation_blueprints(raw_output: str) -> list[dict[str, Any]]:
        if not raw_output:
            return []
        start = raw_output.find("[")
        end = raw_output.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            payload = json.loads(raw_output[start : end + 1])
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    @classmethod
    def _heuristic_variation_blueprints(cls, scenario: Scenario, count: int) -> list[dict[str, Any]]:
        tones = cycle(["formal", "friendly", "urgent", "warm", "assertive"])
        twists = cycle(
            [
                "first-time learner",
                "time pressure",
                "unexpected misunderstanding",
                "follow-up question required",
                "confidence-building opener",
            ]
        )
        skill_cycle = cycle(scenario.target_skills or ["fluency", "vocabulary"])
        blueprints: list[dict[str, Any]] = []

        for index in range(count):
            tone = next(tones)
            twist = next(twists)
            focus_skill = next(skill_cycle)
            parameters = {
                "tone": tone,
                "twist": twist,
                "focus_skill": focus_skill,
            }
            blueprints.append(
                {
                    "variation_name": f"{scenario.title} Variant {index + 1}",
                    "parameters": parameters,
                    "sample_prompt": f"{scenario.title} with a {tone} tone and {twist}.",
                    "sample_conversation": [
                        {"role": "assistant", "content": f"Welcome. Let's begin this {tone} scenario."},
                        {
                            "role": "user",
                            "content": f"I want to practise {focus_skill.replace('_', ' ')} in a {scenario.category} setting.",
                        },
                        {
                            "role": "assistant",
                            "content": f"Great. I will introduce a {twist} while keeping the learner engaged.",
                        },
                    ],
                }
            )
        return blueprints

    @classmethod
    async def _persist_generated_variations(
        cls,
        *,
        db: AsyncSession,
        scenario: Scenario,
        blueprints: list[dict[str, Any]],
        approve_generated: bool,
        overwrite_existing: bool,
    ) -> tuple[int, int]:
        created = 0
        skipped = 0
        for blueprint in blueprints:
            parameters = blueprint.get("parameters") or {}
            seed = VariationService.build_variation_seed(
                scenario_id=scenario.id,
                parameters=parameters,
                mode=scenario.mode,
            )
            existing = await ScenarioRepository.get_variation_by_seed(
                db,
                scenario_id=scenario.id,
                variation_seed=seed,
            )
            if existing and not overwrite_existing:
                skipped += 1
                continue

            payload = {
                "scenario_id": scenario.id,
                "variation_seed": seed,
                "variation_name": blueprint.get("variation_name") or f"{scenario.title} Variant",
                "parameters": parameters,
                "sample_prompt": blueprint.get("sample_prompt")
                or VariationService.build_sample_prompt(
                    scenario=scenario,
                    mode=scenario.mode,
                    parameters=parameters,
                ),
                "sample_conversation": blueprint.get("sample_conversation") or [],
                "system_prompt_override": VariationService.build_system_prompt_override(
                    scenario,
                    mode=scenario.mode,
                    parameters=parameters,
                ),
                "is_active": True,
                "is_pregenerated": True,
                "is_approved": approve_generated,
                "generated_by_model": settings.llm_model,
            }

            try:
                if existing and overwrite_existing:
                    for key, value in payload.items():
                        if key not in {"scenario_id", "variation_seed"}:
                            setattr(existing, key, value)
                else:
                    await ScenarioRepository.create_variation(db, **payload)
                created += 1
            except IntegrityError:
                skipped += 1
        return created, skipped
