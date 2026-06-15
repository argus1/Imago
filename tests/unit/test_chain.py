from dataclasses import replace

import pytest

from imago.domain.events import LedgerEvent
from imago.ledger.chain import LedgerChain


def test_canonical_hash_is_deterministic_for_key_order() -> None:
    chain = LedgerChain()

    payload_a = {"b": 2, "a": 1, "nested": {"z": 26, "m": 13}}
    payload_b = {"nested": {"m": 13, "z": 26}, "a": 1, "b": 2}

    assert chain.canonical_hash(payload_a) == chain.canonical_hash(payload_b)


def test_chain_append_and_verify() -> None:
    chain = LedgerChain()
    event = LedgerEvent.new(
        event_id="evt-1",
        event_type="image.registered",
        principal_id="user-1",
        image_id="img-1",
    )

    chain.append([event])

    assert len(chain.blocks) == 2
    assert chain.verify() is True


def test_chain_verify_fails_after_tamper() -> None:
    chain = LedgerChain()
    event = LedgerEvent.new(
        event_id="evt-1",
        event_type="image.registered",
        principal_id="user-1",
        image_id="img-1",
    )
    chain.append([event])

    tampered = replace(chain.blocks[1], previous_hash="bad")
    chain.blocks[1] = tampered

    assert chain.verify() is False


def test_chain_verify_fails_if_genesis_tampered() -> None:
    chain = LedgerChain()
    tampered_genesis = replace(chain.blocks[0], timestamp="2000-01-01T00:00:00+00:00")
    chain.blocks[0] = tampered_genesis

    assert chain.verify() is False


def test_chain_append_rejects_empty_event_list() -> None:
    chain = LedgerChain()

    with pytest.raises(ValueError):
        chain.append([])
