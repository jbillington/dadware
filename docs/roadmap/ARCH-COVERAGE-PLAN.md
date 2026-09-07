# Architecture Coverage: build fat, test on all three

**Status:** Open, filed Sep 3, 2026. Blocks beta for Apple Silicon users.
**Effort:** 1-2 hours of hands-on across three machines, once the M1 has a
universal2 Python.
**Related:** `docs/roadmap/PERMISSIONS-PLAN.md` (signing/notarization, which the
Tahoe half waits on). PR #10 framed this correctly and was closed:
"arm64 is the untested half, not Intel".

---

## The gap

Every binary built so far is **x86_64-only**, produced on an Intel MacBookPro14,2.
The scanner has never executed on Apple Silicon. That matters more here than in a
portable codebase because the tool is deeply macOS-specific — `vm_stat`,
`system_profiler`, `sysctl`, `du`, `tmutil`, memory-pressure parsing — and those
are exactly the surfaces that differ across architectures.

CI already has a working universal2 job (`.github/workflows/test-and-build.yml`,
`runs-on: macos-13`, installs python.org's universal2 Python, asserts both slices
with `lipo`). It is gated to tags and `workflow_dispatch`, so it has never run.
Triggering it needs no new hardware:

```bash
gh workflow run test-and-build.yml --ref <branch>
```

## Hardware available

| Machine | Role | Covers |
|---|---|---|
| MacBookPro14,2 (Intel, this one) | build + scan | x86_64 slice |
| M1 | **build** + scan | universal2 build host, arm64 runtime |
| M4 | **scan only** | arm64 runtime on current silicon |
| Micah's machine (Tahoe 26.4.1, Apple Silicon) | scan | Gatekeeper on Tahoe |

No machine here runs Tahoe. Micah retests after the `.app` is signed and notarized,
so the Tahoe item is blocked on Apple Developer enrollment — and nothing else is
blocked behind it.

## Trap 1: the build host's Python decides the architecture, not its CPU

PyInstaller cannot cross-compile. A universal2 binary requires the **building
interpreter** to itself be universal2. This cuts both ways and is the single
easiest thing to get wrong:

- Homebrew Python on Intel -> x86_64-only binary
- Homebrew Python on the M1 -> **arm64-only binary**, which will not run on the
  Intel Mac at all
- python.org universal2 Python on *either* -> universal2

The project's zero-runtime-dependency rule makes this tractable: there are no
third-party wheels that might ship thin, only stdlib extension modules, which are
fat in a python.org install.

On the M1:

```bash
curl -fsSL -o /tmp/python.pkg \
  https://www.python.org/ftp/python/3.12.8/python-3.12.8-macos11.pkg
sudo installer -pkg /tmp/python.pkg -target /
PY=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
"$PY" -m pip install 'pyinstaller>=6.0'

export PATH="$(dirname "$PY"):$PATH"
DADWARE_TARGET_ARCH=universal2 ./build_executable.sh

lipo -info dist/askdad    # must list BOTH x86_64 and arm64
```

If `lipo` reports only `arm64`, the wrong interpreter won. Do not ship it. The CI
job makes this a hard failure rather than publishing a silently-thin "universal"
binary; a local build has no such guard, so check by hand.

## Trap 2: Rosetta makes a thin Intel binary look fine on Apple Silicon

An x86_64 binary runs on Apple Silicon under Rosetta 2. So testing the current
Intel build on the M4 would appear to succeed while proving nothing about the
arm64 slice. Confirm the process is running natively:

```bash
sysctl -n sysctl.proc_translated    # 1 = Rosetta, 0 = native arm64
```

## The test plan

Build **once**, test that same binary on three machines. One artifact across three
machines is much stronger evidence than three separate builds.

1. Build universal2 on the M1; verify both slices with `lipo`.
2. Copy to the M4, run a real storage scan, confirm native (not translated) and
   that the numbers are sane.
3. Copy back to the Intel Mac, confirm the x86_64 slice still runs.
4. Then signing/notarization, then Micah on Tahoe.

## What specifically to watch on Apple Silicon

Not known to be broken — `run_command()` returns `None` on any non-zero exit, so a
missing key degrades rather than crashes — but unverified, and silent degradation
is easy to miss in a report full of plausible numbers:

- `sysctl` keys in `utils/system_info.py`: `hw.model`, `machdep.cpu.brand_string`
  (present on Apple Silicon, returns "Apple M1" and similar), `hw.ncpu`,
  `hw.physicalcpu`, `hw.memsize`.
- `system_profiler SPHardwareDataType` / `SPMemoryDataType` output shape — Apple
  Silicon reports memory differently, and `get_memory_info()` parses text.
- `vm_stat` page size and the memory-pressure calculation in `scanners/cpu.py`.
  Apple Silicon uses 16K pages against Intel's 4K; check the pressure percentage
  is plausible, not merely non-zero.
- The report should name the right Mac model and CPU, not fall back to blanks.

## Working agreement

- Run `./venv/bin/python -m pytest tests/ -q` before every commit. **441 passed,
  1 skipped** is the current baseline.
- Open a PR rather than pushing to `main`.
