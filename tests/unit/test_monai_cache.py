from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from imago.config.settings import Settings
from imago.storage.monai_cache import (
    InMemoryMonaiCacheLineageStore,
    MonaiCacheConfig,
    MonaiCacheCoordinator,
    MonaiCacheMode,
)
from imago.storage.policy import DataClassification


@pytest.mark.unit
def test_monai_cache_config_parses_cache_dataset_mode(tmp_path: Path) -> None:
    settings = Settings(
        storage_root=str(tmp_path / "archive"),
        monai_cache_mode="cache_dataset",
        monai_transform_version="v1.2.3",
        monai_cache_retention_hours=48,
        monai_cache_max_items=256,
    )

    config = MonaiCacheConfig.from_settings(settings)

    assert config.mode == MonaiCacheMode.CACHE_DATASET
    assert config.persistent_cache_dir is None
    assert config.transform_version == "v1.2.3"
    assert config.retention_hours == 48
    assert config.max_items == 256


@pytest.mark.unit
def test_monai_cache_config_rejects_persistent_cache_inside_storage_root(tmp_path: Path) -> None:
    storage_root = tmp_path / "archive"
    bad_cache_dir = storage_root / "cache"

    settings = Settings(
        storage_root=str(storage_root),
        monai_cache_mode="persistent_dataset",
        monai_persistent_cache_dir=str(bad_cache_dir),
    )

    with pytest.raises(ValueError, match="outside immutable storage_root"):
        MonaiCacheConfig.from_settings(settings)


@pytest.mark.unit
def test_monai_cache_lineage_recording_and_source_immutability(tmp_path: Path) -> None:
    source_payload = b"canonical-dicom-bytes"
    source_hash = hashlib.sha256(source_payload).hexdigest()

    settings = Settings(
        storage_root=str(tmp_path / "archive"),
        monai_cache_mode="persistent_dataset",
        monai_persistent_cache_dir=str(tmp_path / "scratch" / "monai"),
        monai_transform_version="tfm-2026-06-15",
    )
    config = MonaiCacheConfig.from_settings(settings)
    store = InMemoryMonaiCacheLineageStore()
    coordinator = MonaiCacheCoordinator(config=config, lineage_store=store)

    record = coordinator.register_cache_artifact(
        source_object_key="study-1/image-1.dcm",
        source_object_hash=source_hash,
        classification=DataClassification.RESTRICTED_CLINICAL,
        cache_artifact_ref="scratch://cache/item-1",
    )

    assert record.cache_mode == MonaiCacheMode.PERSISTENT_DATASET
    assert record.source_object_hash == source_hash
    assert record.transform_version == "tfm-2026-06-15"
    assert store.list_records() == [record]

    hash_reader = lambda key: source_hash if key == "study-1/image-1.dcm" else "x" * 64
    assert coordinator.verify_canonical_source_immutability(
        object_key="study-1/image-1.dcm",
        expected_hash=source_hash,
        hash_reader=hash_reader,
    )

    assert not coordinator.verify_canonical_source_immutability(
        object_key="study-1/image-1.dcm",
        expected_hash="0" * 64,
        hash_reader=hash_reader,
    )
