# Document Index

Every doc in the project, what it's for, and whether it's live. One rule keeps this useful:
**live docs get updated when reality changes; historical docs never do** — they're accurate to
when they were written and reading them as current is the mistake this index prevents.

## The living root set

| File | Role |
|---|---|
| [`README.md`](../README.md) | User-facing: what Ask Dad is, license |
| [`CLAUDE.md`](../CLAUDE.md) | Working guide: commands, architecture, key decisions, product & distribution |
| [`BACKLOG.md`](../BACKLOG.md) | **Only unshipped work**, sequenced into milestones. When something ships it moves to the changelog |
| [`CHANGELOG.md`](../CHANGELOG.md) | Everything shipped, full original text preserved — the reasons, not just the changes. Absorbed the old `SESSION.md` day log |

## Reference (live)

| File | Role |
|---|---|
| [`USER-GUIDE.md`](USER-GUIDE.md) | End-user guide; bundled into the distribution zip |
| [`BUILDING.md`](BUILDING.md) | Building, signing, and notarizing the executable |
| [`GRADING.md`](GRADING.md) | How every grade is computed — data flow, components, thresholds, worked examples |
| [`TESTING-AND-LAUNCH.md`](TESTING-AND-LAUNCH.md) | Beta test and launch plan; waits on the signed packages (Milestone 3) |
| [`COMPETITIVE-COMPARISON.md`](COMPETITIVE-COMPARISON.md) | Market positioning vs. ncdu, htop, CleanMyMac, DaisyDisk |
| [`COPY-REVIEW-STORAGE.md`](COPY-REVIEW-STORAGE.md) | Working doc: every storage-scan string, with a revision column for the dad-voice pass |

## Roadmap (`roadmap/`) — PRDs, each with a Status header

| File | Status |
|---|---|
| [`PERMISSIONS-PLAN.md`](roadmap/PERMISSIONS-PLAN.md) | **Active** — the spec behind Milestones 2-4 |
| [`HIDDEN-STORAGE-PLAN.md`](roadmap/HIDDEN-STORAGE-PLAN.md) | Phase 1 shipped Aug 2026; Phase 2 (Trash) open, FDA-gated |
| [`ASKDAD-RENAME-PLAN.md`](roadmap/ASKDAD-RENAME-PLAN.md) | Executed Aug 28, 2026 |
| [`SCAN-PERFORMANCE-PLAN.md`](roadmap/SCAN-PERFORMANCE-PLAN.md) | **Proposed** — timers, then the double home walk; next up |
| [`VOLUME-CROSSING-PLAN.md`](roadmap/VOLUME-CROSSING-PLAN.md) | **Open** — scanning `/` walks mounted volumes (Bug #8); next up |
| [`ARCH-COVERAGE-PLAN.md`](roadmap/ARCH-COVERAGE-PLAN.md) | **Open** — arm64 is untested; build fat on the M1, scan on the M4 |
| [`LIGHTWEIGHT-TUI-PLAN.md`](roadmap/LIGHTWEIGHT-TUI-PLAN.md) | Deprioritized — CLI-channel nicety, unscheduled |

## Historical (never updated)

| Location | What it holds |
|---|---|
| [`CODE-REVIEW.md`](CODE-REVIEW.md) | The Aug 2026 technical review — fully implemented; kept as the rationale |
| [`bugs/`](bugs/) | Resolved bug investigations, kept as forensics. **New bugs go to GitHub Issues** (or `BACKLOG.md` › Bugs) |
| [`research/`](research/) | Competitor UX research (prompt + findings, Aug 2026) — decisions it fed are made |
| `archive/` | Gitignored deep history |
