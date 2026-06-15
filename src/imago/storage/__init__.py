"""Storage adapter interfaces and strategy helpers."""

from imago.storage.contracts import IngestionPayload, IngestionResult
from imago.storage.filesystem import FilesystemObjectStorage
from imago.storage.ingestion import AtomicIngestionCoordinator, IngestionError
from imago.storage.monai_cache import (
	CacheLineageRecord,
	InMemoryMonaiCacheLineageStore,
	MonaiCacheConfig,
	MonaiCacheCoordinator,
	MonaiCacheMode,
)
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
	"AtomicIngestionCoordinator",
	"MonaiCacheMode",
	"MonaiCacheConfig",
	"MonaiCacheCoordinator",
	"CacheLineageRecord",
	"InMemoryMonaiCacheLineageStore",
	"FilesystemObjectStorage",
	"IngestionPayload",
	"IngestionResult",
	"IngestionError",
	"profile_for_format",
]
