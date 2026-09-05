"""Tests for the safe path formatter."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from da_downloader.path import PathFormatter, sanitize_segment


def resolve(formatter: PathFormatter, **overrides) -> Path:
    kwargs = dict(
        id="123-abc",
        title="Sunset Landscape",
        author="alice",
        ext="jpg",
    )
    kwargs.update(overrides)
    return formatter.resolve(**kwargs)


def test_default_template(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path)
    assert resolve(formatter) == tmp_path / "alice" / "123-abc_Sunset Landscape.jpg"


def test_nested_directory_with_strftime(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path, directory="{author}/{published:%Y-%m}")
    path = resolve(formatter, published=date(2025, 1, 15))
    assert path == tmp_path / "alice" / "2025-01" / "123-abc_Sunset Landscape.jpg"


def test_custom_filename_template(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path, filename="{id}.{ext}")
    assert resolve(formatter).name == "123-abc.jpg"


def test_flat_directory(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path, directory="")
    path = resolve(formatter)
    assert path == tmp_path / "123-abc_Sunset Landscape.jpg"


def test_illegal_characters_are_replaced(tmp_path: Path) -> None:
    path = resolve(PathFormatter(tmp_path), title='a/b:c*d?e"f<g>h|i')
    assert path.parent == tmp_path / "alice"
    assert path.name == "123-abc_a_b_c_d_e_f_g_h_i.jpg"


def test_empty_title_gets_fallback(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path)
    path = resolve(formatter, title="")
    assert path.name == "123-abc__untitled.jpg"


def test_path_traversal_is_neutralized(tmp_path: Path) -> None:
    path = resolve(PathFormatter(tmp_path), author="../../etc")
    assert path.is_relative_to(tmp_path)
    assert ".." not in path.parts


def test_windows_reserved_name_is_prefixed(tmp_path: Path) -> None:
    path = resolve(PathFormatter(tmp_path), title="CON")
    assert "_CON" in path.name


def test_long_title_is_truncated(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path, max_length=20)
    path = resolve(formatter, title="x" * 500)
    assert len(path.name) <= 20
    assert path.name.endswith(".jpg")


def test_trailing_dots_and_spaces_are_stripped(tmp_path: Path) -> None:
    path = resolve(PathFormatter(tmp_path), title="hello...   ")
    assert not path.name.endswith(".")


def test_extension_leading_dot_is_normalized(tmp_path: Path) -> None:
    formatter = PathFormatter(tmp_path, filename="{filename}.{ext}")
    assert resolve(formatter, filename="pic", ext=".png").name == "pic.png"


def test_sanitize_segment_guards_dot_components() -> None:
    assert sanitize_segment("..") == "_"
    assert sanitize_segment(".") == "_"
    assert sanitize_segment("") == "_"
    assert sanitize_segment("normal") == "normal"
