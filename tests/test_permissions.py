"""Tests for the Phase 1 permission UX (PERMISSIONS-PLAN.md).

Covers per-folder TCC detection, prompt choreography, the FDA deep-link
offer's non-interactive guarantees, and the honest-denial copy in both
renderers. TCC itself only exists on macOS, so denial is exercised here
with mocked errno — the real dialogs are covered by the plan's manual
`tccutil reset` test matrix.
"""

import errno
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from utils import permissions
from utils.permissions import (
    AUTO_PROMPT_FOLDERS,
    FDA_SETTINGS_URL,
    format_permission_status,
    check_folder_access,
    choreograph_permission_prompts,
    offer_full_disk_access_settings,
)
from renderers.html import render_permission_warning
from renderers.terminal import render_terminal

pytestmark = pytest.mark.unit


class TestCheckFolderAccess:
    def test_readable_folder_is_granted(self, tmp_path):
        assert check_folder_access(str(tmp_path))['status'] == 'granted'

    def test_missing_folder_is_not_found(self, tmp_path):
        result = check_folder_access(str(tmp_path / 'no-such-folder'))
        assert result['status'] == 'not_found'

    def test_eperm_is_a_tcc_denial(self, monkeypatch):
        # macOS TCC blocks a folder the user owns with EPERM
        # ("Operation not permitted"), not the ordinary EACCES.
        def raise_eperm(path):
            raise PermissionError(errno.EPERM, 'Operation not permitted', path)
        monkeypatch.setattr(os, 'listdir', raise_eperm)

        result = check_folder_access('/Users/dad/Desktop')
        assert result['status'] == 'denied'
        assert result['reason'] == 'tcc'

    def test_eacces_is_a_posix_denial(self, monkeypatch):
        def raise_eacces(path):
            raise PermissionError(errno.EACCES, 'Permission denied', path)
        monkeypatch.setattr(os, 'listdir', raise_eacces)

        result = check_folder_access('/root/private')
        assert result['status'] == 'denied'
        assert result['reason'] == 'posix'

    def test_other_oserror_is_an_error_not_a_denial(self, monkeypatch):
        def raise_eio(path):
            raise OSError(errno.EIO, 'Input/output error', path)
        monkeypatch.setattr(os, 'listdir', raise_eio)

        assert check_folder_access('/broken')['status'] == 'error'


class TestChoreography:
    def test_folders_are_touched_in_fixed_order(self, monkeypatch):
        touched = []

        def record(path):
            touched.append(os.path.basename(path))
            return {'status': 'granted', 'path': path}

        monkeypatch.setattr(permissions, 'check_folder_access', record)
        result = choreograph_permission_prompts()

        assert touched == list(AUTO_PROMPT_FOLDERS)
        assert set(result) == set(AUTO_PROMPT_FOLDERS)

    def test_results_carry_each_folder_status(self, monkeypatch):
        monkeypatch.setattr(
            permissions, 'check_folder_access',
            lambda path: {'status': 'denied', 'path': path, 'reason': 'tcc'})

        result = choreograph_permission_prompts()
        assert all(info['status'] == 'denied' for info in result.values())


class _FakeTty:
    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        return self._tty


class TestOfferFullDiskAccessSettings:
    """The offer must never block a scheduled or app-mode run."""

    def test_without_a_tty_input_is_never_called(self, monkeypatch):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(False))

        def forbidden(prompt):
            raise AssertionError('input() must not be called without a TTY')

        assert offer_full_disk_access_settings(input_func=forbidden) is False

    def test_default_answer_is_no(self, monkeypatch):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))
        opened = []
        monkeypatch.setattr(permissions, 'open_full_disk_access_settings',
                            lambda: opened.append(True) or True)

        assert offer_full_disk_access_settings(input_func=lambda p: '') is False
        assert opened == []

    def test_yes_opens_the_pane(self, monkeypatch):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))
        monkeypatch.setattr(permissions, 'open_full_disk_access_settings',
                            lambda: True)

        assert offer_full_disk_access_settings(input_func=lambda p: 'y') is True

    def test_eof_means_no(self, monkeypatch):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))

        def raise_eof(prompt):
            raise EOFError

        assert offer_full_disk_access_settings(input_func=raise_eof) is False


class TestFirstRunGating:
    """The explainer must not promise dialogs that macOS will never show.

    Found on a real Mac Aug 28, 2026: Terminal already had Full Disk Access,
    so the scan announced permission pop-ups, showed none, and then reported
    thousands of "skipped due to permissions" items. Nothing was broken; the
    copy just described a machine the user wasn't on.
    """

    def test_marker_absent_means_first_introduction(self, monkeypatch, tmp_path):
        monkeypatch.setattr(permissions, '_INTRODUCED_MARKER',
                            str(tmp_path / '.permissions-introduced'))
        assert permissions.permissions_introduced() is False

    def test_marker_is_written_and_then_detected(self, monkeypatch, tmp_path):
        monkeypatch.setattr(permissions, '_STATE_DIR', str(tmp_path / 'state'))
        monkeypatch.setattr(permissions, '_INTRODUCED_MARKER',
                            str(tmp_path / 'state' / '.permissions-introduced'))

        assert permissions.permissions_introduced() is False
        assert permissions.mark_permissions_introduced() is True
        assert permissions.permissions_introduced() is True

    def test_marking_survives_an_unwritable_home(self, monkeypatch, tmp_path):
        # A read-only home must not crash the scan - the marker is a
        # convenience, not a requirement.
        unwritable = tmp_path / 'nope'
        unwritable.write_text('I am a file, not a directory')
        monkeypatch.setattr(permissions, '_STATE_DIR', str(unwritable))
        monkeypatch.setattr(permissions, '_INTRODUCED_MARKER',
                            str(unwritable / '.permissions-introduced'))

        assert permissions.mark_permissions_introduced() is False


def _storage_scan(permission_status):
    return {
        'scan_type': 'storage',
        'volume': '/',
        'volume_info': {
            'total_human': '500.0 GB',
            'used_human': '250.0 GB',
            'free_human': '250.0 GB',
            'used_percent': 50,
        },
        'top_folders': [],
        'top_files': [],
        'permission_status': permission_status,
    }


_DENIED_FOLDERS = {
    'Desktop': {'status': 'denied', 'path': '/Users/dad/Desktop', 'reason': 'tcc'},
    'Documents': {'status': 'granted', 'path': '/Users/dad/Documents'},
    'Downloads': {'status': 'denied', 'path': '/Users/dad/Downloads', 'reason': 'tcc'},
}


class TestHtmlHonestDenialCopy:
    def test_denied_folders_get_copy_and_fix_path(self):
        html = render_permission_warning(_storage_scan(
            {'has_access': True, 'missing_permissions': [], 'folders': _DENIED_FOLDERS}))

        assert 'Desktop' in html and 'Downloads' in html
        assert 'Files &amp; Folders' in html
        # The granted folder is not reported as a problem.
        assert 'Documents' not in html

    def test_fda_block_carries_the_deep_link(self):
        html = render_permission_warning(_storage_scan(
            {'has_access': False, 'missing_permissions': ['messages']}))

        assert FDA_SETTINGS_URL in html
        assert 'Messages' in html
        assert 'never counted as zero' in html

    def test_silent_when_everything_was_granted(self):
        html = render_permission_warning(_storage_scan(
            {'has_access': True, 'missing_permissions': [],
             'folders': {'Desktop': {'status': 'granted', 'path': '/Users/dad/Desktop'}}}))

        assert html == ''

    def test_old_scan_data_without_folder_info_still_renders(self):
        # Reports saved before Phase 1 carry no 'folders' key.
        html = render_permission_warning(_storage_scan(
            {'has_access': False, 'missing_permissions': ['mail']}))

        assert 'Mail' in html


class TestTerminalHonestDenialCopy:
    def test_denied_folders_get_copy_and_fix_path(self):
        scan = _storage_scan(
            {'has_access': True, 'missing_permissions': [], 'folders': _DENIED_FOLDERS})
        output = render_terminal(scan, {'status': 'ok', 'comments': [], 'tips': []},
                                 use_color=False)

        assert "Folders I couldn't check" in output
        assert 'Desktop, Downloads' in output
        assert 'Files & Folders' in output

    def test_fda_block_states_the_gap_without_repeating_the_how_to(self):
        # The steps live in the end-of-run hand-off now: a grant cannot
        # change the run in progress, and printing them twice made the
        # report noisier for no gain.
        scan = _storage_scan({'has_access': False, 'missing_permissions': ['messages']})
        output = render_terminal(scan, {'status': 'ok', 'comments': [], 'tips': []},
                                 use_color=False)

        assert 'Messages' in output
        assert 'left blank' in output
        assert FDA_SETTINGS_URL not in output
        assert 'GRANT-PERMISSIONS.md' not in output


class TestFdaOfferCopy:
    """The offer must not imply it changes the report in hand.

    Aug 28 real-Mac run: the prompt appeared mid-scan, saying only "Open
    System Settings -> Full Disk Access now?". Answering yes opened the
    pane and the scan carried straight on, so the click looked like it had
    done nothing - and it could not have: macOS binds Full Disk Access at
    process start, so no toggle can affect a run already in flight.
    """

    def test_prompt_says_the_report_is_already_finished(self, monkeypatch):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))
        asked = []

        def record(prompt):
            asked.append(prompt)
            return 'n'

        offer_full_disk_access_settings(input_func=record)
        assert 'already' in asked[0].lower()
        assert '[y/N]' in asked[0]

    def test_yes_explains_the_restart_and_rerun(self, monkeypatch, capsys):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))
        monkeypatch.setattr(permissions, 'open_full_disk_access_settings', lambda: True)

        offer_full_disk_access_settings(input_func=lambda p: 'y')
        out = capsys.readouterr().out
        assert 'quit Terminal' in out
        assert 'run the scan again' in out

    def test_failure_to_open_still_gives_the_manual_route(self, monkeypatch, capsys):
        monkeypatch.setattr(permissions.sys, 'stdin', _FakeTty(True))
        monkeypatch.setattr(permissions, 'open_full_disk_access_settings', lambda: False)

        assert offer_full_disk_access_settings(input_func=lambda p: 'y') is False
        assert 'Privacy & Security' in capsys.readouterr().out


class TestPermissionStatusScope:
    """The status line named two libraries as if that were everything Full
    Disk Access covers. It is only the subset this scan probes."""

    def test_blocked_line_admits_what_it_leaves_out(self):
        line = format_permission_status(
            {'has_access': False, 'missing_permissions': ['messages', 'mail']})

        assert 'Messages, Mail' in line
        assert 'Trash' in line

    def test_single_library_reads_the_same_way(self):
        line = format_permission_status(
            {'has_access': False, 'missing_permissions': ['mail']})

        assert 'Mail' in line
        assert 'Trash' in line

    def test_granted_line_is_unambiguous(self):
        line = format_permission_status({'has_access': True, 'missing_permissions': []})
        assert 'on' in line.lower()


class TestAllGrantedLineScope:
    def test_it_names_only_the_folders_it_checked(self):
        # An unqualified all-clear contradicted the Full Disk Access notice
        # printed moments later in the same run.
        for folder in AUTO_PROMPT_FOLDERS:
            assert folder in permissions.ALL_GRANTED_LINE
        assert 'everything' not in permissions.ALL_GRANTED_LINE.lower()


class TestPhotosProbe:
    """The bundle directory lists fine without Full Disk Access; only its
    internals are protected. The probe has to read one of those, and must not
    swallow the denial - on the Aug 28 2026 run with the setting off, Photos
    still reported as readable.
    """

    @pytest.fixture
    def photos_library(self, tmp_path, monkeypatch):
        library = tmp_path / 'Pictures' / 'Photos Library.photoslibrary'
        library.mkdir(parents=True)
        monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
        return library

    def test_missing_library_is_not_a_permission_problem(self, tmp_path, monkeypatch):
        monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
        assert permissions.check_photos_access() == {
            'has_access': False, 'reason': 'path_not_found'}

    def test_readable_internals_mean_access(self, photos_library):
        (photos_library / 'database').mkdir()

        assert permissions.check_photos_access()['has_access'] is True

    def test_denied_internals_are_reported_not_swallowed(self, photos_library, monkeypatch):
        (photos_library / 'database').mkdir()
        denied = str(photos_library / 'database')
        real_listdir = os.listdir

        def fake_listdir(path):
            if str(path) == denied:
                raise PermissionError(errno.EACCES, 'Operation not permitted')
            return real_listdir(path)

        monkeypatch.setattr(os, 'listdir', fake_listdir)

        assert permissions.check_photos_access() == {
            'has_access': False, 'reason': 'permission_denied'}

    def test_loose_files_in_the_bundle_are_not_a_verdict(self, photos_library, monkeypatch):
        """A readable file next to a denied folder must not read as access."""
        (photos_library / 'Photos.sqlite').write_bytes(b'x')
        (photos_library / 'originals').mkdir()
        denied = str(photos_library / 'originals')
        real_listdir = os.listdir

        def fake_listdir(path):
            if str(path) == denied:
                raise PermissionError(errno.EACCES, 'Operation not permitted')
            return real_listdir(path)

        monkeypatch.setattr(os, 'listdir', fake_listdir)

        assert permissions.check_photos_access()['has_access'] is False

    def test_empty_bundle_does_not_raise_a_false_alarm(self, photos_library):
        """Nothing inside means nothing Full Disk Access would unlock."""
        result = permissions.check_photos_access()

        assert result == {'has_access': True, 'reason': 'empty_library'}
