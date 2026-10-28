"""Physical M8.1 filesystem edges and explicitly supplementary fail-closed checks."""

import os
import stat
from types import SimpleNamespace

import pytest
from test_m8_security import link_directory

from blackbox_twin.m7_data import contained
from blackbox_twin.run_limits import storage_size


def test_physical_broken_output_root_rejected(tmp_path):
    target, link = tmp_path / "target", tmp_path / "runs"
    target.mkdir()
    link_directory(link, target)
    target.rename(tmp_path / "moved-target")
    with pytest.raises(ValueError, match="Linked"):
        storage_size(link)
    assert not list((tmp_path / "moved-target").iterdir())


def test_physical_nested_link_chain_cannot_escape(tmp_path):
    root, middle, outside = (tmp_path / n for n in ("root", "middle", "outside"))
    for path in (root, middle, outside):
        path.mkdir()
    link_directory(middle / "next", outside)
    link_directory(root / "entry", middle)
    with pytest.raises(ValueError, match="leaves"):
        contained(root, "entry/next/owned.txt")
    assert not (outside / "owned.txt").exists()


def test_physical_replacement_before_revalidation_rejected(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "data").mkdir()
    assert contained(root, "data").is_dir()
    (root / "data").rename(root / "original-data")
    link_directory(root / "data", outside)
    with pytest.raises(ValueError, match="leaves"):
        contained(root, "data/owned.txt")
    assert not list(outside.iterdir())


def test_supplementary_dangling_reparse_root_is_not_missing(tmp_path, monkeypatch):
    # Controlled metadata is supplementary; it does not claim OS link creation passed.
    root = tmp_path / "missing-owned-root"
    original = type(root).lstat

    def metadata(path, *args, **kwargs):
        if path == root:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024),
            )
        return original(path, *args, **kwargs)

    if os.name != "nt":
        monkeypatch.setattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024, raising=False)
    monkeypatch.setattr(type(root), "lstat", metadata)
    with pytest.raises(ValueError, match="Linked"):
        storage_size(root)


def test_missing_output_root_has_zero_existing_storage(tmp_path):
    assert storage_size(tmp_path / "not-created") == 0
