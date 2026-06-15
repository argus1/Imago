from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from imago.domain.events import LedgerEvent


@dataclass(frozen=True)
class LedgerBlock:
    index: int
    timestamp: str
    events: list[LedgerEvent]
    previous_hash: str
    block_hash: str


class LedgerChain:
    def __init__(self) -> None:
        self._blocks: list[LedgerBlock] = [self._build_genesis()]

    @property
    def blocks(self) -> list[LedgerBlock]:
        return self._blocks

    @staticmethod
    def canonical_hash(payload: dict[str, object]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def append(self, events: list[LedgerEvent]) -> LedgerBlock:
        if not events:
            raise ValueError("events must not be empty")

        previous = self._blocks[-1]
        index = previous.index + 1
        timestamp = datetime.now(UTC).isoformat()
        payload = {
            "index": index,
            "timestamp": timestamp,
            "events": [asdict(event) for event in events],
            "previous_hash": previous.block_hash,
        }
        block_hash = self.canonical_hash(payload)
        block = LedgerBlock(
            index=index,
            timestamp=timestamp,
            events=events,
            previous_hash=previous.block_hash,
            block_hash=block_hash,
        )
        self._blocks.append(block)
        return block

    def verify(self) -> bool:
        genesis = self._blocks[0]
        expected_genesis_payload = {
            "index": 0,
            "timestamp": "1970-01-01T00:00:00+00:00",
            "events": [],
            "previous_hash": "0",
        }
        if genesis.index != 0:
            return False
        if genesis.previous_hash != "0":
            return False
        if genesis.timestamp != expected_genesis_payload["timestamp"]:
            return False
        if genesis.events:
            return False
        if genesis.block_hash != self.canonical_hash(expected_genesis_payload):
            return False

        for idx in range(1, len(self._blocks)):
            current = self._blocks[idx]
            previous = self._blocks[idx - 1]
            if current.index != previous.index + 1:
                return False
            if current.previous_hash != previous.block_hash:
                return False
            payload = {
                "index": current.index,
                "timestamp": current.timestamp,
                "events": [asdict(event) for event in current.events],
                "previous_hash": current.previous_hash,
            }
            if self.canonical_hash(payload) != current.block_hash:
                return False
        return True

    def _build_genesis(self) -> LedgerBlock:
        payload = {
            "index": 0,
            "timestamp": "1970-01-01T00:00:00+00:00",
            "events": [],
            "previous_hash": "0",
        }
        return LedgerBlock(
            index=0,
            timestamp=str(payload["timestamp"]),
            events=[],
            previous_hash="0",
            block_hash=self.canonical_hash(payload),
        )
