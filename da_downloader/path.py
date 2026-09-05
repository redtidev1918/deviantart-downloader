"""Safe filename/directory template rendering.

Renders ``{field}`` templates (Python ``format_map`` semantics, so datetime
fields support ``{published:%Y-%m}`` strftime specs) against artwork metadata,
then sanitizes every path segment so the result is always a valid relative path
inside the download root — never an absolute path, ``..``, or a Windows-reserved
name.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

# Characters that are illegal in a single path component (Windows set, plus the
# Unix separator '/').
_ILLEGAL = '<>:"/\\|?*'
_WINDOWS_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

DEFAULT_DIRECTORY = "{author}"
DEFAULT_FILENAME = "{id}_{title}.{ext}"


def sanitize_segment(segment: str, *, max_length: int = 200) -> str:
    """Return a single safe path component for ``segment``."""
    value = _CONTROL.sub("", segment)
    for char in _ILLEGAL:
        value = value.replace(char, "_")
    value = value.rstrip(". ")
    if value.upper() in _WINDOWS_RESERVED:
        value = "_" + value
    if len(value) > max_length:
        stem, ext = os.path.splitext(value)
        if ext and len(ext) <= 10:
            value = stem[: max_length - len(ext)] + ext
        else:
            value = value[:max_length]
        value = value.rstrip(". ")
    if not value or value in (".", ".."):
        value = "_"
    return value


class PathFormatter:
    """Renders directory/filename templates into a safe path under ``root``.

    ``directory`` may contain ``/`` to express nested folders (for example
    ``"{author}/{published:%Y-%m}"``); each segment is sanitized independently.
    ``filename`` is always sanitized as a single component.
    """

    def __init__(
        self,
        root: Path,
        *,
        directory: str = DEFAULT_DIRECTORY,
        filename: str = DEFAULT_FILENAME,
        max_length: int = 200,
    ) -> None:
        self.root = Path(root)
        self.directory_template = directory
        self.filename_template = filename
        self.max_length = max_length

    def resolve(
        self,
        *,
        id: str,
        title: str,
        author: str,
        username: Optional[str] = None,
        published: Any = None,
        filename: Optional[str] = None,
        ext: Optional[str] = None,
        index: Optional[int] = None,
    ) -> Path:
        fields = {
            "id": str(id),
            "title": title or "_untitled",
            "author": author or "_unknown",
            "username": username or author or "_unknown",
            "filename": filename or title or "_untitled",
            "ext": (ext or "").lstrip("."),
            "published": published if published is not None else "",
            "index": index if index is not None else "",
        }
        directory = self.directory_template.format_map(fields)
        name = self.filename_template.format_map(fields)

        segments = [
            sanitize_segment(part, max_length=self.max_length)
            for part in directory.replace("\\", "/").split("/")
            if part
        ]
        component = sanitize_segment(name, max_length=self.max_length)

        path = self.root.joinpath(*segments, component)
        if not path.is_relative_to(self.root):
            raise ValueError("resolved path escaped the download root")
        return path


__all__ = ["DEFAULT_DIRECTORY", "DEFAULT_FILENAME", "PathFormatter", "sanitize_segment"]
