# CPU/RAM report: fixes from the Nov 11, 2026 feedback review

**Status:** section A (items A1-A8) shipped Nov 11, 2026 (see `CHANGELOG.md`, "CPU report: memory pressure from the kernel"). Section B is open and tracked in `BACKLOG.md`; section C is deferred. Source: `docs/research/ask-dad-cpu-memory-scan-feedback.md`, checked against `test-reports/cpu_2026-11-11_11-45.json` / `.html`, `scanners/cpu.py`, `personality/dad.py`, `renderers/html.py`, `utils/llm_prompt.py`, and the live Mac (`vm_stat`, `sysctl`, `memory_pressure`).

## What the review got right (verified)

| Claim | Verdict | Evidence |
|---|---|---|
| Pressure "high" is not established | **True, and it is a bug.** | `scanners/cpu.py:107`: `pressure = 'high'` if `available_gb < 1.0 or pages_swapped_out > 1000`. `Swapouts` from `vm_stat` is a **counter since boot**, not current activity. The report had 27,414, so it is "high" on essentially any Mac that has run a few hours. Available RAM was 6.0 GB (well above the 2 GB line). On the same Mac minutes later: `sysctl kern.memorystatus_vm_pressure_level` = 1 (normal), `memory_pressure` says 70% free, swap used 308 MB of 1 GB. The kernel says normal; Ask Dad says high. |
| "Memory's maxed out" headline | **True, follows from the above.** | `personality/dad.py:180` prints it on `pressure == 'high'`. The "restart your Mac, clears memory cruft" tip (`dad.py:281`) fires on the same flag. |
| Free RAM is shown three ways | **True.** | HTML and terminal: `total - sum(process RSS)` = 3.0 GB (`html.py:2196`, `terminal.py:183`). AI prompt: `vm_stat` free pages = **0.0 GB** (`llm_prompt.py:283`). JSON: `free_gb` 0.012, `available_gb` 5.99. Four numbers, one word "free". |
| "Used" is a questionable definition | **True.** | `total_used_gb` (12.98) is the sum of per-process RSS (`cpu.py:283`). RSS double-counts shared pages and excludes wired/compressor memory, so it is not what Activity Monitor calls Memory Used. |
| "Available" is mislabelled | **Partly true.** | `available = free + inactive` (`cpu.py:94`). Reasonable approximation, but it omits purgeable and file-backed pages and is labelled as if authoritative. |
| Grouped process memory is not recoverable RAM | **True.** | Codex group = 2,433 MB over 15 processes (summed RSS). The code presents it as a ranking, but the AI prompt and tips ("quit apps to free up memory") imply recovery. |
| 551 small processes = 6.5 GB, "death by a thousand cuts" | **Numbers true, framing weak.** | 551 processes, 6,636 MB. Counting small processes says nothing about whether closing them helps. |
| Process command lines leak into exports | **True.** | The JSON holds full command lines (e.g. `--user-data-dir=/Users/johnbillington/Library/Application Support/Codex`). The AI prompt prints the first 150 characters of each of the top 100 (`llm_prompt.py:429-443`) with absolute paths and the account name, not `~`. |
| 0.275 s run, 580 processes, 16 GB RAM, compressed 0.34 GB | **True.** | JSON. The 0.275 s is collection only, as the review says. |
| Generic tips (archive Messages, close browser tabs) not tied to evidence | **True.** | `dad.py:244` tells people to archive Messages conversations because a Messages *process* is over 1 GB; `dad.py:173/184` suggest closing tabs on CPU or pressure flags. |
| Single snapshot shouldn't claim sustained problems | **True.** | One sample of CPU and one `vm_stat` read; the backlog already lists "Sustained CPU hogs". |
| Benchmark, evaluation and evidence-graph recommendations | **Not code claims.** | Reasonable, but deferred (see below). |

The review's second half (benchmark design, product priorities) is strategy, not something to verify in the code.

## Plan

### A. Before beta (small, fast, high trust)

1. **Fix the pressure classification** (`scanners/cpu.py`). Read the kernel's own answer: `sysctl -n kern.memorystatus_vm_pressure_level` (1 normal, 2 warn, 4 critical); map to `low` / `medium` / `high`. Keep `memory_pressure -Q`-style percent as a second signal only if `sysctl` is missing. Stdlib `subprocess`, same pattern as the existing `vm_stat` call, and degrade to "unknown" (not "high") if the call fails. Add `pressure_source` to the dict.
2. **Stop using the lifetime swap counter.** Delete `pages_swapped_out > 1000/100` from the rule. If swap evidence is wanted, use `sysctl vm.swapusage` (current swap used) and show it as a plain number, never as a trigger on its own.
3. **Reword the warnings.** "Memory's maxed out" only on kernel-critical; "memory is getting busy" on warn; on normal say so ("memory is fine, macOS is just using what it has"). Remove "restart clears memory cruft" unless pressure is warn or critical.
4. **One definition of "free".** Pick the schema: `free` (vm_stat free pages), `available` (free + inactive + purgeable, clearly approximated), `used_by_processes` (sum of RSS, renamed). Use these in the HTML, terminal and AI prompt from the same dict; never print `total - sum(RSS)` as "Free". Rename the HTML card "Free" to "Available" and print the number from `available_bytes`.
5. **Rename "Used".** Call the RSS sum "Memory held by apps (approx.)" with a one-line note that shared memory is counted more than once, or switch to `vm_stat` active + wired + compressed. The second is closer to Activity Monitor and is the recommended option.
6. **Privacy in the AI prompt.** Replace the `Command:` lines with the app name and process count only. If a command line is kept, show the executable path with `~` for home and drop all arguments (`--user-data-dir=...`, tokens). Reuse `_tilde()` from `utils/llm_prompt.py`. Leave the local JSON as is, but note it in the report that the JSON holds full command lines and should not be shared.
7. **Soften the recoverability language.** Rename grouped totals "memory used by this app (adds up shared pages)" and change tips to "quitting X may free up to about N GB". Drop the unconditional Messages-archive and tab tips unless pressure is warn or critical.
8. **Tests.** Pressure mapping table (1, 2, 4, unknown, command failure); a regression test that a high `Swapouts` counter with normal kernel pressure is `low`; free/available consistent across HTML, terminal and prompt for one fixture; prompt contains no `--user-data-dir` and no `/Users/<name>`. Regenerate `cpu_scan.snapshot.html` and read the diff.

Order: 1 → 3 (they change what the user is told), then 4-5, then 6, then 7, with tests as each lands. Roughly half a day; every item is a few lines.

### B. After beta, with the feedback in hand

- A second sample a few seconds later (steady vs spike), tied to the existing "Sustained CPU hogs" backlog item.
- Memory health grade, as the sibling of storage Health (backlog: "Health grade for memory", "CPU Health thresholds"). Only after item 1, since it would be graded on the pressure signal.
- Rebuild `generate_cpu_prompt()` in the storage prompt's shape (backlog: "CPU and generic AI prompts still use the old format"). Do it with item 6 if time allows, since both rewrite the same function.
- Validate pressure against Activity Monitor on an idle Mac and a deliberately loaded one (a quick manual check; no framework needed).

### C. Not now

- Evidence graph with provenance, confidence, projected benefit and verification on every recommendation. A good direction, but a redesign of the data model; revisit with the privacy-preserving AI export idea in the feature backlog.
- Codex A/B/C benchmark. It tests the product after A is fixed; running it on a scanner that cries "high" on every Mac would measure the bug.
- Multi-Mac cross-device testing: covered by the beta itself.

## Related

`BACKLOG.md` (CPU items under "Grading fixes" and "Memory and CPU scan"), `FEEDBACK-AND-CPU-PROMO-PLAN.md` (promotes the CPU scan: **do A first**, or the promo sends every beta tester to a report that tells them their memory is maxed out).
