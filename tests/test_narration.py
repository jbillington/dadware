"""say() prints one narrated line and pauses only for a person at a terminal."""
import pytest

from utils import narration

pytestmark = pytest.mark.unit


class _FakeStdout:
    def __init__(self, tty):
        self._tty = tty
        self.text = ''

    def isatty(self):
        return self._tty

    def write(self, s):
        self.text += s

    def flush(self):
        pass


def _run(monkeypatch, tty, **kwargs):
    out = _FakeStdout(tty)
    sleeps = []
    monkeypatch.setattr(narration.sys, 'stdout', out)
    monkeypatch.setattr(narration.time, 'sleep', sleeps.append)
    narration.say('hello', **kwargs)
    return out.text, sleeps


def test_pause_is_two_tenths_of_a_second():
    assert narration.PAUSE_SECONDS == 0.2


def test_arrow_line_and_pause_on_a_terminal(monkeypatch):
    text, sleeps = _run(monkeypatch, tty=True)
    assert text == '→ hello\n'
    assert sleeps == [0.2]


def test_no_pause_when_output_is_not_a_terminal(monkeypatch):
    text, sleeps = _run(monkeypatch, tty=False)
    assert text == '→ hello\n'
    assert sleeps == []


def test_follow_on_line_is_indented_without_an_arrow(monkeypatch):
    text, _ = _run(monkeypatch, tty=False, arrow=False)
    assert text == '     hello\n'
