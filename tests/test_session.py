from __future__ import annotations

import sys
import types

from pytoolset import sessionInfo


def test_session_info_returns_none(capsys):
    assert sessionInfo() is None
    capsys.readouterr()  # drain


def test_session_info_prints_header_fields(capsys):
    sessionInfo()
    out = capsys.readouterr().out
    assert "Python version:" in out
    assert "Platform:" in out
    assert "Implementation:" in out
    assert "Architecture:" in out
    assert "Loaded packages:" in out


def test_session_info_lists_versioned_top_level_module(capsys):
    fake = types.ModuleType("fakepkg_for_test")
    fake.__version__ = "9.9.9"
    sys.modules["fakepkg_for_test"] = fake
    try:
        sessionInfo()
        out = capsys.readouterr().out
    finally:
        del sys.modules["fakepkg_for_test"]
    assert "fakepkg_for_test==9.9.9" in out


def test_session_info_excludes_dotted_submodules(capsys):
    parent = types.ModuleType("fakeparent")
    parent.__version__ = "1.0"
    child = types.ModuleType("fakeparent.sub")
    child.__version__ = "2.0"
    sys.modules["fakeparent"] = parent
    sys.modules["fakeparent.sub"] = child
    try:
        sessionInfo()
        out = capsys.readouterr().out
    finally:
        del sys.modules["fakeparent"]
        del sys.modules["fakeparent.sub"]
    assert "fakeparent==1.0" in out
    assert "fakeparent.sub==2.0" not in out


def test_session_info_excludes_modules_without_version(capsys):
    noversion = types.ModuleType("fakenoversion")  # no __version__
    sys.modules["fakenoversion"] = noversion
    try:
        sessionInfo()
        out = capsys.readouterr().out
    finally:
        del sys.modules["fakenoversion"]
    assert "fakenoversion==" not in out


def test_session_info_packages_listed_sorted(capsys):
    a = types.ModuleType("aaa_fakepkg")
    a.__version__ = "1.0"
    z = types.ModuleType("zzz_fakepkg")
    z.__version__ = "1.0"
    # insert z before a to prove output is sorted, not insertion-ordered
    sys.modules["zzz_fakepkg"] = z
    sys.modules["aaa_fakepkg"] = a
    try:
        sessionInfo()
        out = capsys.readouterr().out
    finally:
        del sys.modules["zzz_fakepkg"]
        del sys.modules["aaa_fakepkg"]
    assert out.index("aaa_fakepkg==") < out.index("zzz_fakepkg==")
