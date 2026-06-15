from __future__ import annotations

from dataclasses import asdict, dataclass

from imago.domain.events import LedgerEvent
from imago.ledger.chain import LedgerBlock, LedgerChain


@dataclass(frozen=True)
class LedgerSubmissionResult:
    block: LedgerBlock
    reused: bool


class IdempotentLedgerService:
    """Submit events to a ledger chain with idempotency-key deduplication."""

    def __init__(self, chain: LedgerChain) -> None:
        self._chain = chain
        self._submitted: dict[str, tuple[str, str]] = {}

    @property
    def chain(self) -> LedgerChain:
        return self._chain

    def submit_events(
        self,
        *,
        idempotency_key: str,
        events: list[LedgerEvent],
    ) -> LedgerSubmissionResult:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if not events:
            raise ValueError("events must not be empty")

        request_hash = self._chain.canonical_hash(
            {
                "events": [asdict(event) for event in events],
            },
        )

        existing_submission = self._submitted.get(idempotency_key)
        if existing_submission is not None:
            existing_hash, existing_request_hash = existing_submission
            if existing_request_hash != request_hash:
                raise ValueError("idempotency_key reused with different payload")

            existing_block = self._find_block(existing_hash)
            if existing_block is not None:
                return LedgerSubmissionResult(block=existing_block, reused=True)

        block = self._chain.append(events)
        self._submitted[idempotency_key] = (block.block_hash, request_hash)
        return LedgerSubmissionResult(block=block, reused=False)

    def verify_chain(self) -> bool:
        return self._chain.verify()

    def _find_block(self, block_hash: str) -> LedgerBlock | None:
        for block in self._chain.blocks:
            if block.block_hash == block_hash:
                return block
        return None