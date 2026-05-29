from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
