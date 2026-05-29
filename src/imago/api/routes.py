import base64
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from imago import __version__
from imago.api.dependencies import get_ingestion_service
from imago.api.models import ImageIngestRequest, ImageIngestResponse
from imago.storage.contracts import AtomicIngestionService, IngestionPayload
from imago.storage.ingestion import IngestionError
from imago.storage.policy import profile_for_format

router = APIRouter(prefix="/api/v1", tags=["imago"])


def ingestion_service_dependency() -> AtomicIngestionService:
    return get_ingestion_service()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}


@router.post(
    "/images/ingest",
    status_code=status.HTTP_201_CREATED,
    response_model=ImageIngestResponse,
)
def ingest_image(
    request: ImageIngestRequest,
    ingestion_service: Annotated[
        AtomicIngestionService,
        Depends(ingestion_service_dependency),
    ],
) -> ImageIngestResponse:
    profile = profile_for_format(request.format_name)
    if profile.extension and profile.extension not in request.object_key.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="object_key does not match declared format",
        )

    try:
        payload = base64.b64decode(request.payload_b64, validate=True)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payload_b64 must be valid base64",
        ) from exc

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payload_b64 decodes to an empty payload",
        )

    ingestion_payload = IngestionPayload(
        object_key=request.object_key,
        object_bytes=payload,
        content_type=request.content_type,
        uploaded_by=request.uploaded_by,
        uploaded_at=datetime.now(UTC),
        format_profile=profile,
        classification=profile.classification,
    )

    try:
        result = ingestion_service.ingest(ingestion_payload)
    except (IngestionError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ingestion failed",
        ) from exc

    return ImageIngestResponse(
        object_key=result.object_key,
        object_hash=result.object_hash,
        metadata_id=result.metadata_id,
        ledger_event_id=result.ledger_event_id,
        classification=profile.classification.value,
        format_family=profile.family.value,
    )
