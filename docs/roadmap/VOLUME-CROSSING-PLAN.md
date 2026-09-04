# Volume Crossing, and the Item Count That Lies

**Status:** Open, filed Sep 3, 2026 from a real-Mac benchmarking session on
JBMacbook-2017 (Intel, 250.7 GB volume, ~332k items). Bugs #8 and #7 in
`docs/bugs/BUG-LOG.md`. Measurements in `docs/bugs/SCAN-TIMING-MEASUREMENTS.md`.
**Effort:** Item 1: 2-3 hours, most of it verification. Item 2: 30 minutes.
**Related:** `docs/roadmap/SCAN-PERFORMANCE-PLAN.md` (shipped as PR #13), whose
phase timers are what made item 1 findable.

This document is written to be pasted directly into a fresh session as the work brief.

---

Work on the volume-crossing bug in `jbillington/dadware`. Branch from `main`.

## Two items, in this order

### 1. The scan walks into every mounted volume (Bug #8, High)

Choosing "Macintosh HD (/)" in the volume picker walks **every mounted volume**,
including external drives and Time Machine backups. `should_exclude()` in
`utils/path_utils.py` filters a fixed list of root directory names
(`EXCLUDED_ROOT_DIRS`, line 24) and has no concept of a filesystem boundary.
`/Volumes` is not on that list:

```python
should_exclude('/Volumes')                         -> False
should_exclude('/Volumes/BACKUP')                  -> False
should_exclude('/Volumes/BACKUP/Backups.backupdb') -> False
```

Measured on the same machine, same code, same chosen volume:

| Backup drive | Items found | Result |
|---|---|---|
| unmounted | ~332,000 | completes in ~1m 45s |
| 2 TB Time Machine mounted | 678,566 and climbing | interrupted at 499s, no end in sight |

**Two separate harms.** The obvious one is that the scan looks hung — and it does
so precisely when a non-technical user has done the responsible thing and attached
their backup drive. The quieter one is worse: backup contents get counted toward
the startup disk, so "Total / Used / Free" and every folder ranking are wrong
whenever any volume is mounted. Nothing in the report says so.

**The fix.** Stat the scan root once, keep its `st_dev`, and skip any directory
entry whose device differs. The walk already carries a `stat_result` per entry
from the single-pass design, so this costs no extra syscall.

Do **not** fix this by adding `Volumes` to `EXCLUDED_ROOT_DIRS`. That is narrower
(misses `/mnt`, `/media`, and arbitrary mount points), and it would wrongly block
an explicit `--volume /Volumes/BACKUP`, which has to keep working — scanning a
named external drive is a legitimate, supported request. The device check handles
both cases correctly: it is relative to whatever root the user picked.

Note `scanners/hidden_storage.py` already gets this right — it shells out to
`du -skx`, where `-x` means "stay on one filesystem", and says so in its module
docstring. The Python walk simply never got the equivalent.

**Verification.** The interesting cases are hard to unit test without a real mount,
so plan on both:

- A unit test with a fake `st_dev` on synthetic entries, asserting the walk stops
  at the boundary.
- A real-Mac check: run with an external drive attached, confirm the item count
  matches the unmounted run (~332k, not ~678k), and confirm
  `--volume /Volumes/<NAME>` still scans that drive fully.

### 2. The home walk reports its count as a total (Bug #7, Low)

`scanners/storage.py:373` prints `→ found {n:,} items total` and is reached by
every walk, with no idea which one is calling it. On the pre-PR#13 path that meant
one run printed two different "totals":

```
→ found 325,114 items total      <- the volume walk
→ found 292,390 items total      <- the home walk, also called a total
```

PR #13 removed the second walk, so the duplicate no longer appears on `main` — the
symptom is gone while the wording is still wrong. Any caller scanning a subtree
hits it. Fix the message to name what was counted and give a running total:

```
→ found 292,390 items in home folder, 617,504 items total
```

`askdad.py:94` has the same ambiguity on the in-progress `→ found {n:,} items...`
line.

## Constraints

- Keep the **single-pass `os.scandir` design** and the **one-`stat()`-per-file**
  rule intact (Key Design Decisions in `CLAUDE.md`). The device check must reuse
  the `stat_result` the walk already has, not add a second stat.
- **`--volume /Volumes/BACKUP` must keep working.** The device check is relative to
  the chosen root, so scanning an external drive on purpose stays supported.
- **Do not disturb the Docker/sparse-file handling** in `utils/path_utils.py`.
- The report's folder breakdown for a normal (nothing mounted) scan must come out
  **identical to today's**. The two HTML snapshot fixtures will catch regressions.

## Measurement notes — read before timing anything

An hour was lost to three traps in the session that produced this document.

- **Unplug external drives before benchmarking,** or record that they were attached.
  A mounted backup drive was responsible for a 2x spread between two runs of
  identical code, and for the 499s non-finishing run above.
- **`askdad` is a shell function** in this user's `~/.zshrc`:
  `askdad () { ( cd ~dad && python3 askdad.py "$@" ) }`. It runs the *script*, so
  `cd dist/ && askdad` does not run `dist/askdad`. Benchmark the executable by
  explicit path only. The build stamp in the banner is the tell — compare it
  against `git log --oneline -1`.
- **Compare wall clock, not the "Scan completed in" line, across PR #13.** That
  commit made the timer honest; the printed number roughly tripled while the work
  got slightly faster. Old code reported 30.6s for a run that took 1:52.

Settled, and not worth re-measuring: the frozen executable and the Python script
are a dead heat (1:46.38 vs 1:46.41 on the same build). The scan is I/O-bound at
45-47% CPU, so PyInstaller's ~0.35s startup is its entire cost.

## Working agreement

- Run `./venv/bin/python -m pytest tests/ -q` before every commit. **441 passed,
  1 skipped** is the current baseline.
- Regenerate the HTML snapshots only when a copy change is intentional, and review
  the diff before committing it.
- Open a PR rather than pushing to `main`.
- **Terminal output stays terse.** The HTML report is where explanation belongs.
