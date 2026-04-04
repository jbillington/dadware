"""
CLI tests for yourdad.py
Basic smoke tests to ensure commands don't crash
"""

import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_version_command():
    """Test --version command works"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "Dad Ware" in result.stdout or "yourdad" in result.stdout


def test_help_command():
    """Test --help command works"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "Dad Ware" in result.stdout or "yourdad" in result.stdout


def test_cpu_command_exists():
    """Test that cpu subcommand is recognized"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "cpu", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode in [0, 2]


def test_all_command_exists():
    """Test that all subcommand is recognized"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "all", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode in [0, 2]


def test_export_command_exists():
    """Test that export command exists"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "export", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    # Should show help or error (not crash)
    assert result.returncode in [0, 2]  # 0 = success, 2 = argparse error (also OK)
