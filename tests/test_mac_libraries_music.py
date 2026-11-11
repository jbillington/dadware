"""Music library scan must not count ~/Music/Music inside ~/Music twice."""
import os

import pytest

from scanners import mac_libraries

pytestmark = pytest.mark.unit


def test_nested_music_folders_are_not_double_counted(tmp_path, monkeypatch):
    music = tmp_path / 'Music'
    (music / 'Music').mkdir(parents=True)
    (music / 'Music' / 'a.m4a').write_bytes(b'x' * 8192)
    (music / 'loose.wav').write_bytes(b'x' * 8192)
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
    seen = []
    real = mac_libraries.get_folder_size

    def spy(path, *a, **k):
        seen.append(path)
        return real(path, *a, **k)

    monkeypatch.setattr(mac_libraries, 'get_folder_size', spy)
    result = mac_libraries.scan_music_library()
    assert seen == [str(music)]
    assert result['count'] == 1
