"""
The feedback invitation and the storage/CPU cross-promo.

Plan: docs/roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md. One module holds the
copy (utils/promo.py); the CLI prints it at the end of a run for a person at a
terminal, and the HTML report carries it in the footer and a small card.
"""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import askdad
from utils import promo
from utils.version import VERSION
from renderers.html import render_html

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
from tests.test_html_render import FIXED_SYSTEM_INFO

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# utils/promo.py
# ---------------------------------------------------------------------------

class TestCopy:
    def test_feedback_line_carries_the_address(self):
        assert promo.FEEDBACK_EMAIL == "john@dadware.net"
        assert promo.feedback_line().endswith("\njohn@dadware.net")

    def test_mailto_carries_the_version_and_nothing_else(self):
        # The full href, so nothing (scan data, paths) can ride along unseen.
        version = VERSION.replace(" ", "%20")
        assert promo.feedback_mailto() == (
            f"mailto:john@dadware.net?subject=Ask%20Dad%20feedback%20%28v{version}%29")

    def test_storage_points_at_cpu_and_cpu_points_at_storage(self, monkeypatch):
        monkeypatch.delenv(promo.CHANNEL_ENV, raising=False)
        assert promo.cpu_promo_line("storage") == (
            "Next - Ask Dad to scan your memory and CPU.  Run:  askdad cpu")
        assert promo.cpu_promo_line("cpu") == (
            "Curious about your storage?  Run:  askdad")
        assert promo.cpu_promo_line("other") is None

    def test_app_channel_says_this_terminal_window(self, monkeypatch):
        monkeypatch.setenv(promo.CHANNEL_ENV, "app")
        line = promo.cpu_promo_line("storage")
        assert "Type in this Terminal window:  askdad cpu" in line


# ---------------------------------------------------------------------------
# CLI: the [y/N] question and the closing lines
# ---------------------------------------------------------------------------

class FakeStream(io.StringIO):
    def __init__(self, tty):
        super().__init__()
        self._tty = tty

    def isatty(self):
        return self._tty


def _args(**overrides):
    values = dict(terminal=False, no_color=True, skip_protected=False,
                  export_memory=None, test_reports=False)
    values.update(overrides)
    return type("Args", (), values)()


class TestAskToRunCpuScan:
    @pytest.mark.parametrize("answer,expected", [
        ("y", True), ("Y", True), ("yes", True),
        ("n", False), ("", False), ("maybe", False),
    ])
    def test_answers(self, monkeypatch, answer, expected):
        monkeypatch.setattr(askdad.sys, "stdin", FakeStream(tty=True))
        monkeypatch.setattr("builtins.input", lambda prompt: answer)
        assert askdad.ask_to_run_cpu_scan() is expected

    @pytest.mark.parametrize("exc", [EOFError, KeyboardInterrupt])
    def test_eof_and_ctrl_c_mean_no(self, monkeypatch, exc):
        def raise_it(prompt):
            raise exc
        monkeypatch.setattr(askdad.sys, "stdin", FakeStream(tty=True))
        monkeypatch.setattr("builtins.input", raise_it)
        assert askdad.ask_to_run_cpu_scan() is False

    def test_no_question_without_a_tty(self, monkeypatch):
        def must_not_ask(prompt):
            raise AssertionError("asked without a TTY")
        monkeypatch.setattr(askdad.sys, "stdin", FakeStream(tty=False))
        monkeypatch.setattr("builtins.input", must_not_ask)
        assert askdad.ask_to_run_cpu_scan() is False


class TestClosingLines:
    def test_storage_run_ends_with_cpu_promo_then_feedback(self, monkeypatch):
        monkeypatch.delenv(promo.CHANNEL_ENV, raising=False)
        out = FakeStream(tty=True)
        monkeypatch.setattr(askdad.sys, "stdout", out)
        askdad.print_closing_lines(_args(), "storage")
        text = out.getvalue()
        assert text.index("askdad cpu") < text.index("john@dadware.net")
        assert text.rstrip().endswith("john@dadware.net")

    def test_both_scans_ran_feedback_only(self, monkeypatch):
        out = FakeStream(tty=True)
        monkeypatch.setattr(askdad.sys, "stdout", out)
        askdad.print_closing_lines(_args())
        assert "askdad" not in out.getvalue().replace("Ask Dad", "")
        assert "john@dadware.net" in out.getvalue()

    @pytest.mark.parametrize("terminal,tty", [(True, True), (False, False)])
    def test_terminal_flag_and_non_tty_print_nothing(self, monkeypatch, terminal, tty):
        out = FakeStream(tty=tty)
        monkeypatch.setattr(askdad.sys, "stdout", out)
        askdad.print_closing_lines(_args(terminal=terminal), "storage")
        assert out.getvalue() == ""


class TestStorageRunEnd:
    """Drive main() for a storage run with the scanners stubbed out."""

    def _stub(self, monkeypatch, answer, scan_scope="home_volume"):
        calls = {"cpu": 0, "saved": []}

        def fake_cpu(args):
            calls["cpu"] += 1
            return {"scan_type": "cpu"}

        monkeypatch.setattr(askdad, "run_storage_scan",
                            lambda args: {"scan_type": "storage", "scan_scope": scan_scope})
        monkeypatch.setattr(askdad, "run_cpu_scan", fake_cpu)
        monkeypatch.setattr(askdad, "add_personality", lambda scan_data: {"comments": []})
        monkeypatch.setattr(askdad, "render_terminal", lambda *a: "")
        monkeypatch.setattr(askdad, "save_and_open_report",
                            lambda scan_data, pd, prefix, args, **k: calls["saved"].append(prefix))
        monkeypatch.setattr(askdad.sys, "stdin", FakeStream(tty=True))
        monkeypatch.setattr(askdad.sys, "stdout", FakeStream(tty=True))
        monkeypatch.setattr("builtins.input", lambda prompt: answer)
        monkeypatch.setattr(sys, "argv", ["askdad.py"])
        monkeypatch.delenv(promo.CHANNEL_ENV, raising=False)
        return calls

    def test_yes_runs_and_saves_the_cpu_report(self, monkeypatch):
        calls = self._stub(monkeypatch, "y")
        assert askdad.main() == 0
        assert calls["cpu"] == 1
        assert calls["saved"] == ["storage", "cpu"]
        out = askdad.sys.stdout.getvalue()
        assert "Run:  askdad cpu" not in out  # it just ran
        assert "john@dadware.net" in out

    def test_no_leaves_the_hint_for_later(self, monkeypatch):
        calls = self._stub(monkeypatch, "n")
        assert askdad.main() == 0
        assert calls["cpu"] == 0
        assert calls["saved"] == ["storage"]
        assert "Run:  askdad cpu" in askdad.sys.stdout.getvalue()

    def test_drive_report_neither_asks_nor_promotes(self, monkeypatch):
        calls = self._stub(monkeypatch, "y", scan_scope="other_volume")
        assert askdad.main() == 0
        assert calls["cpu"] == 0
        out = askdad.sys.stdout.getvalue()
        assert "askdad cpu" not in out
        assert "john@dadware.net" in out


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

def _load(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["scan_data"], data["personality_data"]


def _render(monkeypatch, tmp_path, scan_data, personality_data):
    monkeypatch.setattr("renderers.html.get_system_info", lambda: FIXED_SYSTEM_INFO)
    path = tmp_path / "report.html"
    render_html(scan_data, personality_data, str(path))
    return path.read_text(encoding="utf-8")


class TestReport:
    def test_storage_report_has_cpu_card_and_feedback(self, monkeypatch, tmp_path):
        html = _render(monkeypatch, tmp_path, *_load("storage_scan.json"))
        assert 'id="other-scan"' in html
        assert 'value="askdad cpu"' in html
        assert f'href="{promo.feedback_mailto()}"' in html
        assert ">john@dadware.net</a>" in html

    def test_cpu_report_has_storage_card_and_feedback(self, monkeypatch, tmp_path):
        html = _render(monkeypatch, tmp_path, *_load("cpu_scan.json"))
        assert 'value="askdad"' in html
        assert "Your Mac has a storage report too." in html
        assert ">john@dadware.net</a>" in html

    def test_drive_report_has_feedback_but_no_card(self, monkeypatch, tmp_path):
        scan_data, personality_data = _load("storage_scan.json")
        scan_data["scan_scope"] = "other_volume"
        html = _render(monkeypatch, tmp_path, scan_data, personality_data)
        assert 'id="other-scan"' not in html
        assert ">john@dadware.net</a>" in html

    def test_changing_the_address_changes_both_outputs(self, monkeypatch, tmp_path):
        monkeypatch.setattr(promo, "FEEDBACK_EMAIL", "someone@example.test")
        assert promo.feedback_line().endswith("someone@example.test")
        html = _render(monkeypatch, tmp_path, *_load("storage_scan.json"))
        assert "mailto:someone@example.test?" in html
        assert "john@dadware.net" not in html


# ---------------------------------------------------------------------------
# make_app.sh: the bundled binary goes on the window's PATH
# ---------------------------------------------------------------------------

def _command_script():
    """The AskDad.command heredoc, extracted from make_app.sh."""
    text = (PROJECT_ROOT / "make_app.sh").read_text()
    start = text.index("<<'CMD'\n") + len("<<'CMD'\n")
    return text[start:text.index("\nCMD\n", start)] + "\n"


def test_app_command_script_puts_its_folder_on_path(tmp_path):
    # A folder with a space in it, as in "Ask Dad.app".
    resources = tmp_path / "Ask Dad.app" / "Contents" / "Resources"
    resources.mkdir(parents=True)
    (resources / "askdad").write_text("#!/bin/bash\necho \"ran:$ASKDAD_CHANNEL\"\n")
    (resources / "askdad").chmod(0o755)
    script = _command_script()
    # Stand-in for the final interactive shell: report what it would find.
    script = script.replace('exec "${SHELL:-/bin/zsh}" -l',
                            'command -v askdad; askdad')
    script = script.replace("clear\n", "", 1)
    command = resources / "AskDad.command"
    command.write_text(script)
    command.chmod(0o755)

    env = {k: v for k, v in os.environ.items() if k != promo.CHANNEL_ENV}
    env["PATH"] = "/usr/bin:/bin"
    result = subprocess.run([str(command)], capture_output=True, text=True,
                            env=env, timeout=10)
    assert result.returncode == 0, result.stderr
    assert str(resources / "askdad") in result.stdout
    assert result.stdout.count("ran:app") == 2
