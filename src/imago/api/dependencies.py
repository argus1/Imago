from __future__ import annotations

import itertools
from datetime import UTC, datetime

from imago.storage.contracts import (
    AtomicIngestionService,
    IngestionPayload,
    LedgerWriter,
    MetadataIndex,
    ObjectStorage,
)
from imago.storage.ingestion import AtomicIngestionCoordinator


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

    def write_ingestion_event(
        self,
        payload: IngestionPayload,
        object_hash: str,
        metadata_id: str,
    ) -> str:
        event_id = f"evt-{next(self._counter)}"
        self._events[event_id] = {
            "event_type": "image.ingested",
            "object_key": payload.object_key,
            "metadata_id": metadata_id,
            "object_hash": object_hash,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        return event_id


_object_storage = InMemoryObjectStorage()
_metadata_index = InMemoryMetadataIndex()
_ledger_writer = InMemoryLedgerWriter()
_ingestion_service = AtomicIngestionCoordinator(
    object_storage=_object_storage,
    metadata_index=_metadata_index,
    ledger_writer=_ledger_writer,
)


def get_ingestion_service() -> AtomicIngestionService:
    return _ingestion_service
