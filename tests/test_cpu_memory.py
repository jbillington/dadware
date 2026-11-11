"""Memory pressure, the shared RAM figures, and CPU prompt privacy.

Covers the Nov 2026 CPU report fixes (docs/roadmap/CPU-REPORT-FIXES-PLAN.md,
items A1-A8): pressure comes from the kernel, never from the lifetime swap
counter; free/available print the same in every report; the AI prompt
carries no command lines.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.cpu as cpu
from personality.dad import add_personality
from renderers.html import render_html
from renderers.terminal import render_terminal
from utils.llm_prompt import generate_cpu_prompt
from utils.memory import memory_summary

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).parent / "fixtures" / "cpu_scan.json"

VM_STAT_OUTPUT = """Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                               65403.
Pages active:                           1425996.
Pages inactive:                         1417598.
Pages speculative:                         8064.
Pages wired down:                        973471.
Pages purgeable:                         190391.
Pages occupied by compressor:            303556.
Swapins:                                9999999.
Swapouts:                              27414000.
"""


def fake_run(pressure_stdout="1\n", pressure_rc=0, pressure_exc=None,
             swap_stdout="total = 1024.00M  used = 308.25M  free = 715.75M  (encrypted)\n"):
    """A subprocess.run stand-in answering vm_stat and the two sysctls."""
    def run(cmd, **kwargs):
        if cmd == ['vm_stat']:
            return SimpleNamespace(returncode=0, stdout=VM_STAT_OUTPUT, stderr='')
        if cmd[-1] == 'kern.memorystatus_vm_pressure_level':
            if pressure_exc:
                raise pressure_exc
            return SimpleNamespace(returncode=pressure_rc, stdout=pressure_stdout, stderr='')
        if cmd[-1] == 'vm.swapusage':
            return SimpleNamespace(returncode=0, stdout=swap_stdout, stderr='')
        raise AssertionError(f"unexpected command {cmd}")
    return run


class TestKernelPressureLevel:
    @pytest.mark.parametrize("stdout, expected", [
        ("1\n", 'low'),
        ("2\n", 'medium'),
        ("4\n", 'high'),
        ("0\n", 'unknown'),
        ("3\n", 'unknown'),
        ("not a number\n", 'unknown'),
        ("", 'unknown'),
    ])
    def test_maps_kernel_level(self, monkeypatch, stdout, expected):
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run(pressure_stdout=stdout))
        result = cpu.get_kernel_pressure_level()
        assert result['pressure'] == expected
        if expected == 'unknown':
            assert result['pressure_source'] == 'unavailable'
        else:
            assert result['pressure_source'] == cpu.PRESSURE_SOURCE

    def test_nonzero_exit_is_unknown_not_high(self, monkeypatch):
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run(pressure_rc=1))
        assert cpu.get_kernel_pressure_level()['pressure'] == 'unknown'

    @pytest.mark.parametrize("exc", [
        FileNotFoundError("sysctl"),
        subprocess.TimeoutExpired(cmd='sysctl', timeout=2),
    ])
    def test_failing_sysctl_is_unknown_not_high(self, monkeypatch, exc):
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run(pressure_exc=exc))
        assert cpu.get_kernel_pressure_level()['pressure'] == 'unknown'


class TestMemoryPressureScan:
    def test_huge_swapouts_with_normal_kernel_pressure_is_low(self, monkeypatch):
        """Regression: Swapouts is a counter since boot. 27 million of them
        with the kernel saying normal used to read 'high' ("memory's maxed
        out") on almost every Mac."""
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run(pressure_stdout="1\n"))
        result = cpu.get_memory_pressure()
        assert result['swapouts'] == 27414000
        assert result['pressure'] == 'low'
        assert result['pressure_source'] == cpu.PRESSURE_SOURCE

    def test_failed_pressure_read_never_reports_high(self, monkeypatch):
        monkeypatch.setattr(cpu.subprocess, 'run',
                            fake_run(pressure_exc=OSError("no sysctl")))
        result = cpu.get_memory_pressure()
        assert result['pressure'] == 'unknown'
        assert result['pressure_source'] == 'unavailable'

    def test_free_available_used_definitions(self, monkeypatch):
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run())
        result = cpu.get_memory_pressure()
        page = 4096
        assert result['free_bytes'] == 65403 * page
        assert result['available_bytes'] == (65403 + 1417598 + 190391) * page
        assert result['used_bytes'] == (1425996 + 973471 + 303556) * page

    @pytest.mark.parametrize("stdout, expected", [
        ("total = 1024.00M  used = 308.25M  free = 715.75M  (encrypted)\n",
         int(308.25 * 1024 ** 2)),
        ("total = 4096.00M  used = 1.50G  free = 2.50G  (encrypted)\n",
         int(1.5 * 1024 ** 3)),
        ("total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)\n", 0),
        ("garbage\n", None),
    ])
    def test_swap_used_is_current_usage(self, monkeypatch, stdout, expected):
        monkeypatch.setattr(cpu.subprocess, 'run', fake_run(swap_stdout=stdout))
        assert cpu.get_swap_used_bytes() == expected


def _fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data["scan_data"], data["personality_data"]


def _render_html(scan_data, personality_data, tmp_path, monkeypatch):
    import renderers.html as html_module
    monkeypatch.setattr(html_module, 'get_system_info', lambda: {})
    out = tmp_path / "report.html"
    render_html(scan_data, personality_data, str(out))
    return out.read_text(encoding="utf-8")


class TestOneDefinitionOfFree:
    def test_html_terminal_and_prompt_agree(self, tmp_path, monkeypatch):
        scan_data, personality_data = _fixture()
        mem = memory_summary(scan_data)
        # The fixture's numbers, so a change in the definition shows up here.
        assert mem['free_text'] == "1.0 GB"
        assert mem['available_text'] == "3.0 GB"
        assert mem['used_text'] == "13.0 GB"

        terminal = render_terminal(scan_data, personality_data)
        html = _render_html(scan_data, personality_data, tmp_path, monkeypatch)
        prompt = generate_cpu_prompt(scan_data, personality_data, {})

        for output in (terminal, html, prompt):
            assert f"Free (not used at all): {mem['free_text']}" in output or \
                f"Free: {mem['free_text']}" in output
            assert mem['available_text'] in output
            assert mem['apps_text'] in output

        assert f"Available ({'approx.: free + inactive + purgeable'}): 3.0 GB" in prompt
        assert "Available: 3.0 GB" in terminal
        assert ">Available <span" in html and ">3.0 GB</div>" in html

    def test_total_minus_app_sum_is_never_printed_as_free(self, tmp_path, monkeypatch):
        """The old 'Free' was total RAM minus summed RSS (16.0 - 13.5)."""
        scan_data, personality_data = _fixture()
        html = _render_html(scan_data, personality_data, tmp_path, monkeypatch)
        terminal = render_terminal(scan_data, personality_data)
        assert "2.5 GB" not in html
        assert "2.5 GB" not in terminal
        assert ">Free</div>" not in html


class TestCpuPromptPrivacy:
    def test_prompt_has_no_command_lines_or_home_paths(self):
        scan_data, personality_data = _fixture()
        scan_data = copy.deepcopy(scan_data)
        scan_data['all_processes'].insert(0, {
            'name': 'Codex Helper',
            'cpu_percent': 1.0,
            'memory_percent': 2.0,
            'memory_mb': 900.0,
            'command': ('/Applications/Codex.app/Contents/Frameworks/Codex Helper.app/'
                        'Contents/MacOS/Codex Helper --type=renderer '
                        '--user-data-dir=/Users/someone/Library/Application Support/Codex'),
        })
        prompt = generate_cpu_prompt(scan_data, personality_data, {})
        assert "Codex Helper" in prompt  # the app name stays
        assert "--user-data-dir" not in prompt
        assert "/Users/" not in prompt
        assert "Command:" not in prompt


class TestPressureWording:
    def _scan(self, pressure, hogs=None):
        return {
            'scan_type': 'cpu',
            'top_processes': [],
            'memory_hogs': hogs or [],
            'memory_pressure': {'pressure': pressure},
            'total_memory_gb': 16,
            'total_used_gb': 15.9,  # summed RSS near 100% must not matter
            'process_metrics': {},
        }

    BIG_APPS = [
        {'name': 'Chrome', 'total_mb': 4096, 'process_count': 20},
        {'name': 'Safari', 'total_mb': 2560, 'process_count': 10},
        {'name': 'Messages', 'total_mb': 1536, 'process_count': 2},
    ]

    def test_normal_pressure_says_memory_is_fine(self):
        result = add_personality(self._scan('low', self.BIG_APPS))
        text = ' '.join(result['comments']).lower()
        tips = ' '.join(result['tips']).lower()
        assert "memory looks fine" in text
        assert "maxed" not in text
        assert result['status'] == 'ok'  # big apps alone don't make normal pressure a problem
        assert "restart" not in tips
        assert "tab" not in tips
        assert "archiv" not in tips

    def test_warn_pressure_is_busy_not_maxed(self):
        result = add_personality(self._scan('medium', self.BIG_APPS))
        text = ' '.join(result['comments']).lower()
        assert "busy" in text
        assert "maxed" not in text
        assert result['status'] == 'warn'

    def test_critical_pressure_is_maxed_out_with_recoverability_wording(self):
        result = add_personality(self._scan('high', self.BIG_APPS))
        assert any("maxed out" in c for c in result['comments'])
        assert result['status'] == 'critical'
        assert any("may free up to about 4.0 GB" in t for t in result['tips'])

    def test_unknown_pressure_does_not_guess(self):
        result = add_personality(self._scan('unknown'))
        text = ' '.join(result['comments']).lower()
        assert "maxed" not in text and "looks fine" not in text
        assert result['status'] == 'ok'
        assert not any("restart" in t.lower() for t in result['tips'])
