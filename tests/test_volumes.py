"""Tests for utils/volumes.py — volume classification and select_volume().

Regression coverage for the "scheduled/scripted use" fix: when stdin is not
a TTY (cron, launchd, pipes, CI) and multiple volumes are present,
select_volume() must never block on input() and must instead auto-select
the default (root) volume.

Also covers volume classification: mounted disk images (a .dmg you are
installing from), network shares, and read-only mounts are not storage
devices and stay out of the picker unless asked for.
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
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
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
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)

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
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('2\n', tty=True))

        result = select_volume()

        assert result == '/Volumes/Backup'

    def test_empty_input_returns_default(self, monkeypatch):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_volume(2, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('\n', tty=True))

        result = select_volume()

        assert result == '/'


class TestExplicitVolumePath:
    @pytest.mark.parametrize('tty', [True, False])
    def test_explicit_path_short_circuits_regardless_of_tty(self, monkeypatch, tmp_path, tty):
        def _fail_list_volumes(**kwargs):
            raise AssertionError("list_volumes() should not have been called")

        monkeypatch.setattr(volumes_module, 'list_volumes', _fail_list_volumes)
        monkeypatch.setattr(builtins, 'input', _refuse_input)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=tty))
        monkeypatch.setattr(
            volumes_module, 'get_volume_info',
            lambda path: {'total_human': '1.0 GB', 'used_human': '0.5 GB', 'used_percent': 50.0}
        )
        monkeypatch.setattr(volumes_module, 'get_mount_fstypes', dict)
        monkeypatch.setattr(volumes_module, 'get_disk_image_mounts', dict)

        result = select_volume(str(tmp_path))

        assert result == str(tmp_path)


class TestSingleVolume:
    @pytest.mark.parametrize('tty', [True, False])
    def test_single_volume_auto_selects_no_input(self, monkeypatch, tty):
        vols = [_make_volume(1, 'Macintosh HD', '/')]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=tty))
        monkeypatch.setattr(builtins, 'input', _refuse_input)

        result = select_volume()

        assert result == '/'


def _make_hidden_volume(index, name, path, kind, skip_reason):
    vol = _make_volume(index, name, path)
    vol.update({'kind': kind, 'scannable': False, 'skip_reason': skip_reason})
    return vol


class TestClassifyVolume:
    def test_root_is_scannable_even_though_it_is_read_only(self, monkeypatch):
        """On modern macOS / is the sealed read-only system volume."""
        monkeypatch.setattr(volumes_module, 'is_read_only', lambda path: True)

        result = volumes_module.classify_volume('/')

        assert result['kind'] == 'system'
        assert result['scannable'] is True

    def test_mounted_disk_image_is_not_scannable(self):
        result = volumes_module.classify_volume(
            '/Volumes/Install Widget',
            fstype='hfs',
            disk_image_mounts={'/Volumes/Install Widget': '/Users/dad/Downloads/Widget.dmg'},
        )

        assert result['kind'] == 'disk_image'
        assert result['scannable'] is False
        assert 'Widget.dmg' in result['skip_reason']

    def test_disk_image_without_backing_path_still_reports_a_reason(self):
        result = volumes_module.classify_volume(
            '/Volumes/Installer', disk_image_mounts={'/Volumes/Installer': ''}
        )

        assert result['kind'] == 'disk_image'
        assert result['skip_reason'] == 'mounted disk image'

    @pytest.mark.parametrize('fstype', ['smbfs', 'afpfs', 'nfs', 'webdav'])
    def test_network_shares_are_not_scannable(self, fstype):
        result = volumes_module.classify_volume('/Volumes/NAS', fstype=fstype)

        assert result['kind'] == 'network'
        assert result['scannable'] is False

    def test_read_only_mount_is_not_scannable(self, monkeypatch):
        """Backstop for disk images when hdiutil is unavailable."""
        monkeypatch.setattr(volumes_module, 'is_read_only', lambda path: True)

        result = volumes_module.classify_volume('/Volumes/Install Widget', fstype='hfs')

        assert result['kind'] == 'read_only'
        assert result['scannable'] is False

    def test_writable_external_drive_is_scannable(self, monkeypatch):
        monkeypatch.setattr(volumes_module, 'is_read_only', lambda path: False)

        result = volumes_module.classify_volume('/Volumes/Backup', fstype='apfs')

        assert result['kind'] == 'disk'
        assert result['scannable'] is True


class TestMountParsing:
    def test_get_mount_fstypes_parses_mount_output(self, monkeypatch):
        output = (
            '/dev/disk3s1s1 on / (apfs, sealed, local, read-only, journaled)\n'
            '/dev/disk5s2 on /Volumes/Install Widget (hfs, local, nodev, read-only)\n'
            '//dad@nas._smb._tcp.local/media on /Volumes/media (smbfs, nodev, nosuid)\n'
            'garbage line without the expected shape\n'
        )

        class FakeResult:
            returncode = 0
            stdout = output

        monkeypatch.setattr(volumes_module.subprocess, 'run', lambda *a, **kw: FakeResult())

        fstypes = volumes_module.get_mount_fstypes()

        assert fstypes['/'] == 'apfs'
        assert fstypes['/Volumes/Install Widget'] == 'hfs'
        assert fstypes['/Volumes/media'] == 'smbfs'

    def test_get_mount_fstypes_survives_missing_mount_binary(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise FileNotFoundError('/sbin/mount')

        monkeypatch.setattr(volumes_module.subprocess, 'run', _boom)

        assert volumes_module.get_mount_fstypes() == {}

    def test_get_disk_image_mounts_survives_missing_hdiutil(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise FileNotFoundError('hdiutil')

        monkeypatch.setattr(volumes_module.subprocess, 'run', _boom)

        assert volumes_module.get_disk_image_mounts() == {}


class TestListVolumesFiltering:
    def _patch_environment(self, monkeypatch, entries, fstypes, disk_images, read_only=()):
        monkeypatch.setattr(volumes_module.os.path, 'exists', lambda path: path == '/Volumes')
        monkeypatch.setattr(volumes_module.os, 'listdir', lambda path: entries)
        monkeypatch.setattr(volumes_module.os.path, 'ismount', lambda path: True)
        monkeypatch.setattr(volumes_module, 'get_mount_fstypes', lambda: fstypes)
        monkeypatch.setattr(volumes_module, 'get_disk_image_mounts', lambda: disk_images)
        monkeypatch.setattr(volumes_module, 'is_read_only', lambda path: path in read_only)
        monkeypatch.setattr(
            volumes_module, 'get_volume_info',
            lambda path: {
                'path': path, 'total_bytes': 0, 'used_bytes': 0, 'free_bytes': 0,
                'used_percent': 50.0, 'total_human': '100.0 GB',
                'used_human': '50.0 GB', 'free_human': '50.0 GB',
            }
        )

    def test_disk_image_is_excluded_by_default(self, monkeypatch):
        self._patch_environment(
            monkeypatch,
            entries=['Install Widget', 'Backup'],
            fstypes={'/': 'apfs', '/Volumes/Install Widget': 'hfs', '/Volumes/Backup': 'apfs'},
            disk_images={'/Volumes/Install Widget': '/Users/dad/Downloads/Widget.dmg'},
            read_only=('/Volumes/Install Widget',),
        )

        paths = [v['path'] for v in volumes_module.list_volumes()]

        assert paths == ['/', '/Volumes/Backup']

    def test_include_all_keeps_everything_and_labels_it(self, monkeypatch):
        self._patch_environment(
            monkeypatch,
            entries=['Install Widget'],
            fstypes={'/': 'apfs', '/Volumes/Install Widget': 'hfs'},
            disk_images={'/Volumes/Install Widget': '/Users/dad/Downloads/Widget.dmg'},
            read_only=('/Volumes/Install Widget',),
        )

        volumes = volumes_module.list_volumes(include_all=True)

        assert [v['path'] for v in volumes] == ['/', '/Volumes/Install Widget']
        assert [v['index'] for v in volumes] == [1, 2]
        assert volumes[1]['kind'] == 'disk_image'
        assert volumes[1]['scannable'] is False


class TestSelectVolumeFiltering:
    def test_hidden_volumes_are_reported_not_offered(self, monkeypatch, capsys):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_hidden_volume(2, 'Install Widget', '/Volumes/Install Widget',
                                'disk_image', 'mounted disk image (Widget.dmg)'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=True))
        monkeypatch.setattr(builtins, 'input', _refuse_input)

        result = select_volume()

        # Only the real drive is left, so it is auto-selected without a prompt.
        assert result == '/'
        out = capsys.readouterr().out
        assert 'Not shown' in out
        assert 'Widget.dmg' in out
        assert '--all-volumes' in out

    def test_include_all_offers_the_disk_image(self, monkeypatch, capsys):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_hidden_volume(2, 'Install Widget', '/Volumes/Install Widget',
                                'disk_image', 'mounted disk image (Widget.dmg)'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('2\n', tty=True))

        result = select_volume(include_all=True)

        assert result == '/Volumes/Install Widget'
        assert 'mounted disk image' in capsys.readouterr().out

    def test_menu_indexes_are_contiguous_after_filtering(self, monkeypatch):
        vols = [
            _make_volume(1, 'Macintosh HD', '/'),
            _make_hidden_volume(2, 'Install Widget', '/Volumes/Install Widget',
                                'disk_image', 'mounted disk image'),
            _make_volume(3, 'Backup', '/Volumes/Backup'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin('2\n', tty=True))

        # "2" must mean Backup — the second *offered* volume, not the third entry.
        assert select_volume() == '/Volumes/Backup'

    def test_explicit_path_to_a_disk_image_still_scans_with_a_note(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(
            volumes_module, 'get_volume_info',
            lambda path: {'total_human': '1.0 GB', 'used_human': '0.5 GB', 'used_percent': 50.0}
        )
        monkeypatch.setattr(volumes_module, 'get_mount_fstypes', dict)
        monkeypatch.setattr(
            volumes_module, 'get_disk_image_mounts',
            lambda: {str(tmp_path): '/Users/dad/Downloads/Widget.dmg'}
        )

        result = select_volume(str(tmp_path))

        assert result == str(tmp_path)
        assert 'Scanning it anyway' in capsys.readouterr().out

    def test_all_volumes_filtered_out_falls_back_to_showing_them(self, monkeypatch, capsys):
        vols = [
            _make_hidden_volume(1, 'Install Widget', '/Volumes/Install Widget',
                                'disk_image', 'mounted disk image'),
        ]
        monkeypatch.setattr(volumes_module, 'list_volumes', lambda **kwargs: vols)
        monkeypatch.setattr(sys, 'stdin', FakeStdin(tty=True))

        result = select_volume()

        assert result == '/Volumes/Install Widget'
        assert 'showing all mounted volumes' in capsys.readouterr().out
