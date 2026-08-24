# Competitor UX research: units, purgeable space, and cache safety

**Answers the research prompt in `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`.**
Researched 2026-08-24 via web sources. Written to unblock three `BACKLOG.md` decisions.

**Sourcing caveat, read first:** vendor sites (macpaw.com, daisydiskapp.com, sweep sites, forums.macrumors.com and others) could not be fetched directly from the research environment; quotes were captured through search-engine excerpts of the named pages. They are high-confidence reproductions but were not confirmed against fully rendered pages, and **no app was installed** — live on-screen numbers for CleanMyMac, DaisyDisk, and Sweep are inferred, not observed. Inferences are flagged inline. Verify quotes against the linked pages before reusing them in marketing.

**Second caveat — "Sweep" identity is ambiguous.** At least three products answer to the name: the guide-heavy cleaner at sweepformac.com, "Sweep – Disk Cleaner" at sweepdiskcleaner.com, and the unrelated "MacSweep" (macsweep.app, whose ecosystem shows signs of SEO clone spam). Findings below name which site each fact came from. None of their actual cleanup screens could be observed.

---

## 1. The three recommendations

### Decision 1 — Size units: switch to decimal (1000-based), keep the "GB" label. Match Finder.

**Straight answer: decimal.** A Finder-comparing, non-technical audience should see the same numbers Finder shows, full stop.

The evidence all points one way:

- **Decimal is the macOS platform convention and has been since Snow Leopard (2009).** Apple's `ByteCountFormatter` defaults to the `.file` style, which is decimal on macOS ("in macOS 10.8, this uses the decimal style") — so every native Mac app inherits Finder-matching numbers unless it goes out of its way not to. (developer.apple.com docs, verified; Apple support article 102119.)
- **DaisyDisk engineers its numbers to match Finder deliberately** — its manual's "Mismatches with Finder" page lists compression, hard links, and permissions as mismatch causes and never mentions units, and its purgeable-space guide says it includes purgeable in free space "exactly as Finder does." CleanMyMac's KB likewise explains number differences entirely via category definitions, never units. (Inference, high confidence: both display decimal.)
- **GrandPerspective is the documented existence proof of our exact problem.** It offers a Binary/Decimal preference and its help explicitly warns: "Finder uses the decimal unit system… when you scan using the binary unit system in GrandPerspective, the size reported by GrandPerspective will be smaller." (grandperspectiv.sourceforge.net, verified direct fetch, v3.7.2 May 2026.)
- **Binary-labeled-GB is the pattern of an abandoned app.** Disk Inventory X shows a 500 GB (decimal) drive as "465.6 GB" — the same ~7.4% understatement `format_size()` produces today — and the community fork's README exists partly because of its size formatting.
- **User confusion is real and recurring**: Apple Communities GiB-vs-GB threads, the MacRumors thread literally titled "Omni Disksweeper size does not equal what Mac says," Jamf's enterprise KB on the same 1000/1024 gap, and MacMost's explainer existing at all.
- No units *preference* is documented in any of the three commercial tools — they don't offer one because they don't need one. GrandPerspective's preference serves a power-user audience Dad Ware isn't targeting.

**Implementation notes:** `format_size()` in `utils/formatters.py` divides by 1024 and labels the result GB — change the divisor to 1000. `parse_size()` (used by `--min-size`) must move in lockstep, and grading thresholds in `scanners/grading.py` are expressed in GB, so a pass over thresholds and the test suite is part of the change. One nuance: memory figures (`vm_stat`, Activity Monitor) are natively binary; either keep the CPU report's RAM numbers binary with honest **GiB/MiB** labels, or accept a small mismatch with Activity Monitor — but disk sizes must be decimal GB. Never print binary math with a "GB" label anywhere again; that specific combination is the bug.

### Decision 2 — Purgeable & snapshots: don't chase Finder's number. Compute the gap, explain it, and never claim per-snapshot sizes.

Since no CLI source exposes `NSURLVolumeAvailableCapacityForImportantUsageKey` (verified in-repo; confirmed by this research — scan-only tools like OmniDiskSweeper don't show purgeable either), the recommendation is the **DaisyDisk-derived model**, which happens to be implementable in pure stdlib arithmetic:

1. **Report "space Dad can see is used but can't point at."** DaisyDisk's map shows a virtual **"hidden space"** item that expands into **"purgeable space"**, **"other volumes"**, and a residual called **"still hidden."** Dad Ware can do the honest version of the same thing: `statvfs` used-space minus the scanned total = an "unaccounted space" line item in the report, explained in plain language ("part of this is purgeable space and Time Machine snapshots — here's what those are"). We never need Finder's exact purgeable figure to explain why Finder's "available" is bigger than ours.
2. **Say explicitly that Finder's "available" number will look bigger.** OmniDiskSweeper's forum has to answer "why does OmniDiskSweeper report different amounts of free space than About This Mac?" — proof that a scan-only tool that stays silent gets the "your tool is broken" complaint. One sentence in the report ("Finder adds purgeable space to what it calls available; that space is already promised back to you") converts a trust-loss into a trust-win.
3. **List snapshots by name/date/count only — never per-snapshot sizes.** `tmutil listlocalsnapshots /` is unprivileged and gives names and dates. No credible tool claims accurate per-snapshot sizes: DaisyDisk (the only tool that lists snapshots with sizes at all, since v4.10, 2020) openly admits its figures are "displayed only for reference" because "snapshots share data blocks… after you delete one snapshot, the size of other snapshots may appear to have increased." Sweepformac's guide likewise explains a "10GB" snapshot figure is a change-delta, not a reclaimable amount. Dad Ware saying "3 snapshots, oldest from Tuesday — together they're most of your purgeable space" is both honest and more informative than a fake number.
4. **Frame the advice calmly, CleanMyMac-style reassurance without the button.** CleanMyMac ships snapshot thinning as a one-click Maintenance task ("shrinks those snapshots without affecting your backups"); OnyX deletes them for free. The *action* is a solved commodity — our value is the explanation plus the labeled, copy-pasteable `tmutil thinlocalsnapshots` command, framed the way DaisyDisk frames purgeable space: "in most cases you don't have to worry about it… it will be reclaimed automatically as needed," escalating to the command only when the user actually needs space now (e.g. a big download won't fit).

This also resolves the **BACKLOG Milestone 1 "validation spike"**: the research confirms there is nothing to find — no shipping tool reads purgeable from a CLI source. The spike's answer is the derived-gap arithmetic above, and item 1c should be reworded accordingly (see §5).

### Decision 3 — Cache safety: three verdicts per item, and never call a working cache "junk."

The tester's "these are all apps I actually use" reaction is the market's known unsolved problem: CleanMyMac's framing is binary (junk/protected), DaisyDisk offers honesty with zero guidance ("only delete the files that you can recognize… as those you have created or downloaded yourself"), and only fringe indie tools ship a graded label (macsweep.app claims "every scan result is labeled Safe, Review, or Do Not Delete"). Recommendation:

1. **Give every cache item one of three explicit verdicts:**
   - **Worth clearing** — genuinely stale: dead auto-updater downloads, caches of apps no longer installed, one-time installer leftovers. (This maps to what even MacPaw's defaults treat as unambiguous.)
   - **Safe but pointless** — working caches of apps in use: safe to clear, but "this comes back within a week, and the app's first launch gets slower." OnyX-adjacent docs contain the honest sentence the whole category avoids: "Deleted caches may have to be rebuilt, so an application can initially launch more slowly afterward."
   - **Leave alone / costly to clear** — the category CleanMyMac's own defaults secretly admit exists: its smart-select pre-checks user caches, system caches, and logs but **excludes "iOS device support files, archives, module caches, Xcode documentation cache, and available iOS simulators"** — i.e., exactly the items whose removal forces multi-GB re-downloads. MacPaw never explains that distinction in the UI; Dad Ware should say it out loud: "safe to delete, but you'd just re-download 4 GB."
2. **Per-item, name what the cache is NOT.** The reassurance that works is concrete: "Spotify's cache is not the app and not your playlists — it's streamed songs kept so they don't re-download." But get the facts right (see the correction in §5): Spotify's *offline downloads live in the cache folder*, so honest copy is "your playlists and account are untouched; songs downloaded for offline would need re-downloading." Same for browsers: clearing Arc's cache folder keeps tabs and logins; clearing *cookies/browser data* logs you out (the classic CCleaner burn: "logs you out of everything").
3. **Read-only reframes "default selection" as "default verdict."** Competitors' pre-checked boxes are their real risk statement (MacPaw: "Only the files that can be safely deleted are preselected"). Dad Ware's equivalent is which items get the "worth clearing" verdict — and it should be conservative for the same reason MacPaw excludes device-support files: a burned user never trusts the grade again. The burn evidence is concrete: a damaged Photos library ("CleanMyMac 3 messed up my photos library," Apple Communities), Spotify offline music vanishing after cache-cleaner runs (Spotify staff: "try disabling any power saving or cache clearing apps"), forced Xcode re-downloads.
4. **Borrow CleanMyMac's one good trust mechanic:** an explicit never-list. "Dad never even suggests touching your Documents, Photos, iCloud Drive, or anything you made." Ours is stronger — the tool *can't* touch them — but saying it in the report is what builds the trust.

---

## 2. Comparison table

| | CleanMyMac (MacPaw) | DaisyDisk | Sweep (all candidates) | Notable others |
|---|---|---|---|---|
| **Unit convention** | Decimal GB matching Finder (inferred, high conf. — KB never cites units as a mismatch cause) | Decimal GB matching Finder (inferred, high conf. — "Mismatches with Finder" page omits units; gauge matches Finder "exactly") | Unverified — no public evidence either way; plausibly decimal as modern native apps (low-mod conf.) | GrandPerspective: **user preference** Binary/Decimal, help warns binary "will be smaller" than Finder. Disk Inventory X: binary labeled GB (~7% off, abandoned) |
| **Purgeable space** | "Purgeable Space" item in Space Lens: "temporary system files that are removed automatically in case of need"; "Free Up Purgeable Space" Maintenance task | Richest model: included in free space "exactly as Finder does"; scan shows "hidden space" → "purgeable space" + "other volumes" + "still hidden" | sweepformac.com guides explain it well ("free space INCLUDES purgeable as available") — in-app handling unverified | OmniDiskSweeper: not shown; explains the Finder gap in a forum answer instead. GrandPerspective/DIX: nothing |
| **Local TM snapshots** | One-click "Time Machine Snapshot Thinning" task (not in App Store edition); "without affecting your backups"; no per-snapshot list found | Lists snapshots since v4.10 with **estimated sizes marked "for reference only"** + plain CoW explanation; deletion via a script the user pastes into Terminal | sweepformac.com guide: snapshot figures are change-deltas; thinning how-tos with expectation management — in-app handling unverified | OnyX: free "delete all local snapshots" (v3.7.1+), no thinning granularity, no purgeable figure |
| **Cache categorization** | Named categories (User/System Cache, Logs, Xcode Junk, Language Files…) — all framed as removable "junk"; no worth-it tiering | None — sunburst by size only; guidance lives in the manual ("only delete what you recognize as yours") | macsweep.app claims 3-tier "Safe / Review / Do Not Delete" (unverified in-app; low-trust ecosystem) | Nektony: 20k-app safety database, "Remaining Files" tab; no tiers |
| **Default selections** | Pre-checks everything found **except** iOS device support files, archives, module caches, Xcode doc cache, iOS simulators — the re-download-cost items, unexplained in UI | N/A — nothing ever selected; user drags items to a Collector manually | macsweep.app claims "conservative pre-selection… only confirmed-stale files"; others unknown | — |
| **Safety labeling** | Global, not per-item: "Safety Database", "100% safe for removal", Trash-first, review-before-delete, reveal-in-Finder | Blocks/warns on critical system files only; everything else is on the user | Marketing-level "you always see what's about to go" (sweepformac.com) | OnyX: no labels, power-user honesty in docs |

---

## 3. Quotes appendix (verbatim interface/doc copy)

All captured via search excerpts of the cited pages (see sourcing caveat); versions/dates as noted.

**Purgeable & snapshots**

| Quote | Source |
|---|---|
| "The purgeable space mostly consists of local snapshots of Time Machine, and also caches, sleep images, swap files and other temporary system files." | DaisyDisk v4 guide, PurgeableSpace |
| "In most cases you don't have to worry about it, and just let it be — it will be reclaimed automatically as needed." | DaisyDisk v4 guide, PurgeableSpace |
| "Snapshots share data blocks between each other… after you delete one snapshot, the size of other snapshots may appear to have increased… snapshots' sizes are displayed only for reference." | DaisyDisk v4 guide, Snapshots (feature added v4.10, Mar 2020) |
| "In disks overview, DaisyDisk includes the purgeable space into the free space, exactly as Finder does." | DaisyDisk v4 manual, DisksOverview |
| "In Space Lens, you may notice the Purgeable Space item, which is the space occupied by temporary system files that are removed automatically in case of need." | MacPaw KB, Space Lens (CleanMyMac X era) |
| Snapshot thinning "shrinks those snapshots without affecting your backups." | MacPaw KB, free-up-more-space (current CleanMyMac) |
| "When Storage settings shows free space, it INCLUDES purgeable as available. So a Mac that's '256GB used / 244GB available' might actually be 280GB used with 30GB of that being purgeable." | sweepformac.com guide, find-purgeable-files-mac |
| "a snapshot showing '10GB' usually means it represents 10GB of data that has changed in the live filesystem since the snapshot was taken" | sweepformac.com guide, find-time-machine-snapshots-mac |
| "'About This Mac' includes 'purgeable' space as free/available space." | Omni Group forums, thread 42843 (OmniDiskSweeper) |
| Snapshots are "stored for up to 24 hours or until space is needed on the disk." | Apple support article 102154 (canonical, liability-safe phrasing) |

**Cache safety**

| Quote | Source |
|---|---|
| "Only the files that can be safely deleted are preselected for removal." | MacPaw KB, System Junk |
| Auto-selects everything found in System Junk "except… iOS device support files, archives, module caches, Xcode documentation cache, and available iOS simulators." | MacPaw KB, System Junk |
| "None of your personal files is gone unless you want it." / "will never touch Documents, Photos, iCloud Drive, or anything you created yourself." | MacPaw KB, safety / Safety Database |
| "deletes only those files that are 100% safe for removal" | MacPaw KB, safety (note the absolutism — see burn incidents) |
| System logs "are useful only for debugging and thus aren't worth the disk space they occupy" | MacPaw KB, Smart Scan — MacPaw's closest approach to a "safe but pointless" tier |
| "only delete the files that you can recognize (by location, file name and preview of content) as those you have created or downloaded yourself" | DaisyDisk v4 manual, "What is safe to delete?" |
| "it is your own files that take up the most disk space, not the system files, so there is no real need to touch the latter." | DaisyDisk v4 manual, "What is safe to delete?" |
| "every scan result is labeled Safe, Review, or Do Not Delete before you act on anything" | macsweep.app (claim; unverified in-app, low-trust ecosystem) |
| "Deleted caches may have to be rebuilt, so an application can initially launch more slowly afterward." | OnyX reviews/docs (macmyths, iTechGuides) |

**Units**

| Quote | Source |
|---|---|
| "The default setting is `.file`, which is the system specific value for file and storage sizes… in macOS 10.8, this uses the decimal style" | developer.apple.com, ByteCountFormatter (verified) |
| "Finder uses the decimal unit system, whereas GrandPerspective can use either depending on your Preferences setting. So when you scan using the binary unit system in GrandPerspective, the size reported by GrandPerspective will be smaller." | GrandPerspective help, "How to explain differences in reported sizes" (verified, v3.7.2) |

**User-burn incidents (evidence for conservative cache verdicts)**

- Photos library damaged by cleanup: Apple Communities thread "CleanMyMac 3 messed up my photos library" (~2018); Apple's photo-library docs warn third-party clean/shrink apps "can instead damage the photo library or delete pictures."
- Spotify offline downloads vanish after cache clearing: Spotify Community ongoing-issue thread; staff guidance: "try disabling any power saving or cache clearing apps."
- Cookie clearing logs users out of everything: Tom's Guide CCleaner forum thread; Trustpilot CleanMyMac review of Smart Care cookie erasure.
- Forced multi-GB Xcode re-downloads (device support files) — the very items MacPaw excludes from smart-select.
- MacRumors consensus threads: "a few cleaner apps have been known to corrupt system cache files"; caches "get rebuilt, which slows the Mac down."

---

## 4. Where we should deliberately differ

These are paid apps that delete files; Dad Ware is free and read-only. Copy the trust mechanics, not the pressure mechanics.

**Do not copy:**

1. **"100% safe" absolutism** (MacPaw). The burn incidents above are why that claim reads as marketing. Dad's credibility rests on saying "safe, but here's the cost" — the OnyX sentence, not the MacPaw sentence.
2. **Calling working caches "junk."** CleanMyMac's binary junk/protected framing is what produces the tester's distrust. A cache doing its job is not junk, and a tool that says so earns the right to be believed about the things that *are*.
3. **Pre-checking everything.** MacPaw pre-selects nearly all findings because selected GB justify the subscription ("users find and remove 10.5 GB… after the first Smart Care scan" is a sales stat). Our verdicts should be conservative because nothing about our model needs a big number.
4. **The nudge ecosystem.** Menu-bar reminders, notifications that survive uninstall (documented in Apple Communities), fear-framed malware findings, perpetual "74% off" urgency. All of it exists to drive conversion and all of it would violate the trust promise. Dad Ware runs when asked and is silent otherwise.
5. **Fake precision.** Per-snapshot sizes (no single true answer under copy-on-write) and single-decimal "junk found" totals imply accuracy the data doesn't support. DaisyDisk's "for reference only" honesty is the standard to meet or beat.

**Do copy (these are genuinely good):**

- MacPaw's explicit never-touched list, named in user terms ("Documents, Photos, iCloud Drive, anything you created yourself").
- MacPaw's category-level explanation style ("logs are useful only for debugging and thus aren't worth the disk space").
- DaisyDisk's calm de-escalation ("just let it be — it will be reclaimed automatically") and its Finder-consistency principle.
- DaisyDisk's honest residual accounting ("hidden space" / "still hidden") instead of pretending the scan saw everything.
- OmniDiskSweeper's practice of explaining the Finder discrepancy — but in the report itself, not a forum.

---

## 5. Roadmap impacts

1. **New bug, high priority: `format_size()` uses 1024 math with GB labels** (`utils/formatters.py`). Every size in every report is ~7% below Finder's number for the same bytes. Fix to 1000-based; update `parse_size()`, the GB-denominated grading thresholds, and tests together. This is cheap and should land before wider distribution — it's the single most likely "this tool is broken" trigger for the target audience. Consider labeling RAM figures GiB/MiB if they stay binary.
2. **The BACKLOG "validation spike: purgeable-space data source" is answered by this research: stop looking.** No shipping tool reads purgeable from a CLI source; native apps use the API we can't call. Replace the spike with the derived-gap approach (`statvfs` used minus scanned total = "unaccounted space" item, DaisyDisk-style), and reword `HIDDEN-STORAGE-PLAN.md` 1c's "aggregate purgeable estimate" to match. The report should also state outright that Finder's "available" includes purgeable and will look bigger than ours.
3. **Never show per-snapshot sizes** in the 1c snapshot scanner — names, dates, and count from `tmutil listlocalsnapshots` only. The one tool that shows sizes disclaims them as unreliable; claiming them would be fake precision (see §4.5).
4. **Snapshot *thinning* is a solved commodity** (CleanMyMac one-click, OnyX free) — this validates, rather than threatens, the read-only choice. Our differentiation is the explanation layer plus the copy-pasteable command; there is no feature gap to close.
5. **Cache verdicts need a third tier and corrected copy.** Add the "safe but costly to re-acquire" category (CleanMyMac's own unexplained default-exceptions prove it exists) to the 1a cache scanner's advice model. And fix two factual claims used in planning docs and the research prompt: clearing Spotify's cache **does** remove offline downloads (playlists/likes survive); "Arc keeps logins" is only true if cookies/site data are untouched — advice copy must distinguish the Caches folder from browser data.
6. **A units/discrepancy explainer belongs in the report itself.** One short "why Dad's numbers might not match Finder" note (purgeable space, protected folders we skipped, snapshots) — the OmniDiskSweeper forum answer shows silence just moves the question to support channels. Cheap to add during Wiring.
7. **Follow-up research worth doing when feasible:** hands-on verification of the three apps' live UIs (nothing here was observed on-screen), and resolving which "Sweep" the competitive docs should track — sweepformac.com's guide library is the strongest tonal competitor regardless of its app's quality.
