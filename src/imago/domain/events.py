from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_type: str
    principal_id: str
    image_id: str
    occurred_at: str

    @classmethod
    def new(
        cls,
        event_id: str,
        event_type: str,
        principal_id: str,
        image_id: str,
    ) -> "LedgerEvent":
        return cls(
            event_id=event_id,
            event_type=event_type,
            principal_id=principal_id,
            image_id=image_id,
            occurred_at=datetime.now(UTC).isoformat(),
        )
