from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from imago.domain.models import AccessAction
from imago.storage.policy import DataClassification, FormatFamily


class ImageIngestRequest(BaseModel):
    object_key: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    uploaded_by: str = Field(min_length=1)
    format_name: str = Field(min_length=1)
    payload_b64: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class ImageIngestResponse(BaseModel):
    object_key: str
    object_hash: str
    metadata_id: str
    ledger_event_id: str
    classification: str
    format_family: str


class AccessGrantCreateRequest(BaseModel):
    grant_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    principal_id: str = Field(min_length=1)
    action: AccessAction
    expires_at: datetime | None = None
    idempotency_key: str | None = None

    model_config = ConfigDict(extra="forbid")


class AccessGrantCreateResponse(BaseModel):
    grant_id: str


class AccessGrantRevokeRequest(BaseModel):
    idempotency_key: str | None = None

    model_config = ConfigDict(extra="forbid")


class AccessEvaluationRequest(BaseModel):
    image_id: str = Field(min_length=1)
    image_object_key: str = Field(min_length=1)
    image_content_hash: str = Field(min_length=1)
    image_owner_organization_id: str = Field(min_length=1)
    image_format_family: FormatFamily
    image_classification: DataClassification
    action: AccessAction

    model_config = ConfigDict(extra="forbid")


class AccessEvaluationResponse(BaseModel):
    principal_id: str
    image_id: str
    action: AccessAction
    classification: DataClassification
    allowed: bool
    reason: str
    occurred_at: datetime
