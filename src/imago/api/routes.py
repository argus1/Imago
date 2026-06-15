import base64
import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from imago import __version__
from imago.api.dependencies import (
    RequestAuthContext,
    get_ingestion_service,
    get_policy_engine,
    get_request_auth_context,
)
from imago.api.models import (
    AccessEvaluationRequest,
    AccessEvaluationResponse,
    AccessGrantCreateRequest,
    AccessGrantCreateResponse,
    AccessGrantRevokeRequest,
    AuditDecisionListResponse,
    AuditDecisionRecord,
    ImageIngestRequest,
    ImageIngestResponse,
    ImageVerifyRequest,
    ImageVerifyResponse,
)
from imago.domain.models import AccessGrant, AuditOutcome, ImageAsset, Principal
from imago.security.policy_engine import AuthorizationPolicyEngine
from imago.storage.contracts import (
    AtomicIngestionService,
    HashVerifiableIngestionService,
    IngestionPayload,
)
from imago.storage.ingestion import IngestionError
from imago.storage.policy import profile_for_format

router = APIRouter(prefix="/api/v1", tags=["imago"])


def ingestion_service_dependency() -> AtomicIngestionService:
    return get_ingestion_service()


def policy_engine_dependency() -> AuthorizationPolicyEngine:
    return get_policy_engine()


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


@router.post(
    "/images/verify",
    response_model=ImageVerifyResponse,
)
def verify_image(
    request: ImageVerifyRequest,
    ingestion_service: Annotated[
        AtomicIngestionService,
        Depends(ingestion_service_dependency),
    ],
) -> ImageVerifyResponse:
    if not isinstance(ingestion_service, HashVerifiableIngestionService):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="ingestion backend does not support object verification",
        )

    try:
        computed_hash = ingestion_service.verify_object_hash(request.object_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="object not found",
        ) from exc

    expected_hash = request.expected_hash.lower()
    verified = hmac.compare_digest(computed_hash, expected_hash)

    return ImageVerifyResponse(
        object_key=request.object_key,
        expected_hash=expected_hash,
        computed_hash=computed_hash,
        verified=verified,
        verified_at=datetime.now(UTC),
    )


@router.post(
    "/policy/grants",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessGrantCreateResponse,
    summary="Create policy access grant",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Access grant created",
            "content": {
                "application/json": {
                    "example": {
                        "grant_id": "grant-ct-001",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Caller is not an admin",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "access denied: grant_management_requires_admin",
                    },
                },
            },
        },
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "createGrant": {
                            "summary": "Create a read grant for a radiology image",
                            "value": {
                                "grant_id": "grant-ct-001",
                                "image_id": "img-ct-20260614-0001",
                                "principal_id": "clinician-42",
                                "action": "read",
                                "expires_at": "2026-07-15T00:00:00Z",
                                "idempotency_key": "idem-grant-ct-001",
                            },
                        },
                    },
                },
            },
        },
    },
)
def create_access_grant(
    request: AccessGrantCreateRequest,
    policy_engine: Annotated[
        AuthorizationPolicyEngine,
        Depends(policy_engine_dependency),
    ],
    auth_context: Annotated[
        RequestAuthContext,
        Depends(get_request_auth_context),
    ],
) -> AccessGrantCreateResponse:
    if auth_context.role not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="access denied: grant_management_requires_admin",
        )

    grant = AccessGrant(
        grant_id=request.grant_id,
        image_id=request.image_id,
        principal_id=request.principal_id,
        action=request.action,
        granted_by=auth_context.principal_id,
        granted_at=datetime.now(UTC),
        expires_at=request.expires_at,
    )
    grant_id = policy_engine.record_grant(grant, idempotency_key=request.idempotency_key)
    return AccessGrantCreateResponse(grant_id=grant_id)


@router.post(
    "/policy/grants/{grant_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke policy access grant",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Access grant revoked",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Caller is not an admin",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "access denied: grant_management_requires_admin",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Grant not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "grant not found",
                    },
                },
            },
        },
    },
    openapi_extra={
        "parameters": [
            {
                "name": "grant_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "example": "grant-ct-001",
                "description": "Identifier of the grant to revoke",
            },
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "revokeGrant": {
                            "summary": "Revoke an existing grant",
                            "value": {
                                "idempotency_key": "idem-revoke-grant-ct-001",
                            },
                        },
                    },
                },
            },
        },
    },
)
def revoke_access_grant(
    grant_id: str,
    request: AccessGrantRevokeRequest,
    policy_engine: Annotated[
        AuthorizationPolicyEngine,
        Depends(policy_engine_dependency),
    ],
    auth_context: Annotated[
        RequestAuthContext,
        Depends(get_request_auth_context),
    ],
) -> None:
    if auth_context.role not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="access denied: grant_management_requires_admin",
        )

    try:
        policy_engine.revoke_grant(grant_id, idempotency_key=request.idempotency_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="grant not found",
        ) from exc


@router.post(
    "/policy/evaluate",
    response_model=AccessEvaluationResponse,
)
def evaluate_access(
    request: AccessEvaluationRequest,
    policy_engine: Annotated[
        AuthorizationPolicyEngine,
        Depends(policy_engine_dependency),
    ],
    auth_context: Annotated[
        RequestAuthContext,
        Depends(get_request_auth_context),
    ],
) -> AccessEvaluationResponse:
    principal = Principal(
        principal_id=auth_context.principal_id,
        organization_id=auth_context.organization_id,
        principal_type=auth_context.principal_type,
        role=auth_context.role,
    )
    asset = ImageAsset(
        image_id=request.image_id,
        object_key=request.image_object_key,
        content_hash=request.image_content_hash,
        format_family=request.image_format_family,
        classification=request.image_classification,
        owner_organization_id=request.image_owner_organization_id,
    )
    decision = policy_engine.evaluate(
        principal=principal,
        asset=asset,
        action=request.action,
    )

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"access denied: {decision.reason}",
        )

    return AccessEvaluationResponse(
        principal_id=decision.principal_id,
        image_id=decision.image_id,
        action=decision.action,
        classification=decision.classification,
        allowed=decision.allowed,
        reason=decision.reason,
        occurred_at=decision.occurred_at,
    )


@router.get(
    "/audit/policy-decisions",
    response_model=AuditDecisionListResponse,
)
def list_policy_decisions(
    policy_engine: Annotated[
        AuthorizationPolicyEngine,
        Depends(policy_engine_dependency),
    ],
    auth_context: Annotated[
        RequestAuthContext,
        Depends(get_request_auth_context),
    ],
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    principal_id: str | None = None,
    image_id: str | None = None,
) -> AuditDecisionListResponse:
    if auth_context.role not in {"admin", "super_admin", "auditor"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="access denied: audit_read_requires_admin_or_auditor",
        )

    records: list[AuditDecisionRecord] = []
    for decision in reversed(policy_engine.decisions):
        if principal_id is not None and decision.principal_id != principal_id:
            continue
        if image_id is not None and decision.image_id != image_id:
            continue

        records.append(
            AuditDecisionRecord(
                principal_id=decision.principal_id,
                image_id=decision.image_id,
                action=decision.action,
                classification=decision.classification,
                outcome=AuditOutcome.ALLOW if decision.allowed else AuditOutcome.DENY,
                reason=decision.reason,
                occurred_at=decision.occurred_at,
            ),
        )
        if len(records) >= limit:
            break

    return AuditDecisionListResponse(total=len(records), items=records)
