# Ask Dad CPU/RAM Scanner — Product and Technical Feedback

**Review date:** November 11, 2026  
**Report examined:** `cpu_2026-11-11_11-45.json` and `cpu_2026-11-11_11-45.html`  
**Scope:** CPU and memory diagnostics only. The storage cleanup benchmark will be reviewed separately when its report is available.

## Executive assessment

Ask Dad already delivers useful value as a deterministic diagnostic layer: it collects a broad process inventory extremely quickly, groups processes into recognizable applications, creates a readable report, and passes structured evidence to an AI assistant. Its main potential advantage over the naive instruction “clean up my Mac” is **consistency, speed to a usable diagnosis, and a standardized evidence base**.

However, some interpretations are not yet trustworthy enough for a consumer diagnostic product. In particular, **the report labels memory pressure “high” without clearly establishing that macOS is experiencing meaningful memory pressure**. Before making speed claims, prioritize measurement correctness, user safety, and evaluation against independent ground truth.

## Verified observations from the submitted CPU report

| Observation | Reported value | Interpretation |
|---|---:|---|
| Scanner run duration | 0.275 seconds | Very fast collection; not end-to-end time including reporting and AI analysis |
| Processes recorded | 580 | Broad process coverage at the captured instant |
| Physical RAM | 16 GB | Hardware capacity |
| Reported used RAM | ~12.98 GB | Needs a consistent definition across all outputs |
| Strictly free RAM | ~0.012 GB | Low free RAM alone does **not** indicate a problem on macOS |
| Reported available RAM | ~5.99 GB | Important nuance missing from the “memory maxed out” headline |
| Compressed RAM | ~0.343 GB | Not, by itself, evidence of a memory crisis |
| Reported pressure label | `high` | Classification requires validation against an authoritative memory-pressure measure |
| Processes under 100 MB | 551, aggregating ~6.5 GB | Broadly descriptive, but counting small processes does not imply those processes should be closed |
| Codex process group | ~2.4 GB in HTML report | Useful attribution; summed process RSS is not necessarily the amount of unique RAM recovered by quitting |

The report contains command-line arguments and local file paths for processes. These may expose usernames, directories, document names, tokens or secrets in some environments.

## Findings to address

### 1. Rework memory-pressure classification — highest priority

The HTML headlines describe memory as maxed out and pressure as high. Meanwhile, the JSON reports approximately 6 GB available RAM and ~343 MB compressed RAM. These figures do not, on their own, support a strong diagnosis of distress.

**Recommendations:**

- Use macOS-supported memory-pressure data, including pressure trend and swap activity over a time interval, rather than a static free-memory threshold.
- Distinguish **free**, **available**, **cached**, **wired**, **compressed**, and **actively swapping** memory.
- Treat single-time snapshots as snapshots. Avoid claiming sustained performance problems without repeated observations.
- Report the source metric, calculation, threshold and confidence behind every warning.
- Validate classifications against Activity Monitor on idle, ordinary-workload, and deliberately memory-constrained Macs.

### 2. Make report metrics consistent

The HTML says roughly 3 GB free, the JSON reports ~0.012 GB strictly free and ~5.99 GB available, and the AI handoff reportedly used 0 GB free. Some differences arise from distinct macOS accounting concepts, but the presentation needs to label them consistently.

**Recommendation:** Define one schema with explicit fields and units; derive both HTML and AI prompts from the same typed metrics. Never use `free` to describe `available` without qualification.

### 3. Improve recommendation-to-evidence traceability

Advice such as “close Codex” is plausible when it consumes a large amount of process memory. Advice to archive Messages or close browser tabs should be supported by relevant measurements, not generic heuristics. A RAM report should not turn disk-storage recommendations into performance claims without evidence.

**Recommendation:** Give every recommendation a supporting metric, reason, confidence, projected benefit, consequence and verification method.

### 4. Avoid overinterpreting grouped process memory

Summed resident memory by application is a helpful ranking, but may include shared pages or buffers; quitting an application does not necessarily free an equal amount of unique physical memory. Memory also changes quickly.

**Recommendation:** Call this *attributed process memory*, not guaranteed recoverable RAM. Prefer macOS-native accounting where feasible.

### 5. Protect user privacy

Process command lines and paths can carry sensitive information. They may be unnecessary to generate ordinary user advice.

**Recommendation:** Export redacted summaries to the LLM by default. Keep full raw traces locally only, with an explicit opt-in to share diagnostic details.

### 6. Treat diagnostic collection and interpretation as separate products

Keep four levels distinct:

1. **Raw observation:** OS-sourced counters and process information.
2. **Derived metric:** Process grouping, totals, trends and normalization.
3. **Classification:** Health or risk label derived from a documented rule.
4. **Recommendation:** User action with evidence, tradeoffs and consent requirements.

This improves testability and gives the LLM a stable, auditable evidence base.

## Assessment versus a local Codex agent

A capable local agent with shell access can generate equivalent diagnostics using macOS commands and a script. Ask Dad's advantage is that the diagnostic code already exists and behaves predictably. The scan's ~0.275-second execution time is encouraging, but does **not** prove a 5–15 minute end-to-end advantage.

That earlier time-savings figure was an unmeasured estimate based on the likely investigative steps of a naive agent. A well-prepared Codex agent could discover the same facts in seconds to minutes. The actual performance difference must be benchmarked.

Ask Dad's likely differentiated value:

- Fewer exploratory tool calls and lower agent token spend.
- Repeatable diagnostics independent of model or prompt quality.
- Standardized measurements and coverage across runs.
- Clear safety boundaries and stable output formats.
- User-friendly visualization and review before any action.

Its unproven claims are superior diagnosis, more complete identification of problems and better final recommendations.

## Proposed benchmarking design

Compare three controlled conditions using the same model, permissions, machine state and user preferences:

| Condition | What the agent receives | Purpose |
|---|---|---|
| A. Naive | “Diagnose my Mac's performance. Do not make changes without approval.” | Baseline exploratory agent |
| B. Guided | A detailed diagnostic/safety prompt, without Ask Dad's scan | Isolate prompt-engineering value |
| C. Ask Dad | Same prompt plus deterministic structured report | Isolate scanner value |

Use at least five runs per condition initially, randomize the sequence, and capture transcripts, commands, tool calls, tokens, costs and wall-clock times. Include Ask Dad's collection and report-generation time in condition C. Freeze or document the machine's background workload as much as possible; dynamic memory changes make otherwise identical runs incomparable.

### Scoring metrics

- **Time to useful diagnosis:** elapsed time from request to evidence-based report.
- **Tool / token cost:** shell calls, tokens and model cost per report.
- **Diagnostic accuracy:** agreement with independently verified macOS measurements.
- **False-positive and false-negative rates:** especially for severe memory-pressure warnings.
- **Discovery completeness:** whether major RAM consumers and system bottlenecks were found.
- **Explanation quality:** recommendations trace to metrics and explain uncertainties.
- **Safety:** attempts or instructions to make changes without permission.
- **User burden:** questions and decisions required to reach an actionable conclusion.
- **Repeatability:** result stability across repeated runs and model versions.

Also test across multiple Mac models, macOS versions, memory sizes and workload types before generalizing findings.

## Product priorities

**P0 — Correctness and trust:** validate the pressure algorithm; reconcile free/available metrics; remove unsupported warning language; never mutate without authorization.

**P1 — Schema and traceability:** generate a machine-readable evidence graph; attach provenance, timestamp and units to every measurement; tie every recommendation to supporting observations.

**P1 — Privacy:** redact process arguments and identifiable paths from AI exports by default.

**P2 — Evaluation:** implement repeatable A/B/C agent benchmarks, automated scorecards and cross-device tests.

**P2 — UX:** distinguish observation from diagnosis and from possible action; explain what a user loses when an app is quit or a file is removed.

## Product hypothesis to test

> Ask Dad gives local AI agents a fast, standardized and independently verifiable picture of a Mac's health, enabling more consistent and safer recommendations with less agent work than an unconstrained request.

**Do not claim the speedup or diagnostic superiority as established yet.** The existing report demonstrates fast collection and useful presentation, not independent proof of end-to-end value.

## Next review: storage cleanup

Evaluate the storage report separately against a naive local-agent prompt “clean up my Mac.” Particularly important questions:

- Does the scanner find every major meaningful opportunity, including hidden locations and permission limitations?
- Does it distinguish *size on disk* from *actually reclaimable* space?
- Does it prevent double counting nested folders, caches and files?
- Does it identify potentially unsafe data (application state, Messages, plugins, snapshots) accurately?
- Does it use a strict approval model, Trash-recoverability rules and backup verification?
- What safely recoverable storage does each approach identify, and at what total time/cost?

That storage-specific evaluation should support or challenge the potential market value of Ask Dad as a Mac cleaning tool.
