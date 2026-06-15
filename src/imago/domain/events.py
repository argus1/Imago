from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_type: str
    principal_id: str
    image_id: str
    occurred_at: str

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        if not self.principal_id.strip():
            raise ValueError("principal_id must not be empty")
        if not self.image_id.strip():
            raise ValueError("image_id must not be empty")
        if not self.occurred_at.strip():
            raise ValueError("occurred_at must not be empty")

        parsed = datetime.fromisoformat(self.occurred_at)
        if parsed.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware ISO-8601")

    @classmethod
    def new(
        cls,
        event_id: str,
        event_type: str,
        principal_id: str,
        image_id: str,
    ) -> LedgerEvent:
        return cls(
            event_id=event_id.strip(),
            event_type=event_type.strip(),
            principal_id=principal_id.strip(),
            image_id=image_id.strip(),
            occurred_at=datetime.now(UTC).isoformat(),
        )
