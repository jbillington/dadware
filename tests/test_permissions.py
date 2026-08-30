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

    def test_fda_block_carries_the_deep_link_command(self):
        scan = _storage_scan({'has_access': False, 'missing_permissions': ['messages']})
        output = render_terminal(scan, {'status': 'ok', 'comments': [], 'tips': []},
                                 use_color=False)

        assert FDA_SETTINGS_URL in output
        assert 'GRANT-PERMISSIONS.md' not in output
