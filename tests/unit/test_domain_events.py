from __future__ import annotations

from datetime import datetime

import pytest

from imago.domain.events import LedgerEvent


@pytest.mark.unit
def test_ledger_event_new_normalizes_whitespace() -> None:
    event = LedgerEvent.new(
        event_id="  evt-1  ",
        event_type="  image.registered  ",
        principal_id="  user-1  ",
        image_id="  img-1  ",
    )

    assert event.event_id == "evt-1"
    assert event.event_type == "image.registered"
    assert event.principal_id == "user-1"
    assert event.image_id == "img-1"


@pytest.mark.unit
def test_ledger_event_new_sets_timezone_aware_iso_timestamp() -> None:
    event = LedgerEvent.new(
        event_id="evt-1",
        event_type="image.registered",
        principal_id="user-1",
        image_id="img-1",
    )

    parsed = datetime.fromisoformat(event.occurred_at)
    assert parsed.tzinfo is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("event_id", "", "event_id must not be empty"),
        ("event_type", "", "event_type must not be empty"),
        ("principal_id", "", "principal_id must not be empty"),
        ("image_id", "", "image_id must not be empty"),
        ("occurred_at", "", "occurred_at must not be empty"),
    ],
)
def test_ledger_event_rejects_empty_fields(field: str, value: str, error: str) -> None:
    payload = {
        "event_id": "evt-1",
        "event_type": "image.registered",
        "principal_id": "user-1",
        "image_id": "img-1",
        "occurred_at": "2026-01-01T00:00:00+00:00",
    }
    payload[field] = value

    with pytest.raises(ValueError, match=error):
        LedgerEvent(**payload)


@pytest.mark.unit
def test_ledger_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="occurred_at must be timezone-aware ISO-8601"):
        LedgerEvent(
            event_id="evt-1",
            event_type="image.registered",
            principal_id="user-1",
            image_id="img-1",
            occurred_at="2026-01-01T00:00:00",
        )
