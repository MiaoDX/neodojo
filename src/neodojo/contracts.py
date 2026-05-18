from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

ANNOTATION_SCHEMA = "neodojo.annotation.v1"
HTML_DEMO_SCHEMA = "neodojo.html_demo.v1"
PLAYBACK_SCHEMA = "neodojo.playback_manifest.v1"
PUBLIC_DEMO_SCHEMA = "neodojo.public_demo.v1"
TWO_PANEL_TEACHING_HTML_PROFILE = "neodojo.two_panel_teaching_replay.v1"


def require_schema(payload: dict[str, Any], expected_schema: str, label: str) -> None:
    actual = payload.get("schema")
    if actual != expected_schema:
        raise ValueError(f"{label} must use schema {expected_schema}; got {actual!r}")


def _as_posix(path: Path) -> str:
    return str(path).replace(os.sep, "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_file_metadata(path: Path, *, label: str, allowed_suffixes: set[str] | None = None) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")
    suffix = path.suffix.lower()
    if allowed_suffixes is not None and suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise ValueError(f"{label} must have one of these suffixes: {allowed}")

    resolved = path.resolve()
    return {
        "path": _as_posix(path),
        "resolved_path": _as_posix(resolved),
        "suffix": suffix,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "local_only": True,
    }
