"""Tests for utils/volumes.py — select_volume() interactive/non-interactive behavior.

Regression coverage for the "scheduled/scripted use" fix: when stdin is not
a TTY (cron, launchd, pipes, CI) and multiple volumes are present,
select_volume() must never block on input() and must instead auto-select
the default (root) volume.
"""

import io
import sys
import os
import builtins
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import utils.volumes as volumes_module
from utils.volumes import select_volume


def _make_volume(index, name, path, total_human='100.0 GB', used_human='50.0 GB', used_percent=50.0):
    return {
        'index': index,
        'name': name,
        'path': path,
        'info': {
            'path': path,
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'used_percent': used_percent,
            'total_human': total_human,
            'used_human': used_human,
            'free_human': '50.0 GB',
        },
    }


class FakeStdin(io.StringIO):
    """A stand-in for sys.stdin with a controllable isatty() result.

    Because this is not sys.__stdin__, builtin input() reads via
    readline() rather than the real terminal, so it works as a drop-in
    for simulating typed input regardless of the isatty() value.
    """

    def __init__(self, data='', tty=True):
        super().__init__(data)
        self._tty = tty

    def isatty(self):
        return self._tty


def _refuse_input(*args, **kwargs):
    raise AssertionError("input() should not have been called")


class TestMultipleVolumesNonTty:
    def test_auto_selects_root_volume_without_prompting(self, monkeypatch, capsys):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_volume(2, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=False))
        monkeypatch.setattr(builtins, 'input', _refuse_input)

        result = select_volume()

        assert result == '/'
        out = capsys.readouterr().out
        assert 'Auto-selected' in out
        assert 'Macintosh HD' in out
        assert '--volume' in out

    def test_isatty_raising_is_treated_as_non_tty(self, monkeypatch, capsys):
        """If isatty() itself blows up, treat that as 'not a TTY' rather than crashing."""
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_volume(2, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda: vols)

        class ExplodingStdin:
            def isatty(self):
                raise OSError("no controlling terminal")

        monkeypatch.setattr(sys, 'stdin', ExplodingStdin())
        monkeypatch.setattr(builtins, 'input', _refuse_input)

        result = select_volume()

        assert result == '/'
        assert 'Auto-selected' in capsys.readouterr().out


class TestMultipleVolumesTty:
    def test_user_selects_second_volume(self, monkeypatch):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_volume(2, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('2\n', tty=True))

        result = select_volume()

        assert result == '/Volumes/Backup'

    def test_empty_input_returns_default(self, monkeypatch):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_volume(2, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('\n', tty=True))

        result = select_volume()

        assert result == '/'


class TestExplicitVolumePath:
    @pytest.mark.parametrize('tty', [True, False])
    def test_explicit_path_short_circuits_regardless_of_tty(self, monkeypatch, tmp_path, tty):
        def _fail_list_volumes():
            raise AssertionError("list_volumes() should not have been called")

        monkeypatch.setattr(volumes_module, 'list_volumes', _fail_list_volumes)
        monkeypatch.setattr(builtins, 'input', _refuse_input)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=tty))
        monkeypatch.setattr(
            volumes_module, 'get_volume_info',
            lambda path: {'total_human': '1.0 GB', 'used_human': '0.5 GB', 'used_percent': 50.0}
        )

        result = select_volume(str(tmp_path))

        assert result == str(tmp_path)


class TestSingleVolume:
    @pytest.mark.parametrize('tty', [True, False])
    def test_single_volume_auto_selects_no_input(self, monkeypatch, tty):
        vols = [_make_volume(1, 'Macintosh HD', '/')]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=tty))
        monkeypatch.setattr(builtins, 'input', _refuse_input)

        result = select_volume()

        assert result == '/'
