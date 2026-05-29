from __future__ import annotations

from pathlib import Path

import pytest

from imago.storage.filesystem import FilesystemObjectStorage


@pytest.mark.unit
def test_filesystem_object_storage_writes_and_deletes_file(tmp_path: Path) -> None:
    storage = FilesystemObjectStorage(str(tmp_path))

    etag = storage.put_object(
        key="study-1/series-1/image-1.dcm",
        payload=b"dicom-bytes",
        content_type="application/dicom",
    )

    target = tmp_path / "study-1" / "series-1" / "image-1.dcm"
    assert target.read_bytes() == b"dicom-bytes"
    assert len(etag) == 64

    storage.delete_object("study-1/series-1/image-1.dcm")
    assert not target.exists()


@pytest.mark.unit
def test_filesystem_object_storage_rejects_parent_traversal(tmp_path: Path) -> None:
    storage = FilesystemObjectStorage(str(tmp_path))

    with pytest.raises(ValueError):
        storage.put_object(
            key="../escape.dcm",
            payload=b"x",
            content_type="application/dicom",
        )
