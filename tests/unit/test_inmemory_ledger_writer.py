from __future__ import annotations

from datetime import UTC, datetime

import pytest

from imago.api.dependencies import InMemoryLedgerWriter
from imago.storage.contracts import IngestionPayload
from imago.storage.policy import DataClassification, profile_for_format


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
def test_inmemory_ledger_writer_is_idempotent_for_same_payload() -> None:
    writer = InMemoryLedgerWriter()
    payload = _payload()

    first_id = writer.write_ingestion_event(payload, object_hash="hash-1", metadata_id="meta-1")
    second_id = writer.write_ingestion_event(payload, object_hash="hash-1", metadata_id="meta-1")

    assert first_id == second_id
    assert writer.verify_chain() is True