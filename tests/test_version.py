"""Tests for utils/version.py - BUILD resolution logic."""

import subprocess
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import utils.version as version_module


def _clear_stamp_cache(monkeypatch):
    """Ensure no leftover utils._build_stamp entry survives from a previous
    test or a real (accidental) build artifact on disk."""
    monkeypatch.setitem(sys.modules, 'utils._build_stamp', None)


def _fail_if_called(*args, **kwargs):
    raise AssertionError("subprocess.run should not have been called")


class TestGetBuildStamped:
    def test_stamp_takes_priority(self, monkeypatch):
        fake_module = types.ModuleType('utils._build_stamp')
        fake_module.BUILD = "2026-08-15-stamped01"
        monkeypatch.setitem(sys.modules, 'utils._build_stamp', fake_module)

        assert version_module.get_build() == "2026-08-15-stamped01"

    def test_stamp_wins_even_when_not_frozen(self, monkeypatch):
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)
        fake_module = types.ModuleType('utils._build_stamp')
        fake_module.BUILD = "2026-08-15-stamped02"
        monkeypatch.setitem(sys.modules, 'utils._build_stamp', fake_module)

        def fail_run(*a, **k):
            raise AssertionError("git should not be consulted when a stamp exists")
        monkeypatch.setattr(version_module.subprocess, 'run', fail_run)

        assert version_module.get_build() == "2026-08-15-stamped02"


class TestGetBuildFrozen:
    def test_frozen_without_stamp_never_touches_subprocess(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.setattr(version_module.sys, 'frozen', True, raising=False)
        monkeypatch.setattr(version_module.subprocess, 'run', _fail_if_called)

        result = version_module.get_build()

        assert result == version_module._FALLBACK_BUILD
        assert isinstance(result, str) and result

    def test_frozen_with_stamp_still_never_touches_subprocess(self, monkeypatch):
        monkeypatch.setattr(version_module.sys, 'frozen', True, raising=False)
        fake_module = types.ModuleType('utils._build_stamp')
        fake_module.BUILD = "2026-08-15-frozenstamp"
        monkeypatch.setitem(sys.modules, 'utils._build_stamp', fake_module)
        monkeypatch.setattr(version_module.subprocess, 'run', _fail_if_called)

        assert version_module.get_build() == "2026-08-15-frozenstamp"


class TestGetBuildFromGit:
    def test_git_derivation_clean_tree(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ['git', 'log']:
                return subprocess.CompletedProcess(cmd, 0, stdout="2026-08-15-abc1234\n", stderr="")
            if cmd[:2] == ['git', 'status']:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(version_module.subprocess, 'run', fake_run)

        assert version_module.get_build() == "2026-08-15-abc1234"

    def test_git_derivation_dirty_tree(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ['git', 'log']:
                return subprocess.CompletedProcess(cmd, 0, stdout="2026-08-15-abc1234\n", stderr="")
            if cmd[:2] == ['git', 'status']:
                return subprocess.CompletedProcess(cmd, 0, stdout=" M askdad.py\n", stderr="")
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(version_module.subprocess, 'run', fake_run)

        assert version_module.get_build() == "2026-08-15-abc1234-dirty"

    def test_git_status_failure_still_returns_clean_build(self, monkeypatch):
        """If `git status` itself fails, we still return the build id from
        `git log`, just without a -dirty suffix - dirty detection is
        best-effort, not something that should ever crash resolution."""
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ['git', 'log']:
                return subprocess.CompletedProcess(cmd, 0, stdout="2026-08-15-abc1234\n", stderr="")
            if cmd[:2] == ['git', 'status']:
                raise OSError("boom")
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(version_module.subprocess, 'run', fake_run)

        assert version_module.get_build() == "2026-08-15-abc1234"


class TestGetBuildNoGit:
    def test_git_not_installed(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def raise_fnf(*a, **k):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(version_module.subprocess, 'run', raise_fnf)

        result = version_module.get_build()
        assert result == version_module._FALLBACK_BUILD

    def test_not_a_git_repo(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 128, stdout="", stderr="fatal: not a git repository")

        monkeypatch.setattr(version_module.subprocess, 'run', fake_run)

        result = version_module.get_build()
        assert result == version_module._FALLBACK_BUILD

    def test_git_times_out(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd='git', timeout=2)

        monkeypatch.setattr(version_module.subprocess, 'run', raise_timeout)

        result = version_module.get_build()
        assert result == version_module._FALLBACK_BUILD

    def test_git_raises_unexpected_exception(self, monkeypatch):
        """Any other subprocess failure must also be swallowed - get_build()
        must never raise, no matter what goes wrong shelling out to git."""
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def raise_weird(*a, **k):
            raise PermissionError("no exec bit")

        monkeypatch.setattr(version_module.subprocess, 'run', raise_weird)

        result = version_module.get_build()
        assert result == version_module._FALLBACK_BUILD

    def test_empty_git_output_falls_back(self, monkeypatch):
        _clear_stamp_cache(monkeypatch)
        monkeypatch.delattr(version_module.sys, 'frozen', raising=False)

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout="   \n", stderr="")

        monkeypatch.setattr(version_module.subprocess, 'run', fake_run)

        result = version_module.get_build()
        assert result == version_module._FALLBACK_BUILD


class TestGetBuildAlwaysReturnsString:
    def test_result_is_always_a_non_empty_string(self, monkeypatch):
        # Exercise the resolver against whatever the real environment
        # provides (real repo, real git) - it must never raise and must
        # always hand back a usable string.
        result = version_module.get_build()
        assert isinstance(result, str)
        assert result != ""


class TestYourdadExposesVersionInfo:
    def test_askdad_module_has_version_and_build(self):
        import askdad
        assert isinstance(askdad.VERSION, str) and askdad.VERSION
        assert isinstance(askdad.BUILD, str) and askdad.BUILD

    def test_module_level_build_matches_get_build_shape(self):
        # The module-level BUILD constant is resolved once at import time;
        # just confirm it's a sane, non-empty string (it can't be recomputed
        # here without reloading the module, which would re-trigger real
        # subprocess/git calls unrelated to what this test is checking).
        assert isinstance(version_module.BUILD, str) and version_module.BUILD
        assert isinstance(version_module.VERSION, str) and version_module.VERSION
