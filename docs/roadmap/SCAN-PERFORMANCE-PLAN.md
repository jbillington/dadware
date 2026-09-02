# Scan Performance: timers, then the double walk

**Status:** Proposed — next up after Milestone 2. Nothing started; no branch exists on the remote.
**Effort:** Timers 1-2 hours. Walk fix 2-4 hours, most of it verification.
**Related:** the two `## Bugs` items in `BACKLOG.md` that this plan expands.

This document is written to be pasted directly into a fresh session as the work brief.

---

Work on the scan performance items in `jbillington/dadware`. Branch from `main`.

## Two items, in this order

### 1. Per-phase timers and an honest total

Do this first, so the walk fix below has a real before/after measurement.

Today `duration_seconds` is set inside `scan_storage()`, so it times the volume walk
alone — on a real Mac it reported **63s** while a stopwatch on the whole run read
**3m 10s**. Two parts:

- **Timers on each phase** — volume walk, home walk, Mac libraries, hidden caches,
  snapshots, grading, HTML render — behind `DIAGNOSTIC_LOGGING` or a `--timings` flag,
  so a normal run stays quiet.
- **The reported figure becomes actual wall clock for the whole run**, measured in
  `main()`. Today's number reads as the answer to "how long did that take?" and is
  wrong by a factor of three.

### 2. The home directory is walked twice

`run_storage_scan()` in `askdad.py` walks the selected volume, then — when the volume
isn't home — calls `scan_storage()` again on `~` from scratch for the detailed
breakdown, and `merge_home_folders()` swaps the result in.

Real numbers from that run: volume walk **276,353 items**, home walk **244,324** —
roughly **88% of the second walk re-reads files the first already stat'd**, and it
costs about two of the three minutes.

**Why it exists:** `depth` controls how deep the *reported* folder breakdown goes, not
how deep the walk goes. Scanning `/` at depth 2 buckets everything under
`/Users/<user>` into one row, losing the Downloads/Desktop/Documents breakdown that is
the most useful part of the report. The second scan re-roots at `~` so those become
depth-1 folders.

**Options, cheapest first:**

- **(a)** Let the bucketing go one level deeper *under the home path only*.
  `scan_storage()` already visits every file and accumulates per-folder totals — the
  data is there, it is the bucket key that is wrong. This needs no second walk at all
  and is the one to try first.
- **(b)** Scan home first, then walk the volume with home pruned, and add the totals.
- **(c)** Scan `/` at depth 3 and filter.

## Constraints

- Keep the **single-pass `os.scandir` design** and the **one-`stat()`-per-file** rule
  intact (see Key Design Decisions in `CLAUDE.md`). This is about not walking the same
  tree twice, not about how each file is measured.
- **Do not disturb the Docker/sparse-file handling** in `utils/path_utils.py` —
  `is_docker_path()` plus `st_blocks * 512` sizing is deliberate, tested and hard-won.
- The report's folder breakdown must come out **identical to today's**. The two HTML
  snapshot fixtures in `tests/` will catch regressions there.

## Worth folding in while in these files

Both are filed separately in `BACKLOG.md`, both small:

- **Report footers hardcode `Dad Ware v0.1`** — `renderers/html.py` (two places) and
  `renderers/terminal.py`, while `VERSION` is `0.7`. `utils/version.py` already exports
  it. Note the snapshot fixtures carry the stale string, so either regenerate them or
  teach the snapshot `scrub()` to normalize the version the way it already normalizes
  dates.
- **`check_full_disk_access()` probes only Messages, Mail and Photos** — and on the
  Aug 28 run with Full Disk Access off, Photos still probed as readable, which suggests
  it is testing the `.photoslibrary` bundle directory rather than its internals.

## Working agreement

- Run `./venv/bin/python -m pytest tests/ -q` before every commit. **411 passed,
  1 skipped** is the baseline.
- Regenerate the HTML snapshots only when a copy change is intentional, and review the
  diff before committing it.
- Open a PR rather than pushing to `main`.
- **Terminal output stays terse.** Recent work deliberately cut explanatory copy from
  the terminal report; the HTML report is where explanation belongs.
