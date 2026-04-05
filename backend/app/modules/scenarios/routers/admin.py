from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import (
    BulkScenarioActionRequest,
    BulkScenarioActionResponse,
    GenerateVariationsRequest,
    GenerationTaskRead,
    PromptHistoryRead,
    ScenarioAdminCreate,
    ScenarioAdminRead,
    ScenarioAdminUpdate,
    ScenarioListResponse,
    ScenarioVariationAdminCreate,
    ScenarioVariationAdminRead,
    ScenarioVariationAdminUpdate,
    SuggestSkillsRequest,
    SuggestSkillsResponse,
    VariationListResponse,
)
from app.modules.scenarios.serializers import (
    serialize_admin_prompt_history,
    serialize_admin_scenario,
    serialize_admin_variation,
)
from app.modules.scenarios.services.admin_scenario_service import AdminScenarioService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scenarios/suggest-skills", response_model=SuggestSkillsResponse)
async def suggest_skills(
    body: SuggestSkillsRequest,
    _: User = Depends(require_admin_user),
):
    suggested = AdminScenarioService.suggest_target_skills(body.description, body.category)
    return SuggestSkillsResponse(suggested_skills=suggested)


# NOTE: This MUST be declared before /scenarios/{scenario_id} routes so FastAPI
# doesn't try to parse the literal string "bulk-actions" as an integer ID.
@router.post("/scenarios/bulk-actions", response_model=BulkScenarioActionResponse)
async def bulk_admin_scenario_action(
    body: BulkScenarioActionRequest,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
):
    task = await AdminScenarioService.bulk_action(db=db, user_id=user.id, body=body)
    if task is not None:
        return BulkScenarioActionResponse(
            success=True,
            message="Background generation started",
            task=task,
        )
    return BulkScenarioActionResponse(success=True, message="Bulk action applied")


@router.get("/scenarios", response_model=ScenarioListResponse)
async def list_admin_scenarios(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenarios, usage_counts, total = await AdminScenarioService.list_scenarios(
        db,
        search=search,
        category=category,
        difficulty=difficulty,
        tag=tag,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )
    items = [
        serialize_admin_scenario(
            scenario,
            usage_count=usage_counts.get(scenario.id, 0),
            latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
                prompt=scenario.ai_system_prompt,
                description=scenario.description,
                target_skills=scenario.target_skills or [],
            ),
            include_variations=False,
            include_prompt_history=False,
        )
        for scenario in scenarios
    ]
    return ScenarioListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/scenarios", response_model=ScenarioAdminRead, status_code=status.HTTP_201_CREATED)
async def create_admin_scenario(
    body: ScenarioAdminCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.create_scenario(db, user_id=user.id, body=body)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.get("/scenarios/{scenario_id}", response_model=ScenarioAdminRead)
async def get_admin_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.get_scenario(db, scenario_id)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.put("/scenarios/{scenario_id}", response_model=ScenarioAdminRead)
async def update_admin_scenario(
    scenario_id: int,
    body: ScenarioAdminUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.update_scenario(db, scenario_id=scenario_id, user_id=user.id, body=body)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.delete("/scenarios/{scenario_id}", response_model=ScenarioAdminRead)
async def delete_admin_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.soft_delete_scenario(db, scenario_id)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.post("/scenarios/{scenario_id}/restore", response_model=ScenarioAdminRead)
async def restore_admin_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.restore_scenario(db, scenario_id)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.post("/scenarios/{scenario_id}/toggle-active", response_model=ScenarioAdminRead)
async def toggle_admin_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.toggle_scenario_active(db, scenario_id)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(
        scenario,
        usage_count=usage_count,
        latest_prompt_quality=AdminScenarioService.assess_prompt_quality(
            prompt=scenario.ai_system_prompt,
            description=scenario.description,
            target_skills=scenario.target_skills or [],
        ),
    )


@router.get("/scenarios/{scenario_id}/prompt-history", response_model=list[PromptHistoryRead])
async def get_prompt_history(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    scenario = await AdminScenarioService.get_scenario(db, scenario_id)
    return [serialize_admin_prompt_history(item) for item in scenario.prompt_history]


@router.post("/scenarios/{scenario_id}/generate-variations", response_model=GenerationTaskRead)
async def generate_variations_for_scenario(
    scenario_id: int,
    body: GenerateVariationsRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminScenarioService.get_scenario(db, scenario_id)
    return await AdminScenarioService.start_generation_for_single_scenario(scenario_id=scenario_id, body=body)




@router.get("/scenario-variations", response_model=VariationListResponse)
async def list_admin_variations(
    scenario_id: int = Query(..., ge=1),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    variations = await AdminScenarioService.list_variations(db, scenario_id=scenario_id, search=search)
    items = [serialize_admin_variation(item) for item in variations]
    return VariationListResponse(items=items, total=len(items))


@router.post("/scenario-variations", response_model=ScenarioVariationAdminRead, status_code=status.HTTP_201_CREATED)
async def create_admin_variation(
    body: ScenarioVariationAdminCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    variation = await AdminScenarioService.create_variation(db, body=body)
    return serialize_admin_variation(variation)


@router.get("/scenario-variations/{variation_id}", response_model=ScenarioVariationAdminRead)
async def get_admin_variation(
    variation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    variation = await AdminScenarioService.get_variation(db, variation_id)
    return serialize_admin_variation(variation)


@router.put("/scenario-variations/{variation_id}", response_model=ScenarioVariationAdminRead)
async def update_admin_variation(
    variation_id: int,
    body: ScenarioVariationAdminUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    variation = await AdminScenarioService.update_variation(db, variation_id=variation_id, body=body)
    return serialize_admin_variation(variation)


@router.delete("/scenario-variations/{variation_id}", response_model=ScenarioVariationAdminRead)
async def delete_admin_variation(
    variation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    variation = await AdminScenarioService.soft_delete_variation(db, variation_id)
    return serialize_admin_variation(variation)


@router.get("/generation-tasks/{task_id}", response_model=GenerationTaskRead)
async def get_generation_task(
    task_id: str,
    _: User = Depends(require_admin_user),
):
    return AdminScenarioService.get_task(task_id)
