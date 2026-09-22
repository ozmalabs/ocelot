from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes, parse_canonical
from .interfaces import Object, ObjectStore, StoreError


class MemoryStore(ObjectStore):
    """Generation-checked store used by unit tests and local development."""
    def __init__(self, objects: dict[str, dict[str, Any]] | None = None):
        self._objects: dict[str, Object] = {}
        for name, value in (objects or {}).items():
            self._objects[name] = Object(canonical_bytes(value), 1)

    def get(self, name: str) -> Object:
        try:
            return self._objects[name]
        except KeyError as exc:
            raise StoreError("object not found") from exc

    def create(self, name: str, data: bytes) -> Object:
        if name in self._objects:
            raise StoreError("object already exists")
        item = Object(bytes(data), 1)
        self._objects[name] = item
        return item

    def replace(self, name: str, data: bytes, generation: int) -> Object:
        current = self.get(name)
        if current.generation != generation:
            raise StoreError("generation conflict")
        item = Object(bytes(data), generation + 1)
        self._objects[name] = item
        return item

    def put_json(self, name: str, value: dict[str, Any]) -> Object:
        return self.create(name, canonical_bytes(value))


def _is_not_found_error(exc: BaseException) -> bool:
    """Recognize the GCS client's not-found shape without importing its SDK."""
    code = getattr(exc, "code", None)
    if code == 404 or code == "404":
        return True
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None) == 404


class GCSStore(ObjectStore):
    """Private GCS adapter; secure callers must inject federated credentials."""
    def __init__(self, bucket: str, prefix: str = "", *, client: Any | None = None):
        if not bucket:
            raise ValueError("bucket is required")
        if client is None:
            raise StoreError("explicit federated GCS client is required")
        self._bucket = client.bucket(bucket)
        self._prefix = prefix.strip("/")

    def _blob(self, name: str):
        safe = name.strip("/")
        if ".." in safe.split("/"):
            raise StoreError("invalid object name")
        return self._bucket.blob("/".join(x for x in (self._prefix, safe) if x))

    def get(self, name: str) -> Object:
        blob = self._blob(name)
        try:
            blob.reload()
            return Object(blob.download_as_bytes(), int(blob.generation))
        except Exception as exc:
            if _is_not_found_error(exc):
                # Operation-4 uses this stable boundary to distinguish an
                # absent object (generation 0 / create-only) from a remote
                # read failure.  Do not expose SDK-specific exceptions.
                raise StoreError("object not found") from exc
            raise StoreError("object read failed") from exc

    def create(self, name: str, data: bytes) -> Object:
        blob = self._blob(name)
        try:
            blob.upload_from_string(data, content_type="application/json", if_generation_match=0)
            return Object(bytes(data), int(blob.generation))
        except Exception as exc:
            raise StoreError("object create failed") from exc

    def replace(self, name: str, data: bytes, generation: int) -> Object:
        blob = self._blob(name)
        try:
            blob.upload_from_string(data, content_type="application/json", if_generation_match=generation)
            return Object(bytes(data), int(blob.generation))
        except Exception as exc:
            raise StoreError("object generation conflict") from exc


def get_json(store: ObjectStore, name: str) -> tuple[dict[str, Any], int]:
    item = store.get(name)
    try:
        return parse_canonical(item.data), item.generation
    except Exception as exc:
        raise StoreError("stored object is not canonical") from exc
