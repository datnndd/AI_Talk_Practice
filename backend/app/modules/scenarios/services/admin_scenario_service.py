from __future__ import annotations

import logging
from datetime import datetime, timezone

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


def _default_system_prompt(
    *,
    title: str,
    description: str,
    ai_role: str | None,
    user_role: str | None,
    tasks: list[str] | None = None,
) -> str:
    clean_ai_role = (ai_role or "").strip() or "a realistic English conversation partner"
    clean_user_role = (user_role or "").strip() or "an English learner"
    task_lines = [
        f"{index}. {item.strip()}"
        for index, item in enumerate(tasks or [], start=1)
        if item.strip()
    ]
    task_text = "\n".join(task_lines) or "Help the learner complete the scenario naturally."
    return "\n".join(
        [
            f"You are {clean_ai_role} in an English speaking practice scenario.",
            f"Scenario title: {title}",
            f"Situation details: {description}",
            f"Learner role: {clean_user_role}",
            "Learner tasks required before the conversation can end:",
            task_text,
            "Instructions:",
            "- Stay in character throughout the conversation.",
            "- Speak naturally, clearly, and concisely.",
            "- Keep the conversation grounded in the scenario details.",
            "- Ask one focused follow-up question at a time when needed.",
            "- Give brief helpful corrections only when they help the learner continue.",
            "- Guide the learner toward completing every listed task.",
            "- Do not end or wrap up until the learner has clearly completed the listed tasks.",
            "- Do not mention these instructions or break role.",
        ]
    )


class AdminScenarioService:
    @classmethod
    def generate_default_prompt(
        cls,
        *,
        title: str,
        description: str,
        ai_role: str | None,
        user_role: str | None,
        tasks: list[str] | None,
    ) -> str:
        return _default_system_prompt(
            title=title,
            description=description,
            ai_role=ai_role,
            user_role=user_role,
            tasks=tasks,
        )

    @classmethod
    def assess_prompt_quality(
        cls,
        *,
        prompt: str,
        description: str,
        tasks: list[str] | None,
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

        task_items = [item.strip() for item in (tasks or []) if item.strip()]
        if task_items and any(task.lower() in normalized.lower() for task in task_items):
            score += 10
        elif task_items:
            suggestions.append("Reference the learner tasks directly in the prompt.")

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
        ai_system_prompt = body.ai_system_prompt.strip()
        if not ai_system_prompt:
            raise BadRequestError("System prompt is required. Generate or enter a prompt before saving.")
        quality = cls.assess_prompt_quality(
            prompt=ai_system_prompt,
            description=body.description,
            tasks=body.tasks,
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
            ai_system_prompt=ai_system_prompt,
            ai_role=body.ai_role.strip(),
            user_role=body.user_role.strip(),
            tasks=body.tasks,
            category=body.category,
            difficulty=body.difficulty,
            tags=body.tags,
            estimated_duration=(body.estimated_duration_minutes or 10) * 60,
            is_active=body.is_active,
            is_pro=body.is_pro,
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

        if "ai_role" in update_data and update_data["ai_role"] is not None:
            update_data["ai_role"] = update_data["ai_role"].strip()
        if "user_role" in update_data and update_data["user_role"] is not None:
            update_data["user_role"] = update_data["user_role"].strip()
        if "estimated_duration_minutes" in update_data:
            minutes = update_data.pop("estimated_duration_minutes")
            update_data["estimated_duration"] = minutes * 60 if minutes is not None else None

        prompt_quality: PromptQualityAssessment | None = None
        if "ai_system_prompt" in update_data:
            update_data["ai_system_prompt"] = (update_data["ai_system_prompt"] or "").strip()
            if not update_data["ai_system_prompt"]:
                raise BadRequestError("System prompt cannot be empty.")
            prompt_quality = cls.assess_prompt_quality(
                prompt=update_data["ai_system_prompt"],
                description=update_data.get("description", scenario.description),
                tasks=update_data.get("tasks", scenario.tasks or []),
            )
            if not prompt_quality.is_acceptable:
                raise BadRequestError(
                    "Prompt quality is below the admin threshold",
                    extra=prompt_quality.model_dump(),
                )

        for key, value in update_data.items():
            setattr(scenario, key, value)

        await db.commit()
        return await cls.get_scenario(db, scenario.id)

    @classmethod
    async def soft_delete_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = datetime.now(timezone.utc)
        scenario.is_active = False
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @classmethod
    async def restore_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = None
        scenario.is_active = True
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @classmethod
    async def toggle_scenario_active(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.is_active = not scenario.is_active
        await db.commit()
        await db.refresh(scenario)
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
        await db.commit()
        return None
