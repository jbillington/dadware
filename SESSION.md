# Session

Open this first every time you sit down. Three things only.

---

## What I worked on last session

**Milestone 1 (Hidden Storage) — all of it, merged to `main`.** Three scanners: `scanners/hidden_storage.py`
does app caches (1a) plus developer caches and the generic `~/.*` sweep (1b), and `scanners/snapshots.py`
does APFS local snapshots (1c). All wired for display into the HTML report, the terminal report and the LLM
prompt. Suite **227 → 336**. Verified on real hardware twice: 20.3 GB of caches across 214 folders, and one
168-day-old Time Machine snapshot.

Three decisions were settled with evidence rather than guesses:

- **Purgeable space is not obtainable.** The spike compared every candidate against Finder: `statvfs`,
  `diskutil APFSContainerFree` and `system_profiler free_space_in_bytes` all return the same number, and
  Finder's differs by exactly its stated purgeable figure (57.77 − 50.98 = 6.79 GB, to the cent). The
  formula is right; the data source does not exist outside PyObjC. So the report explains the gap instead
  of inventing a number. Full write-up in `HIDDEN-STORAGE-PLAN.md`.
- **Decimal units.** `format_size()` printed 1024-based math labelled "GB", so every size read ~7% under
  Finder — the single most likely "this tool is broken" trigger. Now 1000-based, with `parse_size()` moved
  in lockstep. **RAM stays binary** (Apple calls a 16 GiB module "16 GB") and **grading thresholds stay
  binary**, documented in `docs/GRADING.md`, because converting them would move real grades.
- **Naming.** Three unrelated apps all rendered as "ShipIt" (Squirrel's updater). Updater frameworks are
  generic suffixes now and each strip re-checks the lookups, so `com.microsoft.VSCode.ShipIt` resolves to
  Visual Studio Code.

Deliberately **not** done: no grade components and no personality comments for any of the three scanners.
Adding one moves every existing tester's composite, so it all waits and re-baselines once. No letter grade
has moved.

## Where I stopped

Merged to `main`. Five findings from the user's second test run are logged in `BACKLOG.md` and are the
natural next batch — start them on a fresh branch off `main`, not by extending the merged one:

1. **Snapshot size** — the user reasonably expects a size when there is only one snapshot. Do the cheap
   check first: `_parse_diskutil_plist()` reads only two keys and nobody has looked at the rest of the
   plist. If a size key is in there, the "no sizes" rule was over-broad.
2. **Mac library scan truncates** at its 10s budget (Mail, Time Machine, Creative Apps all skipped), and
   the Partial Scan banner under-reports which ones.
3. **No next step for a bad grade** — Messages scored F at 29.9 GB with no advice attached.
4. **Cache guidance**, including the fact that uninstalling an app does *not* remove its cache — which
   makes orphaned caches an easy, safe category to surface.
5. **LLM prompt** needs a pass now that it carries three new sections.

## Open questions blocking progress

- **Build/packaging is written but deliberately dormant.** The universal2 build job is gated to tags and manual dispatch only (delete the `if:` on the `build` job to re-enable). Nothing about signing has ever executed — it needs an Apple Developer ID. `docs/BUILDING.md` lists the required secrets.
- **CI's new test matrix has not run yet.** It now covers macos-13/py3.9 and macos-latest/py3.12; the 3.9 leg is unverified and may need a fix on first push.
- **`VERSION` is still `"0.1-poc"`.** The build number is automatic now, but the version is not — bump it before tagging. Note the rename must land first (bundle ID is permanent once users grant permissions).
- **Two grading calls need a product decision** (`docs/GRADING.md`): the clutter grade can never return a C, and it is excluded from the composite, so an F there moves the top-line grade by zero. Both change grades users already see.
- **Purgeable-space validation spike:** ten minutes on a real Mac with visible purgeable space, comparing `statvfs` / `diskutil info -plist` / `system_profiler SPStorageDataType -json` against Finder's number — gates the snapshot/purgeable feature (HIDDEN-STORAGE-PLAN.md, Phase 1c).
- **Rename before signing:** the askdad rename must land before the first signed build.
