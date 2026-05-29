from __future__ import annotations

from datetime import UTC, datetime

import pytest

from imago.storage.contracts import IngestionPayload
from imago.storage.ingestion import AtomicIngestionCoordinator, IngestionError
from imago.storage.policy import DataClassification, profile_for_format


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def put_object(self, key: str, payload: bytes, content_type: str) -> str:
        self.objects[key] = payload
        return "etag"

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)


class FakeMetadataIndex:
    def __init__(self) -> None:
        self.items: dict[str, str] = {}
        self.deleted: list[str] = []
        self.fail_upsert = False

    def upsert_metadata(self, payload: IngestionPayload, object_hash: str) -> str:
        if self.fail_upsert:
            raise RuntimeError("metadata write failed")
        metadata_id = "meta-1"
        self.items[metadata_id] = object_hash
        return metadata_id

    def delete_metadata(self, metadata_id: str) -> None:
        self.deleted.append(metadata_id)
        self.items.pop(metadata_id, None)


class FakeLedgerWriter:
    def __init__(self) -> None:
        self.fail_write = False

    def write_ingestion_event(
        self,
        payload: IngestionPayload,
        object_hash: str,
        metadata_id: str,
    ) -> str:
        if self.fail_write:
            raise RuntimeError("ledger write failed")
        return "evt-1"


def _payload() -> IngestionPayload:
    profile = profile_for_format("scan.dcm")
    return IngestionPayload(
        object_key="images/scan.dcm",
        object_bytes=b"raw-image-bytes",
        content_type="application/dicom",
        uploaded_by="user-1",
        uploaded_at=datetime.now(UTC),
        format_profile=profile,
        classification=DataClassification.RESTRICTED_CLINICAL,
    )


@pytest.mark.unit
def test_ingestion_success() -> None:
    object_storage = FakeObjectStorage()
    metadata_index = FakeMetadataIndex()
    ledger_writer = FakeLedgerWriter()

    service = AtomicIngestionCoordinator(object_storage, metadata_index, ledger_writer)
    result = service.ingest(_payload())

    assert result.object_key == "images/scan.dcm"
    assert result.metadata_id == "meta-1"
    assert result.ledger_event_id == "evt-1"
    assert result.object_hash


@pytest.mark.unit
def test_ingestion_rolls_back_object_when_metadata_fails() -> None:
    object_storage = FakeObjectStorage()
    metadata_index = FakeMetadataIndex()
    metadata_index.fail_upsert = True
    ledger_writer = FakeLedgerWriter()

    service = AtomicIngestionCoordinator(object_storage, metadata_index, ledger_writer)

    with pytest.raises(IngestionError):
        service.ingest(_payload())

    assert object_storage.deleted == ["images/scan.dcm"]
    assert metadata_index.deleted == []


@pytest.mark.unit
def test_ingestion_rolls_back_object_and_metadata_when_ledger_fails() -> None:
    object_storage = FakeObjectStorage()
    metadata_index = FakeMetadataIndex()
    ledger_writer = FakeLedgerWriter()
    ledger_writer.fail_write = True

    service = AtomicIngestionCoordinator(object_storage, metadata_index, ledger_writer)

    with pytest.raises(IngestionError):
        service.ingest(_payload())

    assert metadata_index.deleted == ["meta-1"]
    assert object_storage.deleted == ["images/scan.dcm"]
