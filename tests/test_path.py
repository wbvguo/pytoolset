import pytest
from pathlib import Path
from pytoolset import find_project_root, get_absolute_path, mkdir


def test_mkdir_creates_directory(tmp_path):
    target = tmp_path / "new_dir"
    result = mkdir(target)
    assert target.is_dir()
    assert result == target


def test_mkdir_creates_nested_directories(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    mkdir(target)
    assert target.is_dir()


def test_mkdir_skips_existing_and_prints(tmp_path, capsys):
    target = tmp_path / "existing"
    target.mkdir()
    mkdir(target)
    assert f"{target} exists! Skip creating..." in capsys.readouterr().out


def test_mkdir_returns_path_object(tmp_path):
    target = tmp_path / "new_dir"
    result = mkdir(target)
    assert isinstance(result, Path)


def test_mkdir_accepts_string(tmp_path):
    target = str(tmp_path / "str_dir")
    result = mkdir(target)
    assert Path(target).is_dir()
    assert result == Path(target).resolve()


def test_mkdir_returns_absolute_path(tmp_path):
    result = mkdir(tmp_path / "new_dir")
    assert result.is_absolute()


def test_get_absolute_path_from_string(tmp_path):
    result = get_absolute_path(str(tmp_path))
    assert result == tmp_path.resolve()
    assert result.is_absolute()


def test_get_absolute_path_from_path(tmp_path):
    result = get_absolute_path(tmp_path)
    assert result == tmp_path.resolve()
    assert result.is_absolute()


def test_get_absolute_path_returns_path_object(tmp_path):
    assert isinstance(get_absolute_path(tmp_path), Path)


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
