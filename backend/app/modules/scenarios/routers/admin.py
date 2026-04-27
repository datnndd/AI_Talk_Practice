from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import (
    BulkScenarioActionRequest,
    BulkScenarioActionResponse,
    GenerateDefaultPromptRequest,
    GenerateDefaultPromptResponse,
    ScenarioAdminCreate,
    ScenarioAdminRead,
    ScenarioAdminUpdate,
    ScenarioListResponse,
)
from app.modules.scenarios.serializers import serialize_admin_scenario
from app.modules.scenarios.services.admin_scenario_service import AdminScenarioService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scenarios/generate-default-prompt", response_model=GenerateDefaultPromptResponse)
async def generate_default_prompt(
    body: GenerateDefaultPromptRequest,
    _: User = Depends(require_admin_user),
):
    prompt = AdminScenarioService.generate_default_prompt(
        title=body.title,
        description=body.description,
        ai_role=body.ai_role,
        user_role=body.user_role,
        tasks=body.tasks,
    )
    quality = AdminScenarioService.assess_prompt_quality(
        prompt=prompt,
        description=body.description,
        tasks=body.tasks,
    )
    return GenerateDefaultPromptResponse(prompt=prompt, quality=quality)


# NOTE: This MUST be declared before /scenarios/{scenario_id} routes so FastAPI
# doesn't try to parse the literal string "bulk-actions" as an integer ID.
@router.post("/scenarios/bulk-actions", response_model=BulkScenarioActionResponse)
async def bulk_admin_scenario_action(
    body: BulkScenarioActionRequest,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
):
    task = await AdminScenarioService.bulk_action(db=db, user_id=user.id, body=body)
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
    )
