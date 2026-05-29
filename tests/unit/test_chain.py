from dataclasses import replace

from imago.domain.events import LedgerEvent
from imago.ledger.chain import LedgerChain


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
