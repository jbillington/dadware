"""Tests for utils/timing.py and the run's honest total duration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

import askdad
from utils.timing import RunTimer, format_duration, get_timer


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(0) == "0.0s"
        assert format_duration(4.24) == "4.2s"
        assert format_duration(59.9) == "59.9s"

    def test_minutes(self):
        assert format_duration(60) == "1m 00s"
        assert format_duration(63.4) == "1m 03s"
        assert format_duration(190) == "3m 10s"

    def test_negative_reads_as_zero(self):
        """A clock that ran backwards is still not a negative duration."""
        assert format_duration(-5) == "0.0s"


class TestRunTimer:
    def test_phases_record_in_order_of_first_use(self):
        timer = RunTimer()
        with timer.phase('volume walk'):
            pass
        with timer.phase('home walk'):
            pass
        assert list(timer.phases) == ['volume walk', 'home walk']

    def test_repeated_phase_accumulates(self):
        timer = RunTimer()
        timer.record('html render', 1.0)
        timer.record('html render', 2.0)
        seconds, count = timer.phases['html render']
        assert seconds == pytest.approx(3.0)
        assert count == 2

    def test_phase_records_even_when_the_block_raises(self):
        """A scan that dies still has to say where the time went."""
        timer = RunTimer()
        with pytest.raises(ValueError):
            with timer.phase('mac libraries'):
                raise ValueError("boom")
        assert 'mac libraries' in timer.phases

    def test_start_resets_the_clock_and_the_phases(self):
        timer = RunTimer()
        timer.record('grading', 5.0)
        timer.start()
        assert timer.phases == {}
        assert timer.elapsed < 1

    def test_summary_is_silent_with_no_phases(self):
        assert RunTimer().summary_lines() == []

    def test_summary_is_longest_phase_first_and_carries_a_total(self):
        timer = RunTimer()
        timer.record('volume walk', 1.0)
        timer.record('home walk', 9.0)
        lines = timer.summary_lines()
        assert 'home walk' in lines[1]
        assert 'volume walk' in lines[2]
        assert 'total (wall clock)' in lines[-1]

    def test_print_summary_stays_quiet_unless_enabled(self, capsys):
        timer = RunTimer(enabled=False)
        timer.record('grading', 1.0)
        timer.print_summary(sys.stderr)
        assert capsys.readouterr().err == ""

    def test_print_summary_goes_to_stderr_when_enabled(self, capsys):
        timer = RunTimer(enabled=True)
        timer.record('grading', 1.0)
        capsys.readouterr()  # drop the live line record() prints
        timer.print_summary(sys.stderr)
        err = capsys.readouterr().err
        assert 'phase breakdown' in err
        assert 'grading' in err


class TestFinishRun:
    def test_stamps_whole_run_wall_clock_over_the_walk_time(self):
        """The number in the report answers "how long did that take?".

        It used to be the volume walk alone, which on a real Mac read 63s
        against a stopwatch total of 3m 10s.
        """
        timer = get_timer()
        timer.start()
        timer._start -= 100  # pretend the run began 100 seconds ago
        scan_data = {'duration_seconds': 4.2}
        askdad.finish_run(scan_data)
        assert scan_data['duration_seconds'] >= 100

    def test_none_scan_data_is_a_no_op(self):
        assert askdad.finish_run(None) is None
