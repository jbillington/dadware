# Research prompt: how competing Mac storage tools present the hard parts

Paste the block below into a research agent with web access. Written Aug 24, 2026,
to unblock three specific decisions in `BACKLOG.md` — not as general market research.

---

You are researching how existing macOS storage/cleanup tools solve three specific
presentation problems. I am building a competing tool and need to make three
decisions that will change what every user sees. I want evidence, not opinion.

## The product you are researching for

**Dad Ware** is a free, read-only macOS storage scanner. It scans the disk, assigns
letter grades (A–F), and produces a plain-language HTML report with dad-style
commentary. Hard constraints that shape everything:

- **It never deletes, moves, or changes a file.** There are no clean/delete buttons
  and there never will be. Every recommendation is advice the user carries out
  themselves. This is the core trust promise, not a limitation to design around.
- **Python standard library only, no external runtime dependencies.** It cannot call
  Objective-C/Swift APIs (no PyObjC), so it is limited to what CLI tools expose.
- **Target user: young, non-technical Mac owners** — teenagers and young adults who
  have never cleaned up or backed up a Mac. Developers are a secondary audience.
- It is free and open source; the competitors below are paid commercial apps.

## The three decisions

### 1. Decimal vs binary size units

Dad Ware currently formats sizes with 1024-based math but labels them "GB", so it
prints **47.5 GB** where Finder prints **50.98 GB** for the same bytes. macOS has
used decimal (1000-based) units since Snow Leopard. A user comparing our report to
Finder sees a ~7% discrepancy and reasonably concludes our tool is broken.

Find out:
- What convention does each tool below display — decimal, binary, or binary labeled
  as GiB? Do their numbers match Finder's for the same volume?
- Does any of them explain the difference to the user, or offer a preference?
- Is there evidence from reviews, forums or support tickets of users being confused
  by a tool's numbers not matching Finder?

### 2. Purgeable space and APFS local snapshots

Finder reports "57.77 GB available (6.79 GB purgeable)". That figure comes from
`NSURLVolumeAvailableCapacityForImportantUsageKey`. **We have verified that no macOS
command-line tool exposes it** — `diskutil info -plist` (`APFSContainerFree`) and
`system_profiler SPStorageDataType -json` both return exactly the `statvfs` number,
i.e. free space *excluding* purgeable. Native apps can call the API; we cannot.

This matters because "I deleted a bunch of stuff and nothing changed" is the single
most demoralizing Mac storage experience, and purgeable space plus stale local
Time Machine snapshots are usually the cause.

Find out:
- Does each tool show a purgeable figure? Where, what does it call it, and does it
  match Finder's number?
- How does each handle **APFS local snapshots** — count, age, size, or not at all?
  Note that macOS does not expose per-snapshot sizes to unprivileged callers
  (copy-on-write shared blocks mean "how big is snapshot X" has no single answer).
  Does any tool claim a per-snapshot size anyway? If so, what do they appear to be
  measuring, and do users report it as accurate?
- Do any offer to thin snapshots (`tmutil thinlocalsnapshots`), and how do they
  frame the risk?
- **Most important for us:** find any tool that *explains* purgeable space without
  being able to act on it. What words do they use? Screenshots or exact copy please.

### 3. Telling users which caches are safe to clear

Our scan found 16.4 GB of app caches on one test Mac — Messages 7.6 GB, Arc 1.8 GB,
Spotify 861 MB, plus ~2 GB of stale auto-updater downloads. The tester's reaction to
the list was: *"these are all apps I actually use, so I don't want to delete those."*

That reaction is the problem. Two things are true at once and the UI has to carry
both: a cache is neither the app nor the user's data (clearing Spotify's cache keeps
their playlists; clearing Arc's keeps their tabs and logins), **and** most caches
aren't worth clearing because they come back within a week.

Find out:
- How does each tool categorize caches, if at all? Does it distinguish "safe and
  worth it" from "safe but pointless" from "leave this alone"?
- Does it show a risk or safety indicator per item? What are the exact labels?
- Which items are pre-selected by default when you open the cleanup screen, and
  which are not? Default selections reveal what the vendor considers safe.
- What copy does it use to reassure a hesitant user? Exact wording is what I need.
- Is there evidence of users being burned — losing data, breaking an app, or having
  to re-download something large — after a tool told them a cache was safe? Search
  support forums, Reddit (r/MacOS, r/macapps), and review sites.

## Tools to cover

1. **CleanMyMac** (MacPaw) — the market leader and the most direct competitor to the
   eventual paid version of this idea. Note it is notification/upsell heavy; I am
   interested in what it gets *right* about explanation, and where its pressure
   tactics would violate our trust promise.
2. **DaisyDisk** — visualization-first (sunburst), largely read-oriented, and it has
   an explicit concept of hidden/purgeable space. Probably the closest philosophical
   match to what we are building. Pay particular attention to how it labels space it
   can see but not attribute.
3. **Sweep** — smaller indie cleaner. Interesting as an example of what a solo
   developer ships without a large design team.

If you find a fourth tool that handles any of the three questions notably better
(OmniDiskSweeper, GrandPerspective, Disk Inventory X, Onyx, App Cleaner & Uninstaller),
include it briefly.

## How to research

- Prefer primary sources: vendor documentation, support/KB articles, App Store
  screenshots, official YouTube walkthroughs, and current app-version release notes.
- Secondary: hands-on reviews with screenshots, Reddit threads, MacRumors forums.
- **Say when you are inferring.** If you cannot see a screen without buying and
  installing the app, say so plainly rather than guessing. A confident wrong answer
  about a competitor's UI is worse to me than an admitted gap.
- Note the app version and date for anything you describe — these UIs change.
- Quote exact interface copy wherever you can. The wording is the deliverable for
  question 3, more than the layout is.

## Deliverable

A markdown document with:

1. **A recommendation on each of the three decisions**, with the reasoning and the
   evidence behind it. For decision 1 I want a straight answer: which convention
   should a Finder-comparing, non-technical audience see?
2. **A comparison table** covering, per tool: unit convention, purgeable handling,
   snapshot handling, cache categorization, default selections, and safety labeling.
3. **A quotes appendix** — verbatim interface copy for anything cache-safety or
   purgeable related, with source and version.
4. **Where we should deliberately differ.** These are paid apps that delete files
   for the user; we are free and read-only. Some of their patterns exist to justify
   a subscription or to drive urgency, and copying those would damage the exact
   trust the product is built on. Call those out specifically rather than presenting
   every competitor behavior as a best practice.
5. **Anything that changes the roadmap.** If a competitor has solved a problem we
   have not thought about, or if one of our planned features is a solved commodity
   not worth building, say so.

Existing context in this repo, if available to you: `docs/COMPETITIVE-COMPARISON.md`
(currently compares only ncdu and htop — this research would extend it to the
commercial GUI tools), `docs/roadmap/HIDDEN-STORAGE-PLAN.md`, and `BACKLOG.md`.
