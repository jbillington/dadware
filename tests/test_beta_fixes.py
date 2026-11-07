"""Regression tests for the fixes made after the first signed-beta report review."""

import pytest

from utils import system_info
from renderers import html as html_renderer

pytestmark = pytest.mark.unit


def test_architecture_is_machine_not_i386(monkeypatch):
    monkeypatch.setattr(system_info.platform, 'processor', lambda: 'i386')
    monkeypatch.setattr(system_info.platform, 'machine', lambda: 'x86_64')
    monkeypatch.setattr(system_info, 'run_command', lambda cmd: None)
    assert system_info.get_cpu_info()['architecture'] == 'x86_64'


def test_storage_capacity_listed_once_for_system_and_data_volumes(monkeypatch):
    profile = "Macintosh HD:\n  Capacity: 250.69 GB (250,685,575,168 bytes)\n" \
              "Macintosh HD - Data:\n  Capacity: 250.69 GB (250,685,575,168 bytes)\n"
    monkeypatch.setattr(system_info, 'run_command', lambda cmd: profile)
    assert len(system_info.get_storage_info()['drives']) == 1


def test_library_advice_covers_every_graded_library():
    for key in ('messages', 'photos', 'mail', 'music'):
        text = html_renderer.LIBRARY_ADVICE[key]
        assert text and 'delete' not in text.lower()
