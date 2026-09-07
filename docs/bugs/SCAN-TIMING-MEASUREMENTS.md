# Scan Timing Measurements — Sep 3, 2026

Real-Mac timings from a benchmarking session on JBMacbook-2017 (Intel,
x86_64, 250.7 GB volume, 206.8 GB used, ~325k items). Recorded because
the numbers are only meaningful next to the conditions that produced
them, and two separate measurement traps burned an hour here.

## Measurements

| Run | Code | Interpreter | Scan phase | Wall clock |
|-----|------|-------------|-----------|------------|
| 1 | pre-PR#13 (`bf33589`) | `./venv/bin/python` | 30.6s | 1:52 |
| 2 | pre-PR#13 (`bf33589`) | `python3` via shell function | 59.9s | ~2:48 |

Both runs executed **the same code with the same Python (3.14.2)**. The
~2x spread between them is environmental, not a code difference.

Item counts, run 1: volume walk 325,114; home walk 292,390 (~617k item
visits total across the two walks).

## Trap 1: An external drive was attached

A Time Machine backup volume was plugged in during the slow runs. Disk
contention from backup activity, not the scanner, accounts for most of
the difference between runs 1 and 2. Timings taken with a backup drive
attached are not comparable to timings taken without one.

**Benchmark hygiene:** unplug external drives, or at minimum record their
presence alongside the number.

## Trap 2: `askdad` is a shell function, not the executable

The user's shell defines:

```zsh
askdad () { ( cd ~dad && python3 askdad.py "$@" ) }
```

It `cd`s to the repo and runs the **Python script**. So `cd dist/ && askdad`
does not run `dist/askdad` — it silently runs the source tree instead, and
an attempt to compare "script vs executable" compares the script to itself.

The tell is in the output: the frozen binary built from `main` reports
`v0.7` and `Build: 2026-09-03-ecdfca5`, while both runs above reported
`v0.1` and `Build: 2026-09-01-bf33589` — old-code markers.

**To benchmark the executable, always use an explicit path:** `./dist/askdad`.

## RESOLVED: frozen vs script is a dead heat

Measured Sep 3 ~23:20, same build (`d2e2e5c`) on both sides, backup drive
unplugged, `/` selected:

| Run | Reported scan | Wall clock | user | sys |
|-----|---------------|-----------|------|-----|
| `python3 askdad.py` | 1m 42s | **1:46.41** | 16.92s | 31.18s |
| `./dist/askdad` | 1m 43s | **1:46.38** | 17.01s | 33.16s |

**30 milliseconds apart.** PyInstaller costs ~0.35s at startup and
nothing measurable thereafter. The scan is I/O-bound - both spend ~2/3 of
wall clock blocked on the filesystem (45-47% CPU) - so the interpreter
never becomes the bottleneck. "The executable is slower" is closed as
unfounded.

## The apparent 30.6s -> 1m 42s "regression" is the honest timer

Old code reported far lower numbers than it actually took:

| Code | Reported | Wall clock | Unaccounted |
|------|----------|-----------|-------------|
| pre-PR#13 (`bf33589`) | 30.6s | 1:52.19 | **~82s missing** |
| post-PR#13 (`d2e2e5c`) | 1m 42s | 1:46.41 | ~4s (startup + render) |

The old "Scan completed in 30.6 seconds" was measuring a fraction of the
run. PR #13's `e767dcc` ("Time every scan phase and report the real
total") fixed that, so the number roughly tripled while the actual work
got *slightly faster* - 1:46 vs 1:52 wall clock, with one tree walk
instead of two.

Anyone comparing the printed "Scan completed in" line across that commit
will conclude the scanner got 3x slower. It did not. Compare wall clock.

## What is still unmeasured

The frozen executable has **never been benchmarked against the script**
under controlled conditions. Everything believed about "the executable is
slower" traces back to runs that were the script both times.

Known and measured: PyInstaller startup overhead is ~0.35s
(`--version`: 0.42-0.57s frozen vs 0.16-0.27s script, 3 runs each).
That is real but far too small to explain a minutes-long gap.

1. ~~Script vs executable~~ - done, dead heat (above).
2. ~~Pre- vs post-PR#13~~ - done, 1:46 vs 1:52 wall clock, new code wins.
3. HTML rendering cost is still not isolated, though the ~4s gap between
   reported scan time and wall clock caps it at a few seconds - far too
   small to matter next to the walk.

**The real target is Bug #8**, found during this session: scanning `/`
descends into every mounted volume. With a 2 TB backup drive attached the
same scan blew past 678,000 items and 499s without finishing, versus
~332,000 items in 1m 45s with it unplugged. That, not the interpreter and
not PR #13, is what "glacially slow" was.

## Phase breakdown (post-PR#13, `--terminal --volume /`, no external drive)

```
volume walk          46.8s   68.3%
hidden caches        20.8s   30.3%
mac libraries         0.6s    0.9%
snapshots             0.2s    0.3%
permission check      0.1s    0.1%
grading               0.0s    0.0%
total (wall clock)   1m 09s
```

`hidden caches` spawns 232 `du -skx` subprocesses — the largest remaining
target after the walk itself, and only visible because PR #13 added the
phase timers.
