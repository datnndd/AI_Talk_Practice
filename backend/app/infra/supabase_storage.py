from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestError, UpstreamServiceError


@dataclass(frozen=True)
class SupabaseUploadResult:
    path: str
    public_url: str


class SupabaseStorageClient:
    def __init__(self) -> None:
        self.base_url = (settings.supabase_url or "").rstrip("/")
        self.service_role_key = settings.supabase_service_role_key

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise BadRequestError("Supabase storage is not configured")

    @property
    def is_configured(self) -> bool:
        return bool(
            self.base_url
            and self.service_role_key
            and self.service_role_key != "replace-with-your-service-role-key"
        )

    async def upload_public_object(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str,
        upsert: bool = False,
    ) -> SupabaseUploadResult:
        self._ensure_configured()
        if not bucket:
            raise BadRequestError("Supabase bucket is required")
        if not content:
            raise BadRequestError("Uploaded file was empty")

        encoded_bucket = quote(bucket.strip("/"), safe="")
        clean_path = "/".join(part for part in path.split("/") if part)
        encoded_path = "/".join(quote(part, safe="") for part in clean_path.split("/"))
        upload_url = f"{self.base_url}/storage/v1/object/{encoded_bucket}/{encoded_path}"
        headers = {
            "apikey": self.service_role_key,
            "authorization": f"Bearer {self.service_role_key}",
            "content-type": content_type,
            "x-upsert": "true" if upsert else "false",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(upload_url, content=content, headers=headers)

        if response.status_code >= 400:
            raise UpstreamServiceError(f"Supabase upload failed: {response.text}")

        public_url = f"{self.base_url}/storage/v1/object/public/{encoded_bucket}/{encoded_path}"
        return SupabaseUploadResult(path=clean_path, public_url=public_url)

    async def delete_object(self, *, bucket: str, path: str) -> None:
        self._ensure_configured()
        encoded_bucket = quote(bucket.strip("/"), safe="")
        clean_path = "/".join(part for part in path.split("/") if part)
        encoded_path = "/".join(quote(part, safe="") for part in clean_path.split("/"))
        delete_url = f"{self.base_url}/storage/v1/object/{encoded_bucket}/{encoded_path}"
        headers = {
            "apikey": self.service_role_key,
            "authorization": f"Bearer {self.service_role_key}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(delete_url, headers=headers)

        if response.status_code >= 400 and response.status_code != 404:
            raise UpstreamServiceError(f"Supabase delete failed: {response.text}")


supabase_storage = SupabaseStorageClient()
