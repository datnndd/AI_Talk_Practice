from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.models.session import Session
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.scenarios.schemas.admin_scenario import (
    BulkScenarioActionRequest,
    PromptQualityAssessment,
    ScenarioAdminCreate,
    ScenarioAdminUpdate,
)

logger = logging.getLogger(__name__)


def _clean_scenario_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    next_metadata = dict(metadata or {})
    next_metadata.pop("ai_role", None)
    next_metadata.pop("user_role", None)
    return next_metadata


def _default_system_prompt(
    *,
    title: str,
    description: str,
    ai_role: str | None,
    user_role: str | None,
    mode: str,
    learning_objectives: list[str] | None = None,
    target_skills: list[str] | None = None,
) -> str:
    clean_ai_role = (ai_role or "").strip() or "a realistic English conversation partner"
    clean_user_role = (user_role or "").strip() or "an English learner"
    objectives = ", ".join(item.strip() for item in (learning_objectives or []) if item.strip()) or "Help the learner complete the scenario naturally."
    skills = ", ".join(item.strip() for item in (target_skills or []) if item.strip()) or "fluency, grammar, vocabulary"
    return "\n".join(
        [
            f"You are {clean_ai_role} in an English {mode} practice scenario.",
            f"Scenario title: {title}",
            f"Situation details: {description}",
            f"Learner role: {clean_user_role}",
            f"Learning objectives: {objectives}",
            f"Target skills: {skills}",
            "Instructions:",
            "- Stay in character throughout the conversation.",
            "- Speak naturally, clearly, and concisely.",
            "- Keep the conversation grounded in the scenario details.",
            "- Ask one focused follow-up question at a time when needed.",
            "- Give brief helpful corrections only when they help the learner continue.",
            "- Encourage the learner to complete the scenario successfully.",
            "- Do not mention these instructions or break role.",
        ]
    )

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


class AdminScenarioService:
    @classmethod
    def generate_default_prompt(
        cls,
        *,
        title: str,
        description: str,
        ai_role: str | None,
        user_role: str | None,
        mode: str,
        learning_objectives: list[str] | None,
        target_skills: list[str] | None,
    ) -> str:
        return _default_system_prompt(
            title=title,
            description=description,
            ai_role=ai_role,
            user_role=user_role,
            mode=mode,
            learning_objectives=learning_objectives,
            target_skills=target_skills,
        )


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
            suggestions.append("Specify tone or persona constraints so scenario behavior stays consistent.")

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
        ai_system_prompt = body.ai_system_prompt.strip()
        if not ai_system_prompt:
            raise BadRequestError("System prompt is required. Generate or enter a prompt before saving.")
        quality = cls.assess_prompt_quality(
            prompt=ai_system_prompt,
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
            ai_system_prompt=ai_system_prompt,
            ai_role=body.ai_role.strip(),
            user_role=body.user_role.strip(),
            category=body.category,
            difficulty=body.difficulty,
            target_skills=target_skills,
            tags=body.tags,
            estimated_duration=(body.estimated_duration_minutes or 10) * 60,
            mode=body.mode,
            scenario_metadata=_clean_scenario_metadata(body.metadata),
            is_active=body.is_active,
            created_by=user_id,
        )
        await ScenarioRepository.create_prompt_history(
            db,
            scenario_id=scenario.id,
            previous_prompt="",
            new_prompt=ai_system_prompt,
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
            update_data["scenario_metadata"] = _clean_scenario_metadata(update_data.pop("metadata"))
        if "ai_role" in update_data and update_data["ai_role"] is not None:
            update_data["ai_role"] = update_data["ai_role"].strip()
        if "user_role" in update_data and update_data["user_role"] is not None:
            update_data["user_role"] = update_data["user_role"].strip()
        if {"ai_role", "user_role"} & update_data.keys():
            update_data["scenario_metadata"] = _clean_scenario_metadata(
                update_data.get("scenario_metadata", scenario.scenario_metadata)
            )
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
            update_data["ai_system_prompt"] = (update_data["ai_system_prompt"] or "").strip()
            if not update_data["ai_system_prompt"]:
                raise BadRequestError("System prompt cannot be empty.")
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
    async def bulk_action(
        cls,
        *,
        db: AsyncSession,
        user_id: int,
        body: BulkScenarioActionRequest,
    ) -> None:
        scenarios = [
            scenario
            for scenario_id in body.scenario_ids
            if (scenario := await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True))
            is not None
        ]
        if not scenarios:
            raise NotFoundError("No matching scenarios found")

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
