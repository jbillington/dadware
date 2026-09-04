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

## What is still unmeasured

The frozen executable has **never been benchmarked against the script**
under controlled conditions. Everything believed about "the executable is
slower" traces back to runs that were the script both times.

Known and measured: PyInstaller startup overhead is ~0.35s
(`--version`: 0.42-0.57s frozen vs 0.16-0.27s script, 3 runs each).
That is real but far too small to explain a minutes-long gap.

Worth measuring properly, drives unplugged, alternating order to control
for filesystem cache:

1. Script vs `./dist/askdad`, same code, same volume.
2. Pre- vs post-PR#13, to confirm the single-walk change is the win the
   item counts suggest (284k items walked once, vs ~617k across two).
3. The default no-flag path, which renders the full HTML report. Every
   phase timing collected so far used `--terminal` and skipped rendering
   entirely, so HTML generation cost is still unknown.

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
