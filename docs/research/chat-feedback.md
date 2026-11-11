# Ask Dad Storage Scanner
## Product and Technical Assessment

**Review date:** November 11, 2026  
**Source files:** `storage_2026-11-11_11-42.json` and `.html`  
**Comparison:** Ask Dad + AI versus a local Codex agent given the prompt “Clean up my Mac.”

**Verdict:** Ask Dad is a credible local diagnostic and AI-assisted cleanup planning product. Its strongest potential advantages are systematic discovery, repeatable measurements, and a safety-oriented workflow.

The current implementation has accounting and classification problems that should be corrected before claiming it is safer, faster, or more effective than Codex.

The scanner's reported sizes are observations, not verified recoverable disk space.

---

# 1. Recommended Engineering Improvements

The following ten recommendations are ranked in my subjective priority order, based on safety, correctness, user value, and commercial significance.

### 1. Fix misleading reclaimable-space estimates

**Finding:** The report's `reclaimable_percent` value is 21.0257%, suggesting approximately 52.7 GB of recoverable storage on a 250.7 GB disk.

There is no auditable breakdown showing that 52.7 GB can actually be recovered without affecting protected files.

Some of the space is associated with Messages, application data, and music production software the user wants to preserve.

**Recommendation:** Create an itemized, deduplicated recovery ledger that distinguishes:

- Observed file size
- Potentially recoverable size
- User-approved recovery
- Expected physical storage gain
- Actual measured storage gain

**Why this is my first priority:** Accurate recovery estimates are fundamental to user trust. A tool that promises 50 GB but safely delivers only 10 GB will disappoint users.

### 2. Correct cache classifications

**Finding:** The report groups 25.34 GB under hidden caches and related storage.

This includes:

- `~/.cache`: 2.1 GB
- `~/.npm`: 2.0 GB
- `~/.local`: 1.5 GB
- Messages cache: 8.5 GB

Not all of these directories contain disposable data. In particular, `~/.local` may contain installed software, configuration, and important application state.

**Recommendation:** Rename the category to *Hidden Storage and Temporary-Data Candidates*.

For each item, record its application owner, actual data type, supported cleanup mechanism, and whether removal bypasses Trash.

Unknown folders should default to **Keep / Investigate**.

**Why second:** Incorrectly treating application data as disposable could cause real data loss or break installed software.

### 3. Eliminate double-counting

**Finding:** The Music library reports approximately 3.9 GB by including both a parent folder and a nested folder that appears already counted in the parent.

The report also displays 133.4 GB for its top ten folders, while the first ten JSON folder entries total approximately 128.55 GB.

The discrepancy may reflect different selection criteria, but those criteria aren't documented.

**Recommendation:** Represent parent-child relationships explicitly, normalize paths, and ensure folder totals contain only unique storage.

Use a consistent calculation in the JSON report, HTML report, and AI handoff.

**Why third:** Double-counting undermines the credibility of every subsequent cleanup estimate.

### 4. Rank actionable cleanup opportunities

**Finding:** The short AI handoff emphasizes extremely large files, particularly music instruments and applications.

But the full report contains useful candidates that the handoff underemphasizes:

- Omarchy ISO: 6.2 GB
- Zoom recordings and material: approximately 3.2 GB
- ChatGPT installer DMG: 606.6 MB
- Claude installer DMGs: 253.5 MB and 247.8 MB
- Obsidian installer DMG: 210.4 MB

The user wants to keep Ableton and music plugins. Their large sizes shouldn't make them high-priority cleanup recommendations.

**Recommendation:** Rank candidates based on size, removal confidence, user preferences, and safety.

Provide separate sections for potentially removable files and large protected files.

**Why fourth:** The scanner already discovers useful information. Better prioritization would translate more of that information into actual value.

### 5. Itemize the Trash before suggesting emptying

**Finding:** The report identifies 8.012 GB in Trash, spanning three items. The oldest is reportedly 479 days old.

However, the summary doesn't identify those objects individually.

**Recommendation:** Show each item's name, size, type, and date, with a convenient way to inspect or restore it.

Emptying Trash must remain a separate final action requiring explicit user approval.

**Why fifth:** This is one of the easiest recovery opportunities, but the user needs enough information to decide safely.

### 6. Make AI handoffs private by default

**Finding:** The raw scanner inventory contains full file paths and filenames.

These can expose personal information, development projects, private documents, and other sensitive details.

**Recommendation:** Produce a privacy-preserving AI handoff by default.

Include useful classifications, sizes, and opaque identifiers. Allow users to reveal filenames selectively when they materially improve the cleanup recommendation.

Keep the complete local inventory on the Mac.

**Why sixth:** Privacy could become a meaningful differentiator against cloud-based agent workflows.

### 7. Treat APFS snapshots cautiously

**Finding:** The scanner found one local Time Machine snapshot approximately 247 days old.

Its actual reclaimable size is unknown.

**Recommendation:** Exclude snapshot storage from recovery estimates unless independently measured.

Do not recommend manual snapshot removal by default. Explain that APFS snapshots can retain storage blocks after files have been moved to Trash.

**Why seventh:** Incorrect recovery predictions create confusion, and snapshot removal is not equivalent to a reversible Finder action.

### 8. Expose scan coverage and unknown storage

**Finding:** The scanner reports:

- 6,153 excluded entries
- 9 permission-denied entries
- Separately measured Apple libraries
- Storage that does not fully reconcile to total disk usage

The report is commendably transparent about exclusions.

**Recommendation:** Add a coverage breakdown showing accounted-for storage, excluded storage, inaccessible locations, and remaining unexplained usage.

**Why eighth:** This makes the results easier to trust and helps the AI identify where additional investigation may be valuable.

### 9. Replace opaque grades with useful condition indicators

**Finding:** The Mac receives a D, scoring 67/100.

Messages receives an F because it occupies 32.3 GB, even though the user wants to preserve that data.

The report also implies insufficient free disk space is responsible for poor performance without independently establishing that relationship.

**Recommendation:** Separate disk capacity warnings from performance diagnoses.

Make grading rules transparent and adapt recommendations to user preservation preferences.

**Why ninth:** Users need understandable risks and actions more than a letter grade.

### 10. Benchmark Ask Dad against Codex

**Finding:** The storage scan took 165.38 seconds, approximately 2 minutes 45 seconds.

My earlier estimate of 5–15 minutes saved by Ask Dad was speculative and did not include scan runtime.

**Recommendation:** Measure complete execution time and compare results against a local Codex agent under controlled conditions.

**Why tenth:** A successful benchmark would help establish product differentiation, but the correctness and safety problems should be fixed first.

---

# 2. Scanner Capabilities and Coverage

The report contains substantial diagnostic information.

### 1. Disk capacity

- Total: 250.7 GB
- Used: 226.9 GB
- Available: 23.8 GB
- Utilization: approximately 90.5%

The computer has relatively little free disk capacity.

### 2. Scanner runtime

**165.38 seconds.**

This must be included in all end-to-end performance comparisons.

### 3. Folder inventory

The scanner produced 60 ranked folder entries.

These include user folders, application support directories, music libraries, and system-related paths.

They are not necessarily 60 independent cleanup opportunities.

### 4. File inventory

The scanner produced 500 large-file entries.

Some application bundles are represented alongside ordinary files.

### 5. Hidden storage

The scanner measured 224 hidden cache/log folders totaling approximately 25.34 GB.

This is useful discovery work, although the category includes some non-cache data.

### 6. Trash

8.012 GB in three items.

This is a potentially important recovery opportunity, subject to inspection and approval.

### 7. Apple libraries

Messages: 32.35 GB  
Mail: 1.46 GB

Photos and Music are also measured separately.

### 8. Snapshot discovery

One local Time Machine snapshot, approximately 247 days old.

No reliable reclaimable size is provided.

### 9. Coverage limitations

6,153 exclusions and nine permission-denied entries.

These should remain explicit in every report.

### 10. Overall assessment

The scanner goes considerably beyond checking Downloads and finding large applications.

Its discovery coverage is valuable, even though its output requires more rigorous accounting and classification.

---

# 3. Cleanup Opportunities Found on This Mac

The following is my subjective priority order, incorporating the user's stated preferences.

These entries are not a list of approved deletions.

### 1. Existing Trash — 8.0 GB

**Recommendation:** Inspect the three items individually, restore anything important, then decide whether to empty Trash.

**Classification:** Review before acting.

This is a potentially straightforward recovery opportunity, but final emptying is irreversible.

### 2. Omarchy ISO — 6.2 GB

**Recommendation:** Archive to external storage or cloud storage, verify the copy, and then optionally move the local installer to Trash.

**Classification:** Back up first.

The user explicitly selected project archiving.

### 3. Downloaded application installers — at least 1.32 GB identified

Examples include ChatGPT, Claude, and Obsidian DMG files.

**Recommendation:** Confirm that these installers aren't needed for offline installation or version preservation.

**Classification:** Review, then potentially Move to Trash.

Installed applications are unaffected by removing unrelated downloaded installer copies.

### 4. Zoom recordings/material — approximately 3.2 GB

**Recommendation:** Identify and preview the content. Back up valuable recordings before considering removal.

**Classification:** Back up first.

These may contain unique recordings and must not be treated as disposable simply because they are large.

### 5. Other Downloads

**Recommendation:** Review large archives, videos, and installation packages individually.

**Classification:** Review.

There is insufficient evidence to assign a reliable reclaimable total.

### 6. npm cache — 2.0 GB

**Recommendation:** Inspect using npm's supported maintenance commands.

**Classification:** Supported cache maintenance only, with separate approval.

Packages may need downloading again.

### 7. Application and updater caches

**Recommendation:** Identify the owning applications and use supported cache-clearing methods.

**Classification:** Investigate.

The full cache size should not be advertised as safely recoverable.

### 8. `~/.local` — 1.5 GB

**Recommendation:** Leave untouched until the directory's contents are understood.

**Classification:** Keep / Investigate.

This folder may include executable programs and valuable application data.

### 9. Messages and its cache

Messages library: 32.3 GB  
Reported Messages cache: 8.5 GB

**Recommendation:** Preserve both pending deeper inspection.

**Classification:** Keep.

The user's preservation preference overrides the size-based ranking.

### 10. Ableton and music production libraries

**Recommendation:** Preserve all installed instruments, plugins, sample libraries, and music production applications.

**Classification:** Keep.

The report identifies many large files in this category, but they are not suitable cleanup targets under the user's preferences.

**Important accounting limitation:** These entries must not be summed indiscriminately. Parent folders, nested files, caches, and Downloads may overlap.

The 8.0 GB of Trash plus the 6.2 GB Omarchy installer represent approximately **14.2 GB of nominal candidates**, not guaranteed physical recovery.

---

# 4. Ask Dad Versus a Local Codex Agent

A capable local Codex agent can independently gather much of this information using `df`, `du`, `find`, `diskutil`, `tmutil`, and application-specific tools.

Ask Dad does not have exclusive access to the underlying macOS information.

Its potential value is how systematically and safely it collects and organizes that information.

### 1. Repeatability — Ask Dad advantage

A deterministic scanner follows the same discovery procedure each time.

An agent may choose different commands and investigative paths across repeated runs.

This matters for consistent product behavior.

### 2. Discovery coverage — likely Ask Dad advantage

Ask Dad checks several locations a naive agent could overlook, including hidden development caches and application-specific storage.

A capable agent could achieve similar coverage with an appropriate diagnostic script.

### 3. Safety workflow — potential Ask Dad advantage

The structured prompt asks users what they want to preserve and emphasizes approvals.

However, prompt instructions alone cannot enforce filesystem permissions.

A production tool should have explicit safeguards around execution.

### 4. Diagnostic flexibility — Codex advantage

Codex can investigate unusual folders, run additional commands, and change its approach based on what it discovers.

Ask Dad is limited to its predefined scanner capabilities unless extended.

### 5. Execution speed — unproven

Ask Dad takes approximately 165 seconds to scan storage.

An optimized local agent could potentially finish a targeted investigation more quickly.

There is no measured speed winner yet.

### 6. Cleanup plan quality — unproven

The condensed AI prompt overlooks some useful candidates contained in Ask Dad's complete JSON.

Improving the handoff could materially improve resulting plans.

### 7. Privacy — design-dependent

Ask Dad performs local discovery, which is promising.

But exporting complete file paths to a cloud model may expose unnecessary personal information.

### 8. Overall product differentiation — promising

A predictable, approval-based diagnostic workflow may be valuable to users who do not want to manage agent commands or understand macOS internals.

The strongest differentiation will likely come from reliable discovery, safe classifications, and understandable recommendations.

---

# 5. Benchmark Design

I recommend testing Ask Dad against Codex using the same disk state, user preferences, model version, permissions, and output requirements.

Run at least five repetitions of each condition.

## Experiment Conditions

### 1. Naive Codex

Prompt:

“Clean up my Mac. Propose a plan. Don't change anything without permission.”

Allow read-only filesystem inspection.

### 2. Guided Codex

Give Codex the detailed safety prompt and the same user preservation preferences, but no Ask Dad diagnostic report.

This isolates the value of the prompt.

### 3. Ask Dad + Codex

Supply the safety prompt, user preferences, and scanner output.

Include the scanner's 165-second execution time.

This tests the incremental value of deterministic discovery.

### 4. Optional generic-scanner baseline

Give Codex a structured inventory produced by an existing filesystem analysis tool.

This distinguishes the value of Ask Dad specifically from the general value of precomputed data.

## Evaluation Metrics — In Priority Order

### 1. Unsafe recommendation rate

Measure how often each approach suggests removing protected, unique, or important data.

Serious safety failures should invalidate a run regardless of speed.

### 2. Safe opportunity recall

Measure what percentage of independently verified, user-eligible cleanup opportunities the system discovers.

### 3. Verified recoverable storage

Measure unique, eligible space identified by each approach.

Keep nominal file sizes separate from actual measured physical recovery.

### 4. End-to-end completion time

Include scanning, reasoning, command execution, prompt assembly, user questions, and plan preparation.

### 5. Accounting accuracy

Compare estimated recovery against actual observed disk-space gains in a controlled, restorable environment.

### 6. User effort

Count required decisions, clarification questions, and time spent reviewing the cleanup plan.

### 7. Discovery precision

Measure how many recommended candidates are genuinely eligible for removal under the user's preferences.

### 8. Coverage

Measure whether the system inspected the relevant categories and acknowledged inaccessible areas.

### 9. Repeatability

Measure variation in discovery and recommendations across runs using equivalent conditions.

### 10. Computational cost

Measure token usage, agent tool calls, CPU/I/O utilization, and API-equivalent cost.

### 11. Privacy exposure

Measure how many unnecessary filenames, file paths, and sensitive metadata fields leave the local computer.

## Suggested Benchmark Calculations

```text
Speedup =
  Naive agent total time /
  Ask Dad total time

Time saved =
  Naive agent total time -
  Ask Dad total time

Safe recovery rate =
  Validated reclaimable GB /
  Total elapsed minutes
```

The key principle is to measure safety, completeness, and time together.

An agent that produces a cleanup plan quickly but misses significant safe opportunities is not necessarily better.

**Ground truth must be established independently of Ask Dad.** Otherwise the evaluation will favor its own discoveries.

---

# 6. Product Strategy

## Recommended Initial Positioning

“Ask Dad inventories Mac storage locally, identifies useful cleanup opportunities, and prepares a safe, approval-based plan for an AI assistant.”

This is a credible positioning statement that does not depend on unproven speed or accuracy claims.

## Product Development Sequence

### 1. Read-only diagnostic product

Deliver accurate, understandable storage findings, actionable classifications, user preservation preferences, and privacy-conscious AI handoffs.

### 2. Guided cleanup workflow

Introduce per-item review, backup verification, explicit approvals, and measurement of actual storage recovered.

### 3. Optional execution capability

Consider permissioned cleanup automation only after safety and recoverability are established.

Prefer reversible operations wherever possible.

Make non-reversible procedures clearly distinguishable from ordinary Move to Trash actions.

---

# 7. Final Assessment

Ask Dad's full storage scanner is substantially more valuable than the brief prompt alone suggests.

It discovers meaningful data across user folders, hidden storage, applications, developer tools, Apple libraries, and APFS snapshots.

However, three issues currently weaken its product claims:

1. Reclaimable-space estimates aren't sufficiently traceable.
2. Some application data is classified too broadly as cache.
3. The condensed AI handoff fails to highlight some of the most actionable candidates already present in the scanner's inventory.

The reported **165-second runtime** also prevents a credible speed advantage from being assumed.

## Recommended Next Milestone

My preferred order of work is:

1. Correct recovery estimates and unsafe classifications.
2. Reconcile folder totals and parent-child relationships.
3. Improve actionable candidate prioritization.
4. Itemize Trash and improve review workflows.
5. Make AI exports private by default.
6. Run the controlled Codex comparison.

**Commercial judgment:** Ask Dad is worth developing further as a local diagnostic and AI-assisted cleanup product. The first proof point should be whether it finds more safely recoverable space, with fewer unsafe recommendations and less user effort, than a generic local agent.

No cleanup actions or changes to the user's Mac were performed during this assessment.
