from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.scenario import Scenario, ScenarioVariation
from app.repositories.scenario_repository import ScenarioRepository
from app.schemas.session import SessionCreate

logger = logging.getLogger(__name__)


class VariationService:
    @staticmethod
    def build_variation_seed(
        *,
        scenario_id: int,
        parameters: dict[str, Any] | None,
        mode: str | None,
    ) -> str:
        normalized = json.dumps(
            {
                "scenario_id": scenario_id,
                "mode": mode,
                "parameters": parameters or {},
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def build_system_prompt_override(
        scenario: Scenario,
        *,
        mode: str | None,
        parameters: dict[str, Any],
    ) -> str:
        prompt_parts = [scenario.ai_system_prompt.strip()]
        effective_mode = mode or scenario.mode
        if effective_mode:
            prompt_parts.append(f"Conversation mode: {effective_mode}.")
        if parameters:
            prompt_parts.append(
                "Variation parameters:\n"
                + "\n".join(f"- {key}: {value}" for key, value in sorted(parameters.items()))
            )
        return "\n\n".join(part for part in prompt_parts if part)

    @staticmethod
    def build_sample_prompt(
        *,
        scenario: Scenario,
        mode: str | None,
        parameters: dict[str, Any],
    ) -> str | None:
        if not parameters:
            return None
        details = ", ".join(f"{key}={value}" for key, value in sorted(parameters.items()))
        return f"{scenario.title} [{mode or scenario.mode}] with {details}"

    @classmethod
    async def resolve_variation_for_session(
        cls,
        db: AsyncSession,
        *,
        scenario: Scenario,
        payload: SessionCreate,
    ) -> ScenarioVariation | None:
        if payload.variation_id is not None:
            variation = await ScenarioRepository.get_variation_by_id(
                db,
                payload.variation_id,
                scenario_id=scenario.id,
            )
            if variation is None:
                raise NotFoundError("Scenario variation not found")
            await ScenarioRepository.touch_variation_usage(variation)
            return variation

        if payload.prefer_pregenerated and not payload.variation_seed and not payload.variation_parameters:
            pregenerated = await ScenarioRepository.pick_pregenerated_variation(db, scenario.id)
            if pregenerated is not None:
                await ScenarioRepository.touch_variation_usage(pregenerated)
                return pregenerated

        if payload.variation_seed:
            existing = await ScenarioRepository.get_variation_by_seed(
                db,
                scenario_id=scenario.id,
                variation_seed=payload.variation_seed,
            )
            if existing is not None:
                await ScenarioRepository.touch_variation_usage(existing)
                return existing
            if not payload.create_variation_if_missing:
                raise NotFoundError("Scenario variation not found")

        if not payload.variation_seed and not payload.variation_parameters:
            return None

        if not payload.create_variation_if_missing:
            raise BadRequestError("Variation parameters were provided but variation creation is disabled")

        variation_seed = payload.variation_seed or cls.build_variation_seed(
            scenario_id=scenario.id,
            parameters=payload.variation_parameters,
            mode=payload.mode or scenario.mode,
        )
        existing = await ScenarioRepository.get_variation_by_seed(
            db,
            scenario_id=scenario.id,
            variation_seed=variation_seed,
        )
        if existing is not None:
            await ScenarioRepository.touch_variation_usage(existing)
            return existing

        try:
            async with db.begin_nested():
                variation = await ScenarioRepository.create_variation(
                    db,
                    scenario_id=scenario.id,
                    variation_seed=variation_seed,
                    parameters=payload.variation_parameters,
                    system_prompt_override=cls.build_system_prompt_override(
                        scenario,
                        mode=payload.mode,
                        parameters=payload.variation_parameters,
                    ),
                    sample_prompt=cls.build_sample_prompt(
                        scenario=scenario,
                        mode=payload.mode,
                        parameters=payload.variation_parameters,
                    ),
                    is_pregenerated=False,
                    generated_by_model=settings.llm_model,
                    generation_latency_ms=None,
                    is_approved=False,
                )
        except IntegrityError:
            # Race condition: another request created the same variation simultaneously.
            existing = await ScenarioRepository.get_variation_by_seed(
                db,
                scenario_id=scenario.id,
                variation_seed=variation_seed,
            )
            if existing is None:
                raise
            variation = existing

        await ScenarioRepository.touch_variation_usage(variation)
        logger.info("Used scenario variation id=%s for scenario id=%s", variation.id, scenario.id)
        return variation
