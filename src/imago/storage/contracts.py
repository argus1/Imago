from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from imago.storage.policy import DataClassification, FormatProfile


@dataclass(frozen=True)
class IngestionPayload:
    object_key: str
    object_bytes: bytes
    content_type: str
    uploaded_by: str
    uploaded_at: datetime
    format_profile: FormatProfile
    classification: DataClassification


@dataclass(frozen=True)
class IngestionResult:
    object_key: str
    object_hash: str
    metadata_id: str
    ledger_event_id: str


class ObjectStorage(Protocol):
    def put_object(self, key: str, payload: bytes, content_type: str) -> str:
        """Store raw binary payload and return provider checksum or ETag."""


class MetadataIndex(Protocol):
    def upsert_metadata(self, payload: IngestionPayload, object_hash: str) -> str:
        """Persist extracted metadata and return metadata record id."""


class LedgerWriter(Protocol):
    def write_ingestion_event(
        self,
        payload: IngestionPayload,
        object_hash: str,
        metadata_id: str,
    ) -> str:
        """Write an immutable ledger event and return event id."""


class AtomicIngestionService(Protocol):
    def ingest(self, payload: IngestionPayload) -> IngestionResult:
        """Perform object store, metadata index, and ledger write as one operation."""


@runtime_checkable
class HashVerifiableIngestionService(Protocol):
    def verify_object_hash(self, object_key: str) -> str:
        """Return SHA-256 hash for a stored object key."""


@runtime_checkable
class DeletableObjectStorage(Protocol):
    def delete_object(self, key: str) -> None:
        """Delete object for compensation when downstream steps fail."""


@runtime_checkable
class CompensatingMetadataIndex(Protocol):
    def delete_metadata(self, metadata_id: str) -> None:
        """Delete metadata record for compensation when ledger write fails."""


@runtime_checkable
class ReadableObjectStorage(Protocol):
    def get_object(self, key: str) -> bytes:
        """Fetch stored object bytes for integrity verification."""
