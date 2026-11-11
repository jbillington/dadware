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
| [`FAQ.md`](FAQ.md) | Plain-language answers to "how does the report work?": every grade, the memory figures, privacy. Keep in step with `GRADING.md` |
| [`TESTING-AND-LAUNCH.md`](TESTING-AND-LAUNCH.md) | Beta test and launch plan; waits on the signed packages (Milestone 3) |
| [`COMPETITIVE-COMPARISON.md`](COMPETITIVE-COMPARISON.md) | Market positioning vs. ncdu, htop, CleanMyMac, DaisyDisk |
| [`COPY-REVIEW-STORAGE.md`](COPY-REVIEW-STORAGE.md) | Working doc: every storage-scan string, with a revision column for the dad-voice pass |

## Roadmap (`roadmap/`): open plans only

What to do and in what order is in [`BACKLOG.md`](../BACKLOG.md), the only to-do list; this table only says what each spec is. Finished plans move to [`roadmap-archive/`](roadmap-archive/).

| File | What it is |
|---|---|
| [`PERMISSIONS-PLAN.md`](roadmap/PERMISSIONS-PLAN.md) | **Active**: the spec behind the signed beta (permissions, `.app`, onboarding) |
| [`CPU-REPORT-FIXES-PLAN.md`](roadmap/CPU-REPORT-FIXES-PLAN.md) | CPU/RAM report fixes from the Nov 11 review |
| [`FEEDBACK-AND-CPU-PROMO-PLAN.md`](roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md) | Feedback invitation and CPU-scan cross-promo |
| [`FAMILY-HELPER-CONCEPT.md`](roadmap/FAMILY-HELPER-CONCEPT.md) | Concept: the product after the beta |
| [`PERSONA-PLAN.md`](roadmap/PERSONA-PLAN.md) | Concept: "Dad's guess at who you are" |

## Historical (never updated)

| Location | What it holds |
|---|---|
| [`CODE-REVIEW.md`](CODE-REVIEW.md) | The Aug 2026 technical review — fully implemented; kept as the rationale |
| [`bugs/`](bugs/) | Resolved bug investigations, kept as forensics. **New bugs go to GitHub Issues** (or `BACKLOG.md` › Bugs) |
| [`roadmap-archive/`](roadmap-archive/) | Finished plans, and plans whose open items are all in `BACKLOG.md`; kept for the reasoning |
| [`research/`](research/) | Competitor UX research (prompt + findings, Aug 2026) — decisions it fed are made |
| `archive/` | Gitignored deep history |
