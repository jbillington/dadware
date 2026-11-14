"""Tests for install.sh, the curl installer, and the Homebrew formula.

install.sh runs on a Mac, so these tests fake `uname` to say Darwin and serve
the release files from a local folder through ASKDAD_DOWNLOAD_URL (curl reads
file:// URLs). The "binary" is a shell script that prints a version.
"""

import hashlib
import os
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
INSTALL_SH = ROOT / "install.sh"
FORMULA = ROOT / "Formula" / "askdad.rb"
ASSET = "askdad-macos.tar.gz"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not all(shutil.which(t) for t in ("sh", "curl", "tar", "shasum")),
        reason="needs sh, curl, tar and shasum",
    ),
]


def _make_release(folder: Path, checksum: str = None) -> Path:
    """Write a fake release (tarball + .sha256) into folder."""
    folder.mkdir(parents=True, exist_ok=True)
    binary = folder / "askdad"
    binary.write_text("#!/bin/sh\necho 'Ask Dad vTEST'\n")
    binary.chmod(0o755)
    tarball = folder / ASSET
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(binary, arcname="askdad")
    binary.unlink()
    digest = checksum or hashlib.sha256(tarball.read_bytes()).hexdigest()
    (folder / f"{ASSET}.sha256").write_text(f"{digest}  {ASSET}\n")
    return folder


def _run(tmp_path: Path, release: Path, uname: str = "Darwin", **env):
    """Run install.sh with a fake uname and a fake HOME."""
    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir(exist_ok=True)
    (fake_bin / "uname").write_text(f"#!/bin/sh\necho {uname}\n")
    (fake_bin / "uname").chmod(0o755)
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    full_env = {
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "HOME": str(home),
        "TMPDIR": str(tmp_path),
        "ASKDAD_DOWNLOAD_URL": release.as_uri(),
        **env,
    }
    result = subprocess.run(
        ["sh", str(INSTALL_SH)], env=full_env, capture_output=True, text=True
    )
    return result, home


class TestInstallScript:
    def test_installs_binary_and_adds_path(self, tmp_path):
        release = _make_release(tmp_path / "release")
        result, home = _run(tmp_path, release)
        assert result.returncode == 0, result.stderr
        installed = home / ".local" / "bin" / "askdad"
        assert installed.exists()
        assert os.access(installed, os.X_OK)
        assert "vTEST" in subprocess.run(
            [str(installed)], capture_output=True, text=True
        ).stdout
        assert ".local/bin" in (home / ".zshrc").read_text()

    def test_path_line_is_added_once(self, tmp_path):
        release = _make_release(tmp_path / "release")
        _run(tmp_path, release)
        _, home = _run(tmp_path, release)
        assert (home / ".zshrc").read_text().count("Added by the Ask Dad installer") == 1

    def test_no_modify_path_leaves_zshrc_alone(self, tmp_path):
        release = _make_release(tmp_path / "release")
        result, home = _run(tmp_path, release, ASKDAD_NO_MODIFY_PATH="1")
        assert result.returncode == 0, result.stderr
        assert not (home / ".zshrc").exists()
        assert "is not on your PATH" in result.stdout

    def test_custom_install_dir(self, tmp_path):
        release = _make_release(tmp_path / "release")
        target = tmp_path / "custom"
        result, _ = _run(
            tmp_path, release, ASKDAD_INSTALL_DIR=str(target), ASKDAD_NO_MODIFY_PATH="1"
        )
        assert result.returncode == 0, result.stderr
        assert (target / "askdad").exists()

    def test_bad_checksum_installs_nothing(self, tmp_path):
        release = _make_release(tmp_path / "release", checksum="0" * 64)
        result, home = _run(tmp_path, release)
        assert result.returncode != 0
        assert "checksum does not match" in result.stderr
        assert not (home / ".local" / "bin" / "askdad").exists()

    def test_refuses_non_mac(self, tmp_path):
        release = _make_release(tmp_path / "release")
        result, home = _run(tmp_path, release, uname="Linux")
        assert result.returncode != 0
        assert "macOS only" in result.stderr
        assert not (home / ".local").exists()

    def test_missing_release_fails_cleanly(self, tmp_path):
        result, _ = _run(tmp_path, tmp_path / "nothing-here")
        assert result.returncode != 0
        assert "could not download" in result.stderr


class TestFormula:
    def test_formula_installs_the_release_asset(self):
        text = FORMULA.read_text()
        assert re.search(
            r'url "https://github\.com/jbillington/dadware/releases/download/v[^/]+/'
            + re.escape(ASSET) + '"',
            text,
        )
        assert 'bin.install "askdad"' in text

    def test_formula_version_matches_url_tag(self):
        text = FORMULA.read_text()
        tag = re.search(r"/download/v([^/]+)/", text).group(1)
        version = re.search(r'^\s*version "([^"]+)"', text, re.M).group(1)
        assert tag == version
