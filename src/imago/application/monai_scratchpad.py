from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from imago.config.settings import Settings
from imago.storage.monai_cache import CacheLineageRecord, MonaiCacheCoordinator
from imago.storage.policy import DataClassification


@dataclass(frozen=True)
class ScratchpadUsageResult:
    source_object_key: str
    source_object_hash: str
    cache_artifact_ref: str
    lineage_record_emitted: bool
    lineage_id: str | None = None


class MonaiScratchpadUsageService:
    """Coordinates MONAI scratchpad usage without mutating canonical source records."""

    def __init__(
        self,
        coordinator: MonaiCacheCoordinator,
        *,
        emit_lineage_records: bool,
    ) -> None:
        self._coordinator = coordinator
        self._emit_lineage_records = emit_lineage_records

    @classmethod
    def from_settings(
        cls,
        *,
        coordinator: MonaiCacheCoordinator,
        settings: Settings,
    ) -> "MonaiScratchpadUsageService":
        return cls(
            coordinator,
            emit_lineage_records=settings.monai_emit_lineage_records,
        )

    def process_cache_artifact(
        self,
        *,
        source_object_key: str,
        source_object_hash: str,
        classification: DataClassification,
        cache_artifact_ref: str,
    ) -> ScratchpadUsageResult:
        lineage_record: CacheLineageRecord | None = None
        if self._emit_lineage_records:
            lineage_record = self._coordinator.register_cache_artifact(
                source_object_key=source_object_key,
                source_object_hash=source_object_hash,
                classification=classification,
                cache_artifact_ref=cache_artifact_ref,
            )

        return ScratchpadUsageResult(
            source_object_key=source_object_key,
            source_object_hash=source_object_hash,
            cache_artifact_ref=cache_artifact_ref,
            lineage_record_emitted=lineage_record is not None,
            lineage_id=None if lineage_record is None else lineage_record.lineage_id,
        )

    def verify_canonical_source(
        self,
        *,
        object_key: str,
        expected_hash: str,
        hash_reader: Callable[[str], str],
    ) -> bool:
        return self._coordinator.verify_canonical_source_immutability(
            object_key=object_key,
            expected_hash=expected_hash,
            hash_reader=hash_reader,
        )
