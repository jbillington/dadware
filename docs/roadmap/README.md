# Roadmap index

One line per plan: where it stands and what comes next. `BACKLOG.md` holds the ordered to-do list ("What to do next" at the top); `CHANGELOG.md` holds what shipped and why. Last updated Nov 11, 2026.

## Active: the road to the signed beta

| Plan | Status | Next step |
|---|---|---|
| `PERMISSIONS-PLAN.md` | Phase 1 (permission UX) shipped, pending real-Mac `tccutil` checks. Phase 2: a signed, notarized `.app` in a stapled DMG shipped Nov 7 as a thin Terminal launcher. | Real-Mac permission matrix; then a Terminal-free app and `Info.plist` strings (Phase 2), first-run onboarding (Phase 3). |
| `ARCH-COVERAGE-PLAN.md` | Mostly closed. The universal2 binary runs on Intel and Apple Silicon. | Clean release build from `main`, a clean-machine run on a second Intel Mac, and a Tahoe retest. |
| `VOLUME-CROSSING-PLAN.md` | Fixed in code; confirmed on an M1. | Scan `/` with a backup drive mounted; the item count should match the unplugged run (~332k, not ~678k). |

## Done (kept for the reasoning)

| Plan | Status |
|---|---|
| `ASKDAD-RENAME-PLAN.md` | Executed Aug 28, 2026. |
| `HIDDEN-STORAGE-PLAN.md` | Caches (Aug) and Trash (Sep) shipped. |
| `SCAN-PERFORMANCE-PLAN.md` | Done Sep 2, 2026. Further speed ideas are in the backlog under "Scan Speed and Chart Design". |
| `sonnet-feedback.md` | A review of a sample report and prompt. The prompt items were resolved Nov 11, 2026 (see the note inside); the rest moved to the backlog. |

## Concepts, not scheduled

| Plan | What it is |
|---|---|
| `FAMILY-HELPER-CONCEPT.md` | The product after the beta: a helper for the family's tech-support person. |
| `PERSONA-PLAN.md` | "Dad's guess at who you are" from installed apps; would also add a first sentence to the AI prompt. |
| `LIGHTWEIGHT-TUI-PLAN.md` | A terminal UI for the CLI channel. Deprioritized behind the `.app`. |

## Where the AI prompt stands

The prompt (`utils/llm_prompt.py`) was rebuilt for the storage scan on Nov 11, 2026: it asks for a cleanup plan the user reviews first, defaults to Move to Trash, shows `~` paths, and has a privacy checkbox for file names. The CPU and generic prompts still use the old format (backlog, "Bugs"). The prompt is also the seed of the "Ask ChatGPT" button in `FAMILY-HELPER-CONCEPT.md`.
