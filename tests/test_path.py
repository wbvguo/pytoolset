import pytest
from pathlib import Path
from pytoolset import find_project_root


def test_finds_marker_in_anchor_dir(tmp_path):
    (tmp_path / "pyproject.toml").touch()
    assert find_project_root(anchor=tmp_path) == tmp_path


def test_finds_marker_in_parent(tmp_path):
    (tmp_path / "pyproject.toml").touch()
    subdir = tmp_path / "sub" / "dir"
    subdir.mkdir(parents=True)
    assert find_project_root(anchor=subdir) == tmp_path


def test_anchor_can_be_a_file(tmp_path):
    (tmp_path / "pyproject.toml").touch()
    f = tmp_path / "main.py"
    f.touch()
    assert find_project_root(anchor=f) == tmp_path


def test_raises_when_marker_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="pyproject.toml"):
        find_project_root(anchor=tmp_path)


def test_custom_marker(tmp_path):
    (tmp_path / "setup.cfg").touch()
    subdir = tmp_path / "pkg"
    subdir.mkdir()
    assert find_project_root(anchor=subdir, marker="setup.cfg") == tmp_path
