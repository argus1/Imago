from __future__ import annotations

import pytest

from imago.domain.events import LedgerEvent
from imago.ledger.chain import LedgerChain
from imago.ledger.service import IdempotentLedgerService


def _event(event_id: str = "evt-1") -> LedgerEvent:
    return LedgerEvent.new(
        event_id=event_id,
        event_type="image.registered",
        principal_id="user-1",
        image_id="img-1",
    )


@pytest.mark.unit
def test_idempotent_service_reuses_existing_submission() -> None:
    service = IdempotentLedgerService(LedgerChain())
    event = _event("evt-1")

    first = service.submit_events(idempotency_key="idem-1", events=[event])
    second = service.submit_events(idempotency_key="idem-1", events=[event])

    assert first.reused is False
    assert second.reused is True
    assert first.block.block_hash == second.block.block_hash
    assert len(service.chain.blocks) == 2


@pytest.mark.unit
def test_idempotent_service_rejects_empty_inputs() -> None:
    service = IdempotentLedgerService(LedgerChain())

    with pytest.raises(ValueError):
        service.submit_events(idempotency_key="", events=[_event()])

    with pytest.raises(ValueError):
        service.submit_events(idempotency_key="idem-1", events=[])


@pytest.mark.unit
def test_idempotent_service_rejects_same_key_with_different_payload() -> None:
    service = IdempotentLedgerService(LedgerChain())

    service.submit_events(idempotency_key="idem-1", events=[_event("evt-1")])

    with pytest.raises(ValueError, match="idempotency_key reused with different payload"):
        service.submit_events(idempotency_key="idem-1", events=[_event("evt-2")])