# Session

Open this first every time you sit down. Three things only.

---

## What I worked on last session

Documentation and planning pass (Aug 16, 2026), all on the `claude/your-dad-snapshots-cache-ea9nmt` branch with a PR open. Wrote two PRDs in `docs/roadmap/`: HIDDEN-STORAGE-PLAN.md (app caches with friendly names, dev-cache bonus, purgeable/snapshots — all folded into the existing report, read-only, aggregate snapshot sizing only) and PERMISSIONS-PLAN.md (MVP = signed/notarized `.app` in a drag-to-Applications DMG with browser progress page, CLI via Homebrew as second channel, FDA as optional bonus tier). Rewrote BACKLOG.md into five sequenced milestones. Documented all CLI flags in README/USER-GUIDE. Re-verified the askdad rename plan against the codebase (still accurate, ~1hr job).

## Where I stopped

Merge the open PR, then start Milestone 1 in BACKLOG.md (hidden caches scanner — no permissions needed, ships value first).

## Open questions blocking progress

- **Code-review refactor discrepancy:** the fixes in docs/CODE-REVIEW.md are NOT in the repo despite believing they were done — check for an unpushed local checkout before writing any Milestone 1 code (details in BACKLOG.md → Code Quality).
- **Purgeable-space validation spike:** ten minutes on a real Mac with visible purgeable space, comparing `statvfs` / `diskutil info -plist` / `system_profiler SPStorageDataType -json` against Finder's number — gates the snapshot/purgeable feature (HIDDEN-STORAGE-PLAN.md, Phase 1c).
- **Rename before signing:** the askdad rename must land before the first signed build (bundle ID is permanent once users grant permissions).
