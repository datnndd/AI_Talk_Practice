from __future__ import annotations

import json
import logging
import os
import re
import uuid
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
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
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infra.supabase_storage import supabase_storage

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def _scenario_body_from_form(
    *,
    title: str,
    description: str,
    category: str,
    difficulty: str,
    ai_role: str,
    user_role: str,
    tasks: str | None,
    ai_system_prompt: str,
    tags: str | None,
    estimated_duration_minutes: int,
    character_id: int | None,
    is_active: bool,
    is_pro: bool,
    image_url: str | None,
    update: bool = False,
) -> ScenarioAdminCreate | ScenarioAdminUpdate:
    schema = ScenarioAdminUpdate if update else ScenarioAdminCreate
    return schema(
        title=title,
        description=description,
        category=category,
        difficulty=difficulty,
        ai_role=ai_role,
        user_role=user_role,
        tasks=_parse_json_list(tasks),
        ai_system_prompt=ai_system_prompt,
        tags=_parse_json_list(tags),
        estimated_duration_minutes=estimated_duration_minutes,
        character_id=character_id,
        is_active=is_active,
        is_pro=is_pro,
        image_url=image_url or None,
    )


def _scenario_storage_path_from_url(url: str | None) -> str | None:
    if not url or not settings.supabase_url:
        return None
    parsed = urlparse(url)
    storage_prefix = f"/storage/v1/object/public/{settings.supabase_images_bucket}/"
    if parsed.netloc != urlparse(settings.supabase_url).netloc or not parsed.path.startswith(storage_prefix):
        return None
    path = unquote(parsed.path[len(storage_prefix):])
    return path if path.startswith("scenario-images/") else None


async def _delete_scenario_image_by_url(url: str | None) -> None:
    path = _scenario_storage_path_from_url(url)
    if not path or not supabase_storage.is_configured:
        return
    try:
        await supabase_storage.delete_object(bucket=settings.supabase_images_bucket, path=path)
    except Exception:
        logger.warning("Failed to delete scenario image", exc_info=True)


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
    return GenerateDefaultPromptResponse(prompt=prompt)


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


@router.post("/scenarios/with-image", response_model=ScenarioAdminRead, status_code=status.HTTP_201_CREATED)
async def create_admin_scenario_with_image(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    ai_role: str = Form(default=""),
    user_role: str = Form(default=""),
    tasks: str | None = Form(default=None),
    ai_system_prompt: str = Form(...),
    tags: str | None = Form(default=None),
    estimated_duration_minutes: int = Form(default=10),
    character_id: int | None = Form(default=None),
    is_active: bool = Form(default=True),
    is_pro: bool = Form(default=False),
    image_url: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_user),
):
    body = _scenario_body_from_form(
        title=title,
        description=description,
        category=category,
        difficulty=difficulty,
        ai_role=ai_role,
        user_role=user_role,
        tasks=tasks,
        ai_system_prompt=ai_system_prompt,
        tags=tags,
        estimated_duration_minutes=estimated_duration_minutes,
        character_id=character_id,
        is_active=is_active,
        is_pro=is_pro,
        image_url=image_url,
    )
    if image is not None:
        uploaded = await upload_scenario_image(image, user)
        body.image_url = uploaded["url"]
    try:
        scenario = await AdminScenarioService.create_scenario(db, user_id=user.id, body=body)
    except Exception:
        if image is not None:
            await _delete_scenario_image_by_url(body.image_url)
        raise
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(scenario, usage_count=usage_count)


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


@router.put("/scenarios/{scenario_id}/with-image", response_model=ScenarioAdminRead)
async def update_admin_scenario_with_image(
    scenario_id: int,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    ai_role: str = Form(default=""),
    user_role: str = Form(default=""),
    tasks: str | None = Form(default=None),
    ai_system_prompt: str = Form(...),
    tags: str | None = Form(default=None),
    estimated_duration_minutes: int = Form(default=10),
    character_id: int | None = Form(default=None),
    is_active: bool = Form(default=True),
    is_pro: bool = Form(default=False),
    image_url: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_user),
):
    body = _scenario_body_from_form(
        title=title,
        description=description,
        category=category,
        difficulty=difficulty,
        ai_role=ai_role,
        user_role=user_role,
        tasks=tasks,
        ai_system_prompt=ai_system_prompt,
        tags=tags,
        estimated_duration_minutes=estimated_duration_minutes,
        character_id=character_id,
        is_active=is_active,
        is_pro=is_pro,
        image_url=image_url,
        update=True,
    )
    old_scenario = await AdminScenarioService.get_scenario(db, scenario_id)
    old_image_url = old_scenario.image_url
    if image is not None:
        uploaded = await upload_scenario_image(image, user)
        body.image_url = uploaded["url"]
    try:
        scenario = await AdminScenarioService.update_scenario(db, scenario_id=scenario_id, user_id=user.id, body=body)
    except Exception:
        if image is not None:
            await _delete_scenario_image_by_url(body.image_url)
        raise
    if image is not None:
        await _delete_scenario_image_by_url(old_image_url)
    usage_count = await AdminScenarioService.get_scenario_usage_count(db, scenario.id)
    return serialize_admin_scenario(scenario, usage_count=usage_count)


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

async def upload_scenario_image(
    file: UploadFile,
    _: User,
):
    normalized_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if not normalized_content_type.startswith("image/"):
        raise BadRequestError("Uploaded scenario image must be an image file")

    content = await file.read()
    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else normalized_content_type.split("/", 1)[1]
    safe_extension = re.sub(r"[^a-zA-Z0-9]", "", extension or "jpg")[:12] or "jpg"
    path = f"scenario-images/{uuid.uuid4().hex}.{safe_extension}"
    if not supabase_storage.is_configured:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = path.rsplit("/", 1)[-1]
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as local_file:
            local_file.write(content)
        return {"url": f"/static/uploads/{filename}", "path": filename}

    result = await supabase_storage.upload_public_object(
        bucket=settings.supabase_images_bucket,
        path=path,
        content=content,
        content_type=normalized_content_type,
    )
    return {"url": result.public_url, "path": result.path}
