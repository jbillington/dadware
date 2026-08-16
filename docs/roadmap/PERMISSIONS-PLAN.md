# Permissions & Trust PRD

**Status:** Proposed
**Effort:** Phase 1: 3-4 hours. Phase 2: 4-8 hours plus Apple Developer enrollment wait. Phase 3: 3-4 hours.
**Related:** BACKLOG "Sign and ship as `.app`" and the Tahoe launch bug (signing likely fixes it). `HIDDEN-STORAGE-PLAN.md` Phase 2 (Trash) depends on this plan.

---

## The Problem

Dad Ware's whole value is looking at the user's disk — and macOS, by design, doesn't let software look without asking. Today that asking goes badly:

- **Downloads from the web get blocked.** An unsigned executable from a website triggers Gatekeeper's scariest warnings, and on newer macOS may refuse to launch at all — this is the likely cause of the Tahoe launch failure in the backlog. A user who can't open the app never sees the product.
- **Permission prompts appear with no context.** Mid-scan, macOS suddenly asks about the Downloads folder with no explanation of why, and every prompt says "Terminal" wants access — not Dad Ware. Confused users click "Don't Allow," and the report silently gets worse.
- **Denied access looks like a bug.** Protected areas (Trash, Mail, Messages) show 0 bytes with no explanation, which reads as "this app doesn't work" instead of "this needs one more permission."

For a product whose brand is *the dad you trust to look at your Mac*, a scary or confusing permission experience isn't a papercut — it undermines the entire premise. And permissions can't be bolted on later: macOS ties every grant to the app's signed identity, so this has to be right **before** the first signed build ships.

## The Feature

A designed trust-and-permission experience for the MVP: the user downloads Dad Ware from the website, it opens without warnings, every permission prompt arrives with a plain-language explanation of why, and the report is always honest about what it could and couldn't see — with a one-click path to unlock more.

| Capability | User benefit |
|---|---|
| **Signed + notarized download** | Opens like a normal Mac app — Apple has malware-scanned it. No "unidentified developer" scare screen, no right-click-open ritual. |
| **Prompts with context** | Before macOS asks anything, Dad Ware explains: "macOS will ask about a few folders — I only read sizes, never contents, and I never change anything." All prompts happen up front, not mid-scan. |
| **Honest partial reports** | Anything Dad Ware couldn't see says so in dad language, with the fix: "Can't see your Trash yet — grant Full Disk Access and I'll check it next time." Never a silent zero. |
| **Guided full-access upgrade** | Full Disk Access can't be granted by a dialog (Apple's rule — see below), so Dad Ware does the next best thing: opens the exact System Settings pane and walks the user through the toggle. |

**Positioning:** the read-only promise is the trust asset. Dad Ware never deletes, moves, or uploads anything — every permission screen and prompt description says so. Technically, read-only earns no discount from macOS (its privacy system gates *reading*), but it's the reason a user should feel safe saying yes.

## The MVP Launch Path

Two stages, and this document primarily serves the first:

1. **MVP (this plan): a signed and notarized Python CLI**, downloaded from the website, run in Terminal, producing the existing HTML report. Audience: early adopters and testers. Key consequence: macOS attributes all permission prompts and grants to *Terminal*, not to Dad Ware — the prompts will literally say "Terminal would like to access…". We work with that honestly (see the UX walkthrough) rather than pretending otherwise.
2. **Later: a native Swift wrapper app** — the CleanMyMac competitor. The Python scanner stays the engine; the wrapper makes Dad Ware a real `.app` with its own identity, so prompts finally say "Dad Ware," prompt text is customizable, and Full Disk Access is granted to the product itself. The Future Work section lists exactly what changes then.

## The MVP User Experience, Step by Step

What a tester actually experiences, from download to report:

1. **Download from the website.** The CLI ships inside a notarized, stapled `.dmg` or `.pkg` — not a bare zip. (Technical constraint: Apple's notarization ticket can be stapled to `.app`, `.dmg`, and `.pkg` files, but **not** to a bare executable. A zipped bare binary works only if the Mac is online for Gatekeeper's ticket lookup on first run; a stapled `.dmg`/`.pkg` works offline and shows the cleanest first-open behavior. Homebrew is a good parallel channel — files installed via `brew` don't carry the quarantine flag at all, so brew users skip Gatekeeper entirely.)
2. **First run.** The user opens Terminal and runs `yourdad`. Because the binary is Developer ID-signed and notarized, it just runs — no security warnings. (Today's unsigned build is exactly what fails here, especially on Tahoe.)
3. **Before any scanning**, Dad Ware prints a short explainer: what it's about to look at, the read-only promise, and a heads-up that macOS will show a few permission dialogs *attributed to Terminal*. Then it deliberately touches Desktop, Documents, and Downloads in a fixed order so all the standard prompts happen **up front, with that context fresh** — not scattered through a five-minute scan.
4. **The scan runs.** Everything in the "no permission needed" tier below works regardless of what the user clicked. Denied folders are skipped and labeled, not silently zeroed.
5. **The report opens in the browser** — the existing single HTML report. A status line at the top says either "Full report" or "Partial report — Trash, Mail, and Messages are hidden. Here's how to unlock them," linking to the Full Disk Access walkthrough.
6. **Optional upgrade.** If the user wants the full picture, Dad Ware opens System Settings → Privacy & Security → Full Disk Access directly (`open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`) with step-by-step instructions. For the CLI MVP, the toggle they flip is *Terminal's* — the walkthrough says so plainly. Next scan picks it up automatically.

## What Works at Each Permission Tier

The product decision encoded here: **Dad Ware must be genuinely useful with zero permission grants.** Enhanced access unlocks a bonus tier; it is never required.

| Tier | How it's granted | What the storage scan gets |
|---|---|---|
| **No permission needed** | Nothing — works immediately | Volume totals and free space; the full home-folder scan outside protected areas; hidden app caches (`~/Library/Caches`, per `HIDDEN-STORAGE-PLAN.md` 1a/1b); developer caches and dot-folders; purgeable space + snapshot detection (1c); Music library; the whole CPU/RAM scan |
| **Auto-prompt folders** | macOS shows a yes/no dialog on first access | Desktop, Documents, Downloads folder sizes; external and network volumes |
| **Full Disk Access** | Manual toggle in System Settings — no dialog exists, by Apple's design | Trash, Mail, Messages, Photos library internals |

Every scanner must know its tier and produce the honest-denial message for it. This matrix is also the marketing story: "works out of the box; one optional toggle unlocks everything."

## How macOS Permissions Actually Work

Background for anyone implementing or making product calls against this plan. These are hard platform constraints:

1. **There is no install-time permission grant.** The TCC privacy system cannot be pre-approved by an installer, a `.pkg` script, or any dialog an app shows. "Accept all permissions during install" does not exist on macOS (outside enterprise MDM). The closest legal approximation is a first-launch onboarding flow — Phase 3.
2. **Only the auto-prompt tier shows dialogs.** Desktop/Documents/Downloads and removable/network volumes prompt automatically on first access; a real `.app` controls the explanation text via `Info.plist` usage-description strings. **Full Disk Access has no API and no dialog, ever** — the user must flip the toggle in System Settings themselves. Apps can only deep-link to the pane, explain, and detect the result (`utils/permissions.py` already detects it).
3. **Grants attach to the "responsible process."** A CLI run from Terminal means Terminal owns every prompt and grant. Grants attach to Dad Ware itself only when it ships as a signed `.app` bundle — the single biggest permission reason to eventually wrap the CLI.
4. **Notarization, not the Mac App Store.** App Store apps must be sandboxed, and sandboxed apps cannot receive Full Disk Access or scan a disk — a store submission would kill the core function. The path is: Developer ID certificate → hardened-runtime codesign → notarize with `notarytool` → staple → self-distribute. This holds for the future Swift wrapper too.
5. **Grants are keyed to bundle ID + code signature.** Unsigned or ad-hoc builds get their grants reset on every rebuild; users of a signed app keep grants across updates. Pick the identifier once (e.g. `com.dadware.yourdad`) and never change it. (`tccutil reset All com.dadware.yourdad` resets grants for testing.)
6. **Read-only changes nothing technically.** TCC gates reading — that is its entire purpose — so "we never delete files" earns no reduced prompting. Its value is persuasion: it's why the user should click Allow.

---

## Implementation

### Phase 1: Permission UX foundation

All of it works in today's CLI and carries forward unchanged into the wrapped app.

1. **Prompt choreography.** At scan start, print the one-line explainer (including the "prompts will say Terminal" heads-up), then deliberately `os.listdir()` each auto-prompt folder in a fixed order so all dialogs fire up front with context.
2. **Per-folder detection.** Extend `utils/permissions.py`: distinguish TCC denial (EPERM on a folder the user owns) from ordinary POSIX errors, per folder. Record per-folder grant state in `scan_data['permission_status']`, not just the single FDA boolean.
3. **Honest-denial copy.** Implement the tier matrix in both renderers — every denied area gets its explanation and fix path in the terminal output and the HTML report. Never a silent zero.
4. **FDA deep link.** Where FDA instructions appear, offer to open the System Settings pane directly (behind a `[y/N]` in CLI mode).

### Phase 2: Sign and notarize the CLI

1. Developer ID Application certificate (Apple Developer Program, $99/yr — already on the backlog).
2. `codesign --options runtime` (hardened runtime is required for notarization; FDA needs no entitlement).
3. `xcrun notarytool submit`, then staple the *container*: package the CLI in a `.dmg` or `.pkg` and staple that, since bare executables can't be stapled. Update `package_for_distribution.sh` accordingly.
4. Publish on the website + Homebrew tap. Verify on a clean machine (backlog item) — expected to also resolve the Tahoe launch failure.

### Phase 3: First-run onboarding

The closest macOS allows to "accept on install," built with the HTML we already generate:

1. On first launch (no `~/.dadware` state), before any scan, open a local **welcome page**: what Dad Ware does, the read-only promise, what macOS will ask and why — with a side-by-side of the report *without* FDA vs. *with* it (Trash, Mail, Messages visible). Honest sell; user chooses.
2. Two paths: "Run my first scan" (proceeds with Phase 1 choreography) and "Unlock the full report" (FDA pane deep link + illustrated 3-step walkthrough).
3. Every report header shows current status: "Full report ✓" or "Partial report — here's what's hidden and how to fix it."
4. Store onboarding-completed state in `~/.dadware/` so it runs once.

### Future work: the Swift wrapper

Out of scope for the MVP, listed so the CLI work doesn't paint us into a corner:

- The wrapper becomes the signed `.app` with the stable bundle ID; prompts finally attribute to Dad Ware and grants transfer to the product.
- `Info.plist` usage-description strings put dad's voice in the system dialogs: `NSDesktopFolderUsageDescription`, `NSDocumentsFolderUsageDescription`, `NSDownloadsFolderUsageDescription`, `NSRemovableVolumesUsageDescription`, `NSNetworkVolumesUsageDescription` — "Dad Ware measures folder sizes to build your report card. It never changes or uploads anything."
- The Python scanner remains the engine; Phases 1 and 3 (choreography, detection, onboarding, honest-denial copy) carry over as-is.
- Distribution stays Developer ID + notarization — the Mac App Store remains off the table (constraint 4).

## Testing

- `tccutil reset` between runs to re-test the full grant flow; test all-denied, partially-granted, and FDA-revoked-after-grant states.
- Clean-machine matrix (ties into the existing backlog item): Intel + Apple Silicon; Sonoma, Sequoia, Tahoe. Verify the notarized `.dmg`/`.pkg` opens with no warnings, offline included (stapling), and that the Tahoe failure is gone.
- Unit tests: per-folder TCC detection (mock EPERM), honest-denial copy present in both renderers, onboarding state-file logic.

## Out of Scope

- Mac App Store distribution — sandboxing makes the product impossible.
- Any privilege-escalation tricks (helper tools, launch daemons) to approximate FDA. Not worth the trust cost for a product whose brand is "safe."
- MDM / enterprise pre-approval profiles.
- The Swift wrapper itself — only its permission implications are covered here.
