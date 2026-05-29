"""Storage adapter interfaces and strategy helpers."""

from imago.storage.contracts import IngestionPayload, IngestionResult
from imago.storage.policy import (
	DataClassification,
	FormatFamily,
	FormatProfile,
	profile_for_format,
)

__all__ = [
	"DataClassification",
	"FormatFamily",
	"FormatProfile",
	"IngestionPayload",
	"IngestionResult",
	"profile_for_format",
]
