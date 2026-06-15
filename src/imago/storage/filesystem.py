from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath


class FilesystemObjectStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def put_object(self, key: str, payload: bytes, content_type: str) -> str:
        del content_type
        target = self._resolve_target(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def delete_object(self, key: str) -> None:
        target = self._resolve_target(key)
        if target.exists():
            target.unlink()

    def get_object(self, key: str) -> bytes:
        target = self._resolve_target(key)
        if not target.exists():
            raise KeyError(f"unknown object_key: {key}")
        return target.read_bytes()

    def _resolve_target(self, key: str) -> Path:
        normalized = PurePosixPath(key)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("object key must be a relative path")

        target = self._root.joinpath(*normalized.parts).resolve()
        if self._root not in target.parents and target != self._root:
            raise ValueError("object key escapes storage root")
        return target
