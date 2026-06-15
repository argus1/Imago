from __future__ import annotations

import hashlib
import logging

from imago.storage.contracts import (
    AtomicIngestionService,
    CompensatingMetadataIndex,
    DeletableObjectStorage,
    IngestionPayload,
    IngestionResult,
    LedgerWriter,
    MetadataIndex,
    ObjectStorage,
    ReadableObjectStorage,
)

logger = logging.getLogger(__name__)


class IngestionError(RuntimeError):
    """Raised when the atomic ingestion flow fails."""


class AtomicIngestionCoordinator(AtomicIngestionService):
    def __init__(
        self,
        object_storage: ObjectStorage,
        metadata_index: MetadataIndex,
        ledger_writer: LedgerWriter,
    ) -> None:
        self._object_storage = object_storage
        self._metadata_index = metadata_index
        self._ledger_writer = ledger_writer

    def ingest(self, payload: IngestionPayload) -> IngestionResult:
        if payload.classification != payload.format_profile.classification:
            raise ValueError("payload classification does not match format profile")

        object_hash = hashlib.sha256(payload.object_bytes).hexdigest()
        metadata_id: str | None = None

        try:
            self._object_storage.put_object(
                key=payload.object_key,
                payload=payload.object_bytes,
                content_type=payload.content_type,
            )
            metadata_id = self._metadata_index.upsert_metadata(payload, object_hash)
            ledger_event_id = self._ledger_writer.write_ingestion_event(
                payload=payload,
                object_hash=object_hash,
                metadata_id=metadata_id,
            )
        except Exception as exc:
            self._compensate(payload.object_key, metadata_id)
            raise IngestionError("atomic ingestion failed") from exc

        return IngestionResult(
            object_key=payload.object_key,
            object_hash=object_hash,
            metadata_id=metadata_id,
            ledger_event_id=ledger_event_id,
        )

    def _compensate(self, object_key: str, metadata_id: str | None) -> None:
        if metadata_id is not None and isinstance(
            self._metadata_index,
            CompensatingMetadataIndex,
        ):
            try:
                self._metadata_index.delete_metadata(metadata_id)
            except Exception as exc:
                logger.warning(
                    "failed to roll back metadata during ingestion compensation",
                    exc_info=exc,
                )

        if isinstance(self._object_storage, DeletableObjectStorage):
            try:
                self._object_storage.delete_object(object_key)
            except Exception as exc:
                logger.warning(
                    "failed to delete object during ingestion compensation",
                    exc_info=exc,
                )

    def verify_object_hash(self, object_key: str) -> str:
        if not isinstance(self._object_storage, ReadableObjectStorage):
            raise NotImplementedError("object storage backend does not support verification reads")
        payload = self._object_storage.get_object(object_key)
        return hashlib.sha256(payload).hexdigest()
