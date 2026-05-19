import re
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel

from app.api.dependencies import require_admin_user
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infra.supabase_storage import supabase_storage
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/site", tags=["admin"])

LOGO_UPLOAD_MAX_BYTES = 5 * 1024 * 1024

class SiteAssetUploadRead(BaseModel):
    url: str
    path: str

@router.post("/logo", response_model=SiteAssetUploadRead, status_code=status.HTTP_200_OK)
async def upload_site_logo(
    file: UploadFile = File(...),
    _: User = Depends(require_admin_user),
):
    normalized_content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if not normalized_content_type.startswith("image/"):
        raise BadRequestError("Uploaded logo must be an image file")

    content = await file.read()
    if len(content) > LOGO_UPLOAD_MAX_BYTES:
        raise BadRequestError("Logo image must be 5MB or smaller")

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else normalized_content_type.split("/", 1)[1]
    safe_extension = re.sub(r"[^a-zA-Z0-9]", "", extension or "jpg")[:12] or "jpg"
    path = f"site/logos/{uuid.uuid4().hex}.{safe_extension}"
    result = await supabase_storage.upload_public_object(
        bucket=settings.supabase_images_bucket,
        path=path,
        content=content,
        content_type=normalized_content_type,
    )
    return SiteAssetUploadRead(url=result.public_url, path=result.path)
