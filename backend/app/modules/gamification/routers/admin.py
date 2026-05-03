from __future__ import annotations

from datetime import date
import logging
import os
import re
import uuid
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infra.supabase_storage import supabase_storage
from app.modules.gamification.models.shop_product import ShopProduct
from app.modules.gamification.schemas.admin_gamification import (
    AdminGamificationOverviewRead,
    AdminShopProductRead,
    AdminShopProductWrite,
    AdminShopRedemptionRead,
    AdminShopRedemptionStatusUpdate,
    GamificationSettingsRead,
    GamificationSettingsUpdateRequest,
)
from app.modules.gamification.services.admin_gamification_service import AdminGamificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/gamification", tags=["admin"])
logger = logging.getLogger(__name__)


async def _upload_shop_product_image(file: UploadFile) -> dict[str, str]:
    normalized_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if not normalized_content_type.startswith("image/"):
        raise BadRequestError("Uploaded shop product image must be an image file")

    content = await file.read()
    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else normalized_content_type.split("/", 1)[1]
    safe_extension = re.sub(r"[^a-zA-Z0-9]", "", extension or "jpg")[:12] or "jpg"
    path = f"shop-products/{uuid.uuid4().hex}.{safe_extension}"
    if not supabase_storage.is_configured:
        upload_dir = "static/uploads/shop-products"
        os.makedirs(upload_dir, exist_ok=True)
        filename = path.rsplit("/", 1)[-1]
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as local_file:
            local_file.write(content)
        return {"url": f"/static/uploads/shop-products/{filename}", "path": f"shop-products/{filename}"}

    result = await supabase_storage.upload_public_object(
        bucket=settings.supabase_images_bucket,
        path=path,
        content=content,
        content_type=normalized_content_type,
    )
    return {"url": result.public_url, "path": result.path}


def _shop_product_body_from_form(
    *,
    code: str,
    name: str,
    description: str,
    price_coin: int,
    image_url: str | None,
    stock_quantity: int,
    is_active: bool,
    sort_order: int,
) -> AdminShopProductWrite:
    return AdminShopProductWrite(
        code=code,
        name=name,
        description=description,
        price_coin=price_coin,
        image_url=image_url or None,
        stock_quantity=stock_quantity,
        is_active=is_active,
        sort_order=sort_order,
    )


def _shop_product_storage_path_from_url(url: str | None) -> str | None:
    if not url or not settings.supabase_url:
        return None
    parsed = urlparse(url)
    storage_prefix = f"/storage/v1/object/public/{settings.supabase_images_bucket}/"
    if parsed.netloc != urlparse(settings.supabase_url).netloc or not parsed.path.startswith(storage_prefix):
        return None
    path = unquote(parsed.path[len(storage_prefix):])
    return path if path.startswith("shop-products/") else None


async def _delete_shop_product_image_by_url(url: str | None) -> None:
    path = _shop_product_storage_path_from_url(url)
    if not path or not supabase_storage.is_configured:
        return
    try:
        await supabase_storage.delete_object(bucket=settings.supabase_images_bucket, path=path)
    except Exception:
        logger.warning("Failed to delete old shop product image", exc_info=True)


@router.get("/shop/products", response_model=list[AdminShopProductRead])
async def list_admin_shop_products(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.list_shop_products(db)


@router.post("/shop/products", response_model=AdminShopProductRead, status_code=201)
async def create_admin_shop_product(
    body: AdminShopProductWrite,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.create_shop_product(db, body)


@router.post("/shop/products/with-image", response_model=AdminShopProductRead, status_code=201)
async def create_admin_shop_product_with_image(
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(default=""),
    price_coin: int = Form(...),
    image_url: str | None = Form(default=None),
    stock_quantity: int = Form(...),
    is_active: bool = Form(default=True),
    sort_order: int = Form(default=0),
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    body = _shop_product_body_from_form(
        code=code,
        name=name,
        description=description,
        price_coin=price_coin,
        image_url=image_url,
        stock_quantity=stock_quantity,
        is_active=is_active,
        sort_order=sort_order,
    )
    if image is not None:
        uploaded = await _upload_shop_product_image(image)
        body.image_url = uploaded["url"]
    try:
        return await AdminGamificationService.create_shop_product(db, body)
    except Exception:
        if image is not None:
            await _delete_shop_product_image_by_url(body.image_url)
        raise


@router.put("/shop/products/{product_id}", response_model=AdminShopProductRead)
async def update_admin_shop_product(
    product_id: int,
    body: AdminShopProductWrite,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_shop_product(db, product_id, body)


@router.put("/shop/products/{product_id}/with-image", response_model=AdminShopProductRead)
async def update_admin_shop_product_with_image(
    product_id: int,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(default=""),
    price_coin: int = Form(...),
    image_url: str | None = Form(default=None),
    stock_quantity: int = Form(...),
    is_active: bool = Form(default=True),
    sort_order: int = Form(default=0),
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    body = _shop_product_body_from_form(
        code=code,
        name=name,
        description=description,
        price_coin=price_coin,
        image_url=image_url,
        stock_quantity=stock_quantity,
        is_active=is_active,
        sort_order=sort_order,
    )
    if image is not None:
        old_product = await db.get(ShopProduct, product_id)
        old_image_url = old_product.image_url if old_product is not None else None
        uploaded = await _upload_shop_product_image(image)
        body.image_url = uploaded["url"]
    else:
        old_image_url = None
    try:
        result = await AdminGamificationService.update_shop_product(db, product_id, body)
    except Exception:
        if image is not None:
            await _delete_shop_product_image_by_url(body.image_url)
        raise
    if image is not None:
        await _delete_shop_product_image_by_url(old_image_url)
    return result


@router.delete("/shop/products/{product_id}", response_model=AdminShopProductRead)
async def hide_admin_shop_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.hide_shop_product(db, product_id)


@router.get("/shop/redemptions", response_model=list[AdminShopRedemptionRead])
async def list_admin_shop_redemptions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.list_shop_redemptions(db)


@router.put("/shop/redemptions/{redemption_id}/status", response_model=AdminShopRedemptionRead)
async def update_admin_shop_redemption_status(
    redemption_id: int,
    body: AdminShopRedemptionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_shop_redemption_status(db, redemption_id, body)


@router.get("/settings", response_model=GamificationSettingsRead)
async def get_admin_gamification_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_settings(db)


@router.put("/settings", response_model=GamificationSettingsRead)
async def update_admin_gamification_settings(
    body: GamificationSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_settings(db, actor=actor, body=body)


@router.get("/overview", response_model=AdminGamificationOverviewRead)
async def get_admin_gamification_overview(
    date_: date | None = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_overview(db, target_date=date_ or date.today())
