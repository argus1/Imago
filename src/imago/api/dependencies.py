from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from fastapi import Header, HTTPException, status

from imago.config.settings import get_settings
from imago.domain.events import LedgerEvent
from imago.domain.models import PrincipalType
from imago.ledger.chain import LedgerChain
from imago.ledger.service import IdempotentLedgerService
from imago.security.policy_engine import AuthorizationPolicyEngine
from imago.storage.contracts import (
    AtomicIngestionService,
    IngestionPayload,
    LedgerWriter,
    MetadataIndex,
    ObjectStorage,
)
from imago.storage.filesystem import FilesystemObjectStorage
from imago.storage.ingestion import AtomicIngestionCoordinator


@dataclass(frozen=True)
class RequestAuthContext:
    principal_id: str
    organization_id: str
    principal_type: PrincipalType
    role: str


def get_request_auth_context(
    x_imago_principal_id: str | None = Header(default=None, alias="X-Imago-Principal-Id"),
    x_imago_org_id: str | None = Header(default=None, alias="X-Imago-Org-Id"),
    x_imago_principal_type: str | None = Header(default=None, alias="X-Imago-Principal-Type"),
    x_imago_role: str | None = Header(default=None, alias="X-Imago-Role"),
) -> RequestAuthContext:
    if not x_imago_principal_id or not x_imago_org_id or not x_imago_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "missing required auth headers: X-Imago-Principal-Id, "
                "X-Imago-Org-Id, X-Imago-Role"
            ),
        )

    principal_type_raw = x_imago_principal_type or PrincipalType.USER.value
    try:
        principal_type = PrincipalType(principal_type_raw.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid X-Imago-Principal-Type header",
        ) from exc

    return RequestAuthContext(
        principal_id=x_imago_principal_id,
        organization_id=x_imago_org_id,
        principal_type=principal_type,
        role=x_imago_role.lower(),
    )


class InMemoryObjectStorage(ObjectStorage):
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put_object(self, key: str, payload: bytes, content_type: str) -> str:
        del content_type
        self._objects[key] = payload
        return "mem-etag"

    def delete_object(self, key: str) -> None:
        self._objects.pop(key, None)


class InMemoryMetadataIndex(MetadataIndex):
    def __init__(self) -> None:
        self._counter = itertools.count(1)
        self._records: dict[str, dict[str, str]] = {}

    def upsert_metadata(self, payload: IngestionPayload, object_hash: str) -> str:
        metadata_id = f"meta-{next(self._counter)}"
        self._records[metadata_id] = {
            "object_key": payload.object_key,
            "uploaded_by": payload.uploaded_by,
            "uploaded_at": payload.uploaded_at.isoformat(),
            "object_hash": object_hash,
            "classification": payload.classification.value,
            "format_family": payload.format_profile.family.value,
        }
        return metadata_id

    def delete_metadata(self, metadata_id: str) -> None:
        self._records.pop(metadata_id, None)


class InMemoryLedgerWriter(LedgerWriter):
    def __init__(self) -> None:
        self._counter = itertools.count(1)
        self._events: dict[str, dict[str, str]] = {}
        self._idempotency_to_event_id: dict[str, str] = {}
        self._submission_service = IdempotentLedgerService(LedgerChain())

    def write_ingestion_event(
        self,
        payload: IngestionPayload,
        object_hash: str,
        metadata_id: str,
    ) -> str:
        idempotency_key = hashlib.sha256(
            f"{payload.object_key}:{object_hash}:{metadata_id}".encode("utf-8"),
        ).hexdigest()

        existing_event_id = self._idempotency_to_event_id.get(idempotency_key)
        if existing_event_id is not None:
            return existing_event_id

        event_id = f"evt-{next(self._counter)}"
        ledger_event = LedgerEvent.new(
            event_id=event_id,
            event_type="image.ingested",
            principal_id=payload.uploaded_by,
            image_id=payload.object_key,
        )
        submission = self._submission_service.submit_events(
            idempotency_key=idempotency_key,
            events=[ledger_event],
        )

        self._events[event_id] = {
            "event_type": "image.ingested",
            "object_key": payload.object_key,
            "metadata_id": metadata_id,
            "object_hash": object_hash,
            "recorded_at": datetime.now(UTC).isoformat(),
            "block_hash": submission.block.block_hash,
            "block_index": str(submission.block.index),
        }
        self._idempotency_to_event_id[idempotency_key] = event_id
        return event_id

    def verify_chain(self) -> bool:
        return self._submission_service.verify_chain()


def _build_object_storage() -> ObjectStorage:
    settings = get_settings()
    backend = settings.storage_backend.lower()

    if backend == "filesystem":
        return FilesystemObjectStorage(settings.storage_root)
    if backend == "memory":
        return InMemoryObjectStorage()

    raise ValueError(f"unsupported storage backend: {settings.storage_backend}")


@lru_cache(maxsize=1)
def get_ingestion_service() -> AtomicIngestionService:
    return AtomicIngestionCoordinator(
        object_storage=_build_object_storage(),
        metadata_index=InMemoryMetadataIndex(),
        ledger_writer=InMemoryLedgerWriter(),
    )


@lru_cache(maxsize=1)
def get_policy_engine() -> AuthorizationPolicyEngine:
    return AuthorizationPolicyEngine()
