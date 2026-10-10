# Ask Dad for Mac (Dad Ware) — Competitive Analysis

**Purpose:** Single source of truth for competitive positioning across both releases.
**Scope:**
- **V1 (CLI release):** Free Python CLI tool (`askdad`) that produces graded, personality-driven HTML report cards, with an agent-friendly output path on the roadmap.
- **Future commercial Mac app:** Native GUI product competing in the consumer storage/cleaner market.

**Core positioning:** Ask Dad is an **advisor**, not an instrument and not a cleaner. It interprets Mac-specific data, explains what things mean in plain language, grades health, and recommends next steps — especially for non-technical and younger users. It is **read-only by design**: it never deletes, moves, or changes anything. Every recommendation is advice the user carries out themselves; that is the product's core trust promise. As consumer agents take over the *doing*, that constraint is being re-read as the product's thesis rather than its limit — see §7.1.

**Last updated:** September 2026

---

## 1. Product Positioning Summary

| Dimension | Ask Dad |
|-----------|---------|
| **Core promise** | "Is my Mac healthy, and what should I do about it?" |
| **User** | Anyone with a Mac who wants clear guidance (primary focus: non-technical / younger users) |
| **Output model** | Graded report card + plain-language explanations + actionable advice + personality |
| **Interaction** | Run scan → read interpreted report → take (or ignore) recommended actions yourself |
| **Key differentiator** | Interpretation + Mac-specific knowledge + explanation quality, not raw data or automation |
| **Trust posture** | 100% read-only — advises, never deletes; cleanup decisions stay with the user |
| **V1 form factor** | Python CLI (stdlib only) + shareable self-contained HTML report + JSON manifest per scan |
| **Future form factor** | Native Mac app with the same advisory philosophy |

**Instruments vs Advisor (foundational framing)**

Tools like ncdu and htop are *instruments*: they surface raw data and assume the user knows how to interpret and act. Ask Dad is an *advisor*: it collects similar underlying data, then grades it, explains Mac-specific meaning (Photos libraries, iPhone backups, Time Machine, Messages, Mail, etc.), and tells the user what matters and what to consider doing about it.

This distinction is the central strategic axis for both the CLI and the eventual GUI product.

---

## 2. Competitive Landscape Overview

The competitive field splits into two overlapping but distinct arenas that matter at different stages of the product.

### Arena A — CLI / Power-Tool Competitors (Primary for V1)

These are the tools a technical or semi-technical user might already reach for when storage or performance feels wrong.

| | ncdu | htop | Ask Dad |
|---|---|---|---|
| **Problem it solves** | "Where is my disk space going?" | "What's using CPU/RAM right now?" | "Is my Mac healthy, and what should I do about it?" |
| **User** | Developer who knows what to delete | Developer debugging a performance issue | Anyone with a Mac who wants guidance |
| **Output** | Interactive file browser | Interactive process list | Report card with grades, advice, and a personality |
| **Requires knowledge** | You need to know what's safe to delete | You need to know which processes matter | It tells you what matters |
| **Interaction model** | Navigate and drill down in real time | Watch and kill processes in real time | Run scan, read report, take action offline |

**What these tools do that Ask Dad (CLI) does not (by design):**
- Real-time interactive navigation / live process control
- Direct deletion or kill from the UI
- Cross-platform Unix generality

**What Ask Dad does that they do not:**
- Letter-grade health scoring (A–F, weighted composite — see `docs/GRADING.md`)
- Mac-specific identification and explanation (Photos, Mail, Music, Messages, Time Machine libraries, iPhone backups)
- Plain-language guidance on what things are and what's reasonable to do about them
- Personality-driven, shareable, fully self-contained HTML report
- Storage and memory/CPU scans in one tool (`all` runs both through the same flow)
- An LLM-ready "Consult AI" prompt built from the scan (`utils/llm_prompt.py`), with structured agent output as a natural next step

#### ncdu — detail

ncdu is a disk usage explorer. You navigate a tree of folders sorted by size. It's extremely good at what it does, but it assumes you know what you're looking at. If someone sees `/Users/dad/Library/Application Support/MobileSync/Backup` taking 40GB, ncdu shows you the number — it doesn't tell you "those are your old iPhone backups, and here's how to manage them." No grading, no advice, no shareable interpreted report.

#### htop — detail

htop is best-in-class real-time process monitoring with sorting, filtering, and the ability to send signals (kill, nice, etc.). It's a power tool for people who already understand processes. Ask Dad's value is the opposite: group processes by app (Chrome's total across 47 helper processes), grade the overall memory situation, and give plain advice ("Chrome is using 4.2 GB — consider closing tabs") rather than live control.

**Strategic takeaway for CLI V1:** Do not try to out-ncdu ncdu or out-htop htop. The overlap is in data collection; the differentiation is interpretation and presentation. Win on Mac knowledge and the advisor experience delivered via the HTML report and, later, structured output.

### Arena B — Consumer Mac Storage & Cleaner Market (Critical for GUI release; relevant for messaging now)

This is the market non-technical users actually search and pay in.

| Cluster | Description | Typical pricing | Key players |
|---------|-------------|-----------------|-------------|
| All-in-one cleaners | Junk + large files + uninstaller + often malware/performance | Mostly subscription ($30–45/yr) | **CleanMyMac**, MacBooster, MacKeeper, MacCleaner Pro |
| Visual disk analyzers | Beautiful maps of where space went; mostly manual delete | One-time ($10–20) or free | **DaisyDisk**, GrandPerspective, OmniDiskSweeper |
| Safety-first / focused cleaners | Calmer UI, Trash-first, stronger explanations | Free + one-time or light sub | **Sweep for Mac**, various MacSweep / DiskCleaner-style tools |
| Free / power-user tools | Maintenance scripts, lists, treemaps | Free | OnyX, AppCleaner, Disk Inventory X, GrandPerspective |
| Niche | Duplicates, developer caches, recovery | Mixed | Gemini, WhatSize, Disk Drill, open-source variants |

**CleanMyMac** is the dominant commercial reference point for brand awareness and paid search.
**DaisyDisk** owns the pure "where did my space go?" visualization mindshare.
**Sweep** and similar tools are the closest in tone (explanation + safety) to Ask Dad's advisory stance.

---

### Arena C — Free, Built-In, and Manual Methods (the real default)

Forum research on MacRumors (the CleanMyMac "snake oil" thread plus ~10 adjacent
storage threads) shows that most people never buy a cleaner. They use a built-in
macOS feature, one Terminal command, or nothing at all. Ask Dad V1 is free, so
these — not CleanMyMac — are its true competitive set.

| Method | What it is | Where it wins | Where it fails the target user |
|---|---|---|---|
| **About This Mac → Storage → Manage** | Apple's own panel: Store in iCloud, Optimize Storage, Empty Trash Automatically, Reduce Clutter, built-in Large Files and Downloads browser | Free, pre-installed, first stop for every non-technical user | Buckets everything confusing into "System Data" and explains nothing |
| **"Do nothing"** | The most common forum verdict: "Macs don't generally need routine maintenance"; cleaner apps are "mildly useless at best, if not outright scams at worst" | Often correct. Costs nothing. Carries real advocates | Gives the worried user no way to confirm they are fine |
| **Disk Utility → View → Show APFS Snapshots** | Delete snapshots with the minus button | Free, built in, the fix the forums actually prescribe | Undiscoverable. Nobody finds it without being told |
| **Finder folder sizes** (Cmd+J → Calculate all sizes) | Per-folder sizes in list view | No install | Slow, manual, one folder at a time |
| **Finder Smart Folders / search by file size** | Built-in large-file finding | No install | Requires knowing the search-attribute UI exists |
| **`sudo du -d 1 -x -c -g ~/`** | Raw per-folder totals | Free, exact, scriptable | Numbers with no meaning attached |
| **`tmutil` family** — `thinlocalsnapshots`, `deletelocalsnapshots`, `thinlocalbackups` | Reclaim snapshot space | The forums' most-reported big win (e.g. System Data 189GB → 42GB) | Terminal, `sudo`, and destructive if misused |
| **`xcrun simctl delete unavailable`** | Removes stale Xcode simulator runtimes | Recovers 50–80GB in forum reports | Developers only |
| **Photos → Optimize Mac Storage / iCloud Drive → Optimize Storage** | Offload originals to iCloud | Reclaims a lot without deleting | Users do not trust it, and do not understand what stays local |
| **Restart / Safe Mode** | Triggers a purge pass | Free, one step | Frequently does nothing, which deepens the confusion |
| **Move a library to an external drive** | Relocate Photos, Music, or backups | Keeps the data | Manual, error-prone, no guidance on what is safe to move |

**Delayed-delete holding areas** are a category of their own and the source of most
"I deleted it and nothing changed" reports: Trash, per-app trashes, Photos
Recently Deleted (30 days), iCloud's multi-day hold, and APFS snapshots. See §5.1.

**Strategic takeaway:** the matrix in §4 compares Ask Dad to products people *buy*.
Most of the market never buys. Ask Dad's honest competition is Apple's own Storage
panel, a `du` command, and a shrug — and Ask Dad beats all three on the same axis:
it says what the numbers *mean*.

---

## 3. Detailed Competitor Notes (Consumer Layer)

**CleanMyMac (MacPaw)**
- Positioning: Polished all-in-one "Smart Care" + Space Lens + malware + performance.
- Strengths: Brand, breadth, Apple-notarized, explicit Time Machine local snapshot thinning.
- Weaknesses: Subscription model creates fatigue; can feel heavy or overly automated for users who mainly want to *understand*.
- Relevance: Primary long-term commercial competitor. Users will compare any Mac storage product to it.

**DaisyDisk**
- Positioning: Best-in-class sunburst / interactive map. Manual control.
- Strengths: Speed, clarity of visualization, one-time purchase (~$10), high user affection.
- Weaknesses: Little automatic cleaning, limited education about *why* space is occupied (especially snapshots / purgeable space / Mac libraries).
- Relevance: Strong for discovery keywords. Many users start here and later want guidance.

**Sweep for Mac**
- Positioning: Calm, safety-first cleaner with explanations and privacy tools.
- Strengths: Content that directly addresses Time Machine snapshots and storage mysteries; lighter feel than CleanMyMac.
- Weaknesses: Smaller brand and less complete feature surface.
- Relevance: Closest tonal competitor on the "explain + safe" axis. Monitor messaging closely.

**Pearcleaner**
- Positioning: Open-source app uninstaller and leftover finder; a modern AppCleaner.
- Strengths: Free, open source, actively recommended over AppCleaner in current
  round-ups, and finds remnants of apps already removed.
- Relevance: Sets the free-tool quality bar. Open source plus free is now the
  default expectation in this niche, which validates Ask Dad V1's licence choice.

**Mole / Mole CLI**
- Positioning: Open-source command-line Mac cleaner for users who prefer the Terminal.
- Strengths: Same form factor as Ask Dad V1 — free, open source, CLI, no GUI tax.
  Emphasises visibility and automation.
- Weaknesses: It cleans, so it carries the deletion risk Ask Dad deliberately avoids.
  No grading, no interpretation, no shareable report.
- Relevance: **The closest direct competitor to Ask Dad V1 by form factor**, and the
  one to monitor most closely. The differentiation is unchanged — Mole is an
  instrument that acts; Ask Dad is an advisor that explains.

**Other frequent players**
- GrandPerspective / OmniDiskSweeper / Disk Inventory X — free visual or list analyzers.
- OnyX — free power-user maintenance (not beginner-friendly).
- AppCleaner — excellent free app leftover removal.
- MacBooster / MacKeeper / similar — all-in-one subscription competitors in the same SERPs, often lower trust.
- Emerging one-time or freemium tools (various MacSweep, DiskCleaner, AI-assisted cleaners) that emphasize safety or developer caches as differentiators against CleanMyMac's subscription model.

---

## 4. Competitive Positioning Matrix

| Dimension | ncdu / htop | CleanMyMac | DaisyDisk | Sweep-style | **Ask Dad opportunity** |
|-----------|-------------|------------|-----------|-------------|--------------------------|
| Raw data exploration | Excellent | Medium | Excellent (visual) | Medium | Not the goal |
| Interpretation & grading | None | Medium (Smart Care) | Low | Medium–High | **Core strength** |
| Mac-specific explanations | None | Partial | Low | Higher (content) | **High priority** (snapshots, backups, Photos, etc.) |
| Beginner / non-technical friendliness | Low | Medium | Medium | Higher | **Primary target** |
| Time Machine local snapshots | None (user must know `tmutil`) | Explicit thinning | Indirect | Content + tools | Explanation + graded, copy-pasteable advice (read-only; see `docs/roadmap/HIDDEN-STORAGE-PLAN.md`) |
| Safety / "won't delete the wrong thing" | User responsibility | Generally high brand | High (manual) | Emphasized | **Structural**: read-only by design — the tool *cannot* delete the wrong thing |
| Pricing model | Free | Subscription | One-time | Free / one-time leaning | V1 free (MIT); GUI flexible — avoid pure heavy sub for younger users |
| Shareable / advisor report | None | Limited | None | Limited | Strong (self-contained HTML report + personality) |
| Agent / structured output | None / raw | None | None | None | Natural extension of CLI V1 (see §6) |
| Form factor | CLI | GUI app | GUI app | GUI app | CLI first → native Mac app later |

---

### 4.1 Tools Named in the Forums (coverage check)

Added after the MacRumors review. Everything below is something real users name
unprompted when someone asks where their space went.

| Tool | Type | Status in this doc |
|---|---|---|
| DaisyDisk, GrandPerspective, OmniDiskSweeper, Disk Inventory X, WhatSize, ncdu | Analyzers | Covered (§2, §4) |
| **JDiskReport** | Analyzer | Newly added. Minor, but appears in the standard forum list |
| AppCleaner | Uninstaller | Covered |
| **Pearcleaner** | Uninstaller, open source | Newly added — see §3 |
| **An app's own bundled uninstaller** | Uninstaller | Newly added. The first thing forums tell people to check |
| OnyX | Maintenance | Covered |
| **Mole / Mole CLI** | Terminal cleaner, open source | Newly added — see §3. Closest form-factor competitor to Ask Dad V1 |
| Gemini | Duplicates | Covered |

**Space hogs the forums name repeatedly:** Time Machine local snapshots and
"System Data"; purgeable space; `~/Library/Application Support/MobileSync/Backup`
(iPhone backups, often for devices the user no longer owns); Mail downloads;
Photos, Music and Messages libraries; `~/Library/Developer` — Xcode DerivedData
and CoreSimulator runtimes; Docker and other sparse disk images.

Note: Xcode and developer caches appear in §3 only as a *competitor's*
differentiator. They should be a target. The scanner already reads
`~/Library/Caches` and sizes sparse and Docker files accurately, so this
capability largely exists and is simply unclaimed.

**Apple Intelligence is now part of the problem.** The on-device models occupy
roughly 4–7GB under `/System/Library/AssetsV2/`, macOS counts them as System Data,
there is no supported way to remove them short of turning the feature off, and the
user cannot trigger reclamation manually. Apple's newest feature made the
"System Data is huge" confusion worse, not better. That is a durable opening.

---

## 5. Time Machine Local Snapshots & Hidden Space — Cross-Cutting Opportunity

Local APFS snapshots created by Time Machine (while "Back Up Automatically" is enabled) are a high-friction, poorly understood source of "missing" space. They use copy-on-write, are treated as purgeable by the system, and frequently confuse non-technical users — "I deleted a bunch of stuff. Nothing changed."

| Player | Handling |
|--------|----------|
| CleanMyMac | Explicit thinning tool |
| DaisyDisk | Can surface space but does not specialize in explanation or management |
| Sweep | Strong educational content + practical guidance |
| Built-in macOS | Automatic purge under pressure; Disk Utility; opaque to beginners |
| Most free analyzers | Little or none (users end up in Terminal) |
| **Ask Dad** | Own the plain-language explanation + graded recommendation layer — advice with labeled, copy-pasteable commands (e.g. `tmutil thinlocalsnapshots`), never a thin/delete button |

This topic is especially valuable for the non-technical audience because the behavior is counter-intuitive (space "disappears" or "reappears") and most tools either ignore it or treat it as an advanced feature. Note the deliberate constraint: the repo's roadmap **considered and rejected** in-app thinning to protect the read-only trust story (which also underpins the permissions strategy). Ask Dad competes on *explanation*, not on performing the cleanup.

**Companion documents:** `docs/roadmap/HIDDEN-STORAGE-PLAN.md` (app caches, purgeable space, snapshots, Trash — the product requirements for this module) and `docs/roadmap/PERMISSIONS-PLAN.md` (Full Disk Access strategy it depends on).

---

### 5.1 The Phantom Space Problem (the complaint behind the complaints)

Forum thread titles are the clearest statement of user need available:

- "I deleted 80gb, but I still have the same storage space"
- "Not regaining used space when deleting files. DaisyDisk says 180 GB of hidden space"
- "Disk full, but I can't delete any files because my disk is full"
- "Where are all these files? (I already used a disk sweeper)"
- "System Data HUGE - 700GB. Help!"

The recurring complaint is almost never "I cannot find large files." Tools for that
are free and plentiful. The complaint is **"I deleted things and nothing changed."**

The fourth title is the most valuable one in this document. A disk sweeper ran, and
the user is still lost. That is the hand-off point where an explanation layer earns
its place, and no existing tool serves it.

Causes, all of which look identical to a non-technical user:

| Cause | Why the space does not come back |
|---|---|
| APFS / Time Machine local snapshots | Copy-on-write keeps deleted files alive inside snapshots |
| Purgeable space | Reserved by the system; reclaimed on its own schedule, not the user's |
| Trash and per-app trashes | Not actually deleted yet |
| Photos Recently Deleted | 30-day hold |
| iCloud deletions | Multi-day hold as a safety measure |
| Apple Intelligence model assets | Counted as System Data, not user-removable |

§5 covers snapshots well. This section widens the frame: **delayed deletion is the
category**, and snapshots are only its largest member. Treat the whole set as one
educational module and one grading input.

---

## 6. Agent Strategy — The Advisor as Infrastructure

"Help me fix my slow Mac" is one of the most common requests people bring to AI assistants, and right now those assistants are guessing blind. Ask Dad can give them eyes — and neither classic cleaners nor pure instruments own this today. An agent calling ncdu gets raw numbers; an agent calling Ask Dad gets graded, interpreted, Mac-specific analysis with recommendations already attached.

The groundwork already exists: `utils/llm_prompt.py` generates a structured prompt with system specs, scan results, and pre-written questions, surfaced as the HTML report's "Consult AI" section that users copy/paste into ChatGPT or Claude. That's a manual agent workflow — the user is the glue between Ask Dad and an LLM. Each scan also already saves a JSON manifest alongside the HTML report. The evolution path inverts the flow so the agent calls Ask Dad as a tool:

**Tier 1: Structured output (low effort, high value) — build first.**
A `--json` flag that writes scan results as clean JSON to stdout. Any agent or MCP tool can call `askdad --json`, parse the results, and reason about them. A few hours of work, it makes everything else possible, and it doesn't change the existing UX.

**Tier 2: MCP tool (medium effort, very high value).**
Ask Dad as an MCP server that agents like Claude Code call directly: `scan_storage` returns structured results, and the agent answers "Your disk is 94% full. The biggest thing is 38GB of old iPhone backups in..." — no copy/paste required.

**Tier 3: The prompt is the product.**
A `--prompt` flag that outputs just the LLM-ready prompt, so any agent helping with Mac issues can run one command and get rich, pre-interpreted context.

The scanning, grading, and interpretation logic — the hard part — is already built; the prompt generator proves the concept. Structured output and eventual MCP support turn the interpretation layer into infrastructure other agents can use, a differentiator orthogonal to both arenas. Validate Tier 1 before investing in Tiers 2–3.

---

## 7. Implications by Release

### V1 — CLI + HTML Report (Now)

**Primary competitive frame:** Instruments (ncdu, htop) vs Advisor.
**Win by:**
- Mac-specific identification and explanation
- Letter grades and clear recommendations
- Personality and the shareable, self-contained HTML report
- Shipping the Tier 1 `--json` output (low-effort, high-leverage)

**Do not over-index on:**
- Trying to match interactive real-time UIs
- Full consumer-cleaner feature parity
- Any deletion automation — it contradicts the read-only trust promise

**Messaging angle that works now:**
"This is not another ncdu. It tells you what the big folders *mean* on a Mac and what to do about them — and it can't delete anything, so a kid can run it."

### Future Commercial Mac App

**Primary competitive frame:** Consumer cleaners (CleanMyMac, DaisyDisk, Sweep-style).
**Win by:**
- Carrying the same advisory / explanatory DNA into a polished GUI
- Superior handling of confusing Mac-specific issues (especially local snapshots and purgeable space)
- Trust and safety posture tuned for non-technical users
- More flexible pricing than pure subscription all-in-ones
- Big-file finding + archiving recommendations as a coherent story alongside cleanup

**Key risks to manage:**
- Being seen as "just another CleanMyMac"
- Losing the explanatory clarity that is the CLI's strength when adding automation — if the GUI ever performs cleanup actions, that is a deliberate departure from the CLI's read-only promise and must be decided (and messaged) explicitly, not drifted into
- Subscription fatigue among the younger audience

**Positioning options to test:**
1. "The clearer, safer storage advisor for people who aren't IT"
2. "Big files + archiving + the hidden space problems other cleaners don't explain well"
3. "CleanMyMac alternative that actually tells you *why* before you clean"

---

### 7.1 Positioning Alternatives (open, not yet decided)

Context for this section: consumer agents are moving toward doing file maintenance
on the user's behalf. That commoditizes the *doing*. Every cleaner on the market
sells the doing, which puts the whole category on the wrong side of the shift.

Apple has not shipped agentic file maintenance as of macOS Tahoe. It has not
shipped a button to remove Apple Intelligence's own model assets. Apple's
consistent instinct is to hide the mechanism, automate the decision, and explain
nothing — which is precisely what produces the forum threads in §5.1. An Apple
agent will likely inherit that instinct: it will clean silently and explain
nothing. The explanation gap therefore does not close. It widens.

**The unifying insight.** A twelve-year-old and a language model need the same
thing from a disk scanner. Give either the output of `du -d 1 -x ~/` and both fail
the same way — neither has priors about what a Mac's folders mean. Neither knows
that `MobileSync/Backup` is old iPhone backups, that 40GB there is abnormal, or
what is safe to do about it. Both need interpretation, not numbers.

Competitors sell the doing. Instruments (ncdu, the macOS system-monitor MCP
servers) sell the numbers. Nobody sells the judgment. One interpretation engine,
two output formats — one written for a kid, one written for a model.

Three candidate positions follow. They are compatible; the question is which one
leads.

**Option A — The report card (education).**

> A good dad doesn't clean your room for you. He shows you what a clean room looks
> like, and why it matters.

Read-only stops being a constraint to apologize for and becomes the point of the
brand metaphor. A tool that cleans for you is a maid. A tool that grades you and
explains why is a parent. The letter grade is a teaching device: it implies a
student who can improve.

This reframes the "Safety" row in §4. "Won't delete the wrong thing" is a
defensive feature. "Won't do it *for* you, on purpose" is a philosophy.

*Candidate lines:* "Ask Dad doesn't clean your Mac. It teaches you how." /
"A good dad doesn't clean your room for you."

**Option B — Eyes for the agent (harness).**

The 2026 agent-CLI design language is settled: run unattended, speak JSON, ship an
MCP server or skill. The §6 roadmap already matches it. Two claims are not yet
made anywhere in this document:

1. **Read-only means zero blast radius.** An autonomous agent can be handed
   `askdad` and cannot destroy anything. No cleaner on the market can say this. For
   agent adoption it is not a nice property, it is the entry requirement — a tool
   with a delete function must be sandboxed, audited, or refused.
2. **The existing macOS MCP servers are instruments.** They return CPU, memory and
   disk numbers, so an agent reading them still guesses about Macs. `askdad --json`
   would be the only source returning graded, Mac-aware interpretation.

*Candidate line:* "Give your agent eyes. Not hands."

**Option C — The receipt (audit).**

When an agent does clean the Mac, something has to say what changed and whether it
was right. Read-only scan before, read-only scan after, plain-language diff.

This position grows more valuable as agents improve, which is the opposite of every
cleaner on the market. It is also the answer to "what happens when Apple ships
this?" — Ask Dad becomes the instrument panel and the agent becomes the autopilot.
Aircraft have both. Nobody removed the gauges.

**What changes if these are adopted**

| Current framing | Proposed framing |
|---|---|
| Read-only is a trust constraint | Read-only is the thesis — for the kid *and* for the agent |
| Advisor vs instrument | Judgment vs numbers vs doing. Agents take "doing"; Ask Dad takes "judgment" |
| Competing with CleanMyMac | Not competing. Cleaners are on the wrong side of the agent shift |
| Education as a side benefit | Education as the delivered experience |
| `--json` as roadmap Tier 1 | `--json` as the second half of the product |

**The hand-off is a feature, not an unfinished edge.** Ask Dad ends where judgment
begins, and the hand-off now has three targets: the user's own hands, an agent, or
a paste into an LLM. `utils/llm_prompt.py` already serves the third. Name the
pattern and design for it.

**Risks to weigh before committing**

1. *"Educational" is a bad thing to advertise.* Nobody wakes up wanting to learn
   about `~/Library`. They wake up with a full disk. Education must be what people
   get, never what is promised. `why is my mac so slow` is the door; the lesson is
   the room. A landing page that leads with "learn how macOS storage works" will
   have no visitors.
2. *The agent market pays nothing today.* It is a strategic position, not revenue.
   Ship `--json` because it is cheap and it makes the thesis real, but do not let
   MCP work outrank the human report card.
3. *"Dad" is warm, and narrow.* It plays well for a kid's first Mac and awkwardly
   for a 55-year-old photographer with a full drive. Open question: is the voice a
   wrapper that can vary, or is it the product? The grade may travel further than
   the dad.
4. *Category distrust is wider than this doc admits.* §3 flags MacKeeper as lower
   trust. The forums distrust the whole category, CleanMyMac included — "MacPaw has
   been guilty of some very aggressive marketing tactics, which speaks to their
   motivations." For a free, read-only, open-source tool that is an asset, and it
   is currently unclaimed.

---

## 8. Strategic Recommendations

1. **Maintain one competitive analysis document** (this file) until the native Mac app becomes an active workstream. Then consider splitting CLI-focused vs consumer-GUI-focused views if the audiences diverge sharply.

2. **For CLI V1, lean hard into the advisor identity.** The ncdu/htop contrast is the cleanest way to explain the product to early technical users, while the HTML report carries the value to non-technical recipients.

3. **Treat Time Machine local snapshots and "System Data / purgeable" confusion as a signature educational opportunity** in both releases (execution plan: `docs/roadmap/HIDDEN-STORAGE-PLAN.md`).

4. **Monitor continuously:**
   - CleanMyMac feature and pricing moves
   - DaisyDisk updates
   - Sweep and similar safety-first tools' content and messaging
   - New one-time-purchase or AI-assisted cleaners

5. **Keyword / acquisition implications (more relevant as the GUI approaches):**
   - "CleanMyMac alternatives", "Mac storage full", "System Data high", "Time Machine taking space", "find large files Mac", "DaisyDisk alternatives"
   - Educational content on snapshots and Mac libraries can capture users who later convert

6. **Ship the agent path incrementally** (§6): `--json` first, validate that agents use it, then MCP.

7. **Decide the lead position before the next campaign** (§7.1). Education, agent
   harness and audit are compatible, but only one can lead the landing page. Until
   that is settled, messaging will drift between "advisor", "teacher" and "tool for
   agents" and none of them will compound.

8. **Compete against free, not against CleanMyMac** (Arena C in §2). Ask Dad V1 is
   free, so its real rivals are Apple's Storage panel, a `du` command and "do
   nothing". Benchmark the report against those three, not against a $40/yr suite.

---

## 9. Quick Reference Tables

### Snapshot / Hidden Space Handling

| App / Tool | Local TM snapshots support | Notes |
|------------|---------------------------|-------|
| CleanMyMac | Yes — dedicated thinning | Most visible commercial solution |
| DaisyDisk | Indirect (visualization) | Does not specialize in explanation |
| Sweep for Mac | Content + practical tools | Strong educational angle |
| Built-in macOS | Automatic purge, plus Disk Utility → View → Show APFS Snapshots | The fix the forums prescribe, and undiscoverable without being told |
| ncdu / free analyzers | None / manual Terminal | User must already know what to do |
| **Ask Dad** | Planned: explanation + graded, copy-pasteable advice (read-only) | Own the "why + what to do" story; see `HIDDEN-STORAGE-PLAN.md` |

### Pricing & Model Snapshot (indicative, mid-2026)

| Player | Model | Approx. range |
|--------|-------|---------------|
| CleanMyMac | Subscription | ~$35–45/yr common |
| DaisyDisk | One-time | ~$10 |
| Sweep-style | Free / freemium / one-time leaning | Varies |
| Free analyzers (GrandPerspective, OmniDiskSweeper, etc.) | Free | — |
| Ask Dad V1 | Free, open source (MIT; "Ask Dad"/"DadWare" branding trademarked) | Zip download, `install.sh`, Homebrew formula |
| Ask Dad future GUI | TBD — flexibility is an advantage vs pure subscription | — |

---

## 10. Document Maintenance

- Re-validate competitor pricing, feature claims, and messaging before major launches or campaigns; treat specific numbers as snapshots that require re-checking.
- Update §7 as V1 ships and GUI work begins.
- §7.1 holds open positioning options, not decisions. Collapse it into §1 and §7 once a lead position is chosen.
- Arena C (§2), §4.1 and §5.1 came from MacRumors forum research (September 2026), read through search
  snippets across the CleanMyMac "snake oil" thread and ~10 adjacent storage threads. Re-validate against
  primary threads before quoting any of it externally.
- Keep capability claims in sync with the codebase: today the agent path (§6 Tiers 1–3) is roadmap, not shipped — the current interfaces are the HTML report, the saved JSON manifest, and the copy/paste "Consult AI" prompt.
- Related docs: `docs/roadmap/HIDDEN-STORAGE-PLAN.md`, `docs/roadmap/PERMISSIONS-PLAN.md`, `docs/roadmap/ASKDAD-RENAME-PLAN.md`, `docs/GRADING.md`.

---

*Synthesized from product research, public competitor materials, and internal positioning work as of August 2026.*
