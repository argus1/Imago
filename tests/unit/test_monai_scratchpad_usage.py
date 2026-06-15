from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from imago.application.monai_scratchpad import MonaiScratchpadUsageService
from imago.config.settings import Settings
from imago.storage.monai_cache import (
    InMemoryMonaiCacheLineageStore,
    MonaiCacheConfig,
    MonaiCacheCoordinator,
)
from imago.storage.policy import DataClassification


def _coordinator(tmp_path: Path) -> tuple[MonaiCacheCoordinator, InMemoryMonaiCacheLineageStore]:
    settings = Settings(
        storage_root=str(tmp_path / "archive"),
        monai_cache_mode="cache_dataset",
        monai_transform_version="tfm-unit",
    )
    config = MonaiCacheConfig.from_settings(settings)
    store = InMemoryMonaiCacheLineageStore()
    return MonaiCacheCoordinator(config=config, lineage_store=store), store


@pytest.mark.unit
def test_process_cache_artifact_emits_lineage_when_enabled(tmp_path: Path) -> None:
    coordinator, store = _coordinator(tmp_path)
    settings = Settings(monai_emit_lineage_records=True)
    service = MonaiScratchpadUsageService.from_settings(coordinator=coordinator, settings=settings)

    source_hash = hashlib.sha256(b"raw-canonical").hexdigest()
    result = service.process_cache_artifact(
        source_object_key="study-a/image-1.dcm",
        source_object_hash=source_hash,
        classification=DataClassification.RESTRICTED_CLINICAL,
        cache_artifact_ref="ram://cache/item-1",
    )

    assert result.lineage_record_emitted is True
    assert result.lineage_id is not None
    assert len(store.list_records()) == 1


@pytest.mark.unit
def test_process_cache_artifact_skips_lineage_when_disabled(tmp_path: Path) -> None:
    coordinator, store = _coordinator(tmp_path)
    settings = Settings(monai_emit_lineage_records=False)
    service = MonaiScratchpadUsageService.from_settings(coordinator=coordinator, settings=settings)

    source_hash = hashlib.sha256(b"raw-canonical").hexdigest()
    result = service.process_cache_artifact(
        source_object_key="study-a/image-2.dcm",
        source_object_hash=source_hash,
        classification=DataClassification.RESTRICTED_CLINICAL,
        cache_artifact_ref="ram://cache/item-2",
    )

    assert result.lineage_record_emitted is False
    assert result.lineage_id is None
    assert store.list_records() == []


@pytest.mark.unit
def test_verify_canonical_source_passes_through(tmp_path: Path) -> None:
    coordinator, _ = _coordinator(tmp_path)
    settings = Settings(monai_emit_lineage_records=False)
    service = MonaiScratchpadUsageService.from_settings(coordinator=coordinator, settings=settings)

    source_hash = hashlib.sha256(b"raw-canonical").hexdigest()
    assert service.verify_canonical_source(
        object_key="study-a/image-3.dcm",
        expected_hash=source_hash,
        hash_reader=lambda _: source_hash,
    )
