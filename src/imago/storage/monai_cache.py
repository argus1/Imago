from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Callable

from imago.config.settings import Settings
from imago.storage.policy import DataClassification


class MonaiCacheMode(StrEnum):
    DISABLED = "disabled"
    CACHE_DATASET = "cache_dataset"
    PERSISTENT_DATASET = "persistent_dataset"


@dataclass(frozen=True)
class MonaiCacheConfig:
    mode: MonaiCacheMode
    transform_version: str
    retention_hours: int
    max_items: int
    persistent_cache_dir: Path | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "MonaiCacheConfig":
        mode = MonaiCacheMode(settings.monai_cache_mode.strip().lower())
        storage_root = Path(settings.storage_root).resolve()

        if mode == MonaiCacheMode.PERSISTENT_DATASET:
            cache_dir = Path(settings.monai_persistent_cache_dir).resolve()
            if _is_subpath(cache_dir, storage_root):
                raise ValueError(
                    "MONAI persistent cache directory must be outside immutable storage_root",
                )
        else:
            cache_dir = None

        return cls(
            mode=mode,
            transform_version=settings.monai_transform_version,
            retention_hours=settings.monai_cache_retention_hours,
            max_items=settings.monai_cache_max_items,
            persistent_cache_dir=cache_dir,
        )


@dataclass(frozen=True)
class CacheLineageRecord:
    lineage_id: str
    source_object_key: str
    source_object_hash: str
    classification: DataClassification
    cache_mode: MonaiCacheMode
    cache_artifact_ref: str
    transform_version: str
    created_at: datetime


class InMemoryMonaiCacheLineageStore:
    def __init__(self) -> None:
        self._records: list[CacheLineageRecord] = []

    def append(self, record: CacheLineageRecord) -> None:
        self._records.append(record)

    def list_records(self) -> list[CacheLineageRecord]:
        return list(self._records)


class MonaiCacheCoordinator:
    def __init__(
        self,
        config: MonaiCacheConfig,
        lineage_store: InMemoryMonaiCacheLineageStore,
    ) -> None:
        self._config = config
        self._lineage_store = lineage_store

    def register_cache_artifact(
        self,
        *,
        source_object_key: str,
        source_object_hash: str,
        classification: DataClassification,
        cache_artifact_ref: str,
    ) -> CacheLineageRecord:
        if self._config.mode == MonaiCacheMode.DISABLED:
            raise RuntimeError("MONAI cache mode is disabled")

        created_at = datetime.now(UTC)
        lineage_id = hashlib.sha256(
            (
                f"{source_object_key}:{source_object_hash}:{cache_artifact_ref}:"
                f"{self._config.mode.value}:{self._config.transform_version}:{created_at.isoformat()}"
            ).encode("utf-8"),
        ).hexdigest()

        record = CacheLineageRecord(
            lineage_id=lineage_id,
            source_object_key=source_object_key,
            source_object_hash=source_object_hash,
            classification=classification,
            cache_mode=self._config.mode,
            cache_artifact_ref=cache_artifact_ref,
            transform_version=self._config.transform_version,
            created_at=created_at,
        )
        self._lineage_store.append(record)
        return record

    def verify_canonical_source_immutability(
        self,
        *,
        object_key: str,
        expected_hash: str,
        hash_reader: Callable[[str], str],
    ) -> bool:
        computed_hash = hash_reader(object_key)
        return hmac.compare_digest(computed_hash, expected_hash.lower())


def _is_subpath(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True
