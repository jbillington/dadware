# Session

Open this first every time you sit down. Three things only.

---

## What I worked on last session

Started Milestone 1 (hidden storage) with **Phase 1a — the app cache scanner**: new `scanners/hidden_storage.py`, plus `CacheEntry`/`CacheRootInfo`/`HiddenCachesScan` in `scanners/models.py`. It measures every top-level subfolder of `~/Library/Caches` and `~/Library/Logs` with `du -skx` (one subprocess per folder, 10s timeout each, 45s for the whole scan), which the plan chose over a Python walk because npm/pnpm/Hugging Face trees nest deeper than any sane depth cap. `get_folder_size_generic()` is the fallback when `du` isn't there, using the same disk-accurate `st_blocks * 512` sizing so a fallback total is comparable to a `du` total.

Friendly names resolve in three steps: bundle IDs of the apps actually installed on this Mac (read straight out of each `Info.plist`), then a table of ~30 mainstream apps, then a reverse-DNS heuristic that drops the TLD prefix and trailing "kind of program" words, so `com.spotify.client` reads as **Spotify** and not **Client**. Existing capitalization survives (`iTerm2`, `VSCode`), and non-bundle folder names (`Firefox`, `CloudKit`) pass through untouched.

Degradation choices worth remembering: the size floor (10 MB) and the top-N cap trim only the entry *list* — `total_size_bytes` always counts every folder measured, including loose files sitting directly in a root, so the report can say "and 240 smaller ones" honestly. A `du` that exits non-zero but still prints a total keeps the total and attaches a permission note; an unreadable root sets `permission_denied` for the Full Disk Access messaging to pick up later. Tests: **227 → 265**, all mocked-subprocess so they pass on non-Mac CI, with one end-to-end case over real files on the `du`-less path.

## Where I stopped

Phase 1a is complete but deliberately **not wired in** — nothing calls `scan_app_caches()` yet. Next is either 1b (developer caches + the `~/.*` sweep, which extends this same module) or the Wiring item (grade component, personality comments, report sections, `llm_prompt.py`). 1b first is the cheaper order: it reuses `measure_folder()` as-is and means the wiring work happens once against a finished dataset.

## Open questions blocking progress

- **Build/packaging is written but deliberately dormant.** The universal2 build job is gated to tags and manual dispatch only (delete the `if:` on the `build` job to re-enable). Nothing about signing has ever executed — it needs an Apple Developer ID. `docs/BUILDING.md` lists the required secrets.
- **CI's new test matrix has not run yet.** It now covers macos-13/py3.9 and macos-latest/py3.12; the 3.9 leg is unverified and may need a fix on first push.
- **`VERSION` is still `"0.1-poc"`.** The build number is automatic now, but the version is not — bump it before tagging. Note the rename must land first (bundle ID is permanent once users grant permissions).
- **Two grading calls need a product decision** (`docs/GRADING.md`): the clutter grade can never return a C, and it is excluded from the composite, so an F there moves the top-line grade by zero. Both change grades users already see.
- **Purgeable-space validation spike:** ten minutes on a real Mac with visible purgeable space, comparing `statvfs` / `diskutil info -plist` / `system_profiler SPStorageDataType -json` against Finder's number — gates the snapshot/purgeable feature (HIDDEN-STORAGE-PLAN.md, Phase 1c).
- **Rename before signing:** the askdad rename must land before the first signed build.
