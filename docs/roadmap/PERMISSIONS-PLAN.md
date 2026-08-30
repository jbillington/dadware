# Permissions & Trust PRD

**Status:** Active — the spec behind BACKLOG Milestones 2-4. The askdad rename (the identity prerequisite) landed Aug 28, 2026.
**Effort:** Phase 1: 3-4 hours. Phase 2: 8-12 hours plus Apple Developer enrollment wait. Phase 3: 3-4 hours.
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

The MVP ships as **two packages from one codebase**, and this document primarily serves the first:

1. **The app (primary, for beta testers): a signed and notarized `.app` bundle inside a stapled DMG.** The user downloads the DMG from the website, drags Dad Ware to Applications (the standard DMG window with an Applications shortcut), and double-clicks it. The app runs the scan itself — no Terminal ever appears — and shows progress in the browser immediately (see the UX walkthrough). Because it's a real `.app`, macOS attributes every permission prompt to *Dad Ware*, prompt text is ours to write via `Info.plist` usage strings, and Full Disk Access is granted to the product itself — the best possible permission story.
2. **The CLI (secondary, for technical users): the same scanner as a command-line tool**, distributed via Homebrew (brew installs skip quarantine entirely) and optionally as a notarized download from the website. Prompts and grants attribute to Terminal in this channel, which its audience understands. This channel also serves the automation/AI use case: paired with the backlog `--json` and `--prompt` flags, the CLI becomes a scan engine a local LLM or agent harness can call.

**Later: a native Swift app** — the CleanMyMac competitor with real UI. The Python scanner stays the engine; the Future Work section lists what changes then.

## The MVP User Experience, Step by Step

What a beta tester actually experiences, from download to report:

1. **Download and install.** The website serves a notarized, stapled DMG. Opening it shows the standard Mac install window: the Dad Ware icon next to an Applications-folder shortcut; the user drags it over. (Technical constraint behind the DMG choice: Apple's notarization ticket can be stapled to `.app`, `.dmg`, and `.pkg` files, but **not** to a bare executable. A stapled DMG passes Gatekeeper offline and shows the cleanest first-open behavior. A `.pkg` could auto-install to Applications, but the drag-to-Applications DMG is the convention Mac users already know.)
2. **First launch.** The user double-clicks Dad Ware in Applications. Because the app is Developer ID-signed and notarized, it opens without security warnings — no Terminal, no right-click ritual. (Today's unsigned build is exactly what fails here, especially on Tahoe.)
3. **Progress appears immediately.** The app opens the default browser on a progress page right away, so there's never a "did it launch?" dead moment. The page explains what's being scanned, shows items found so far, and carries the read-only promise. See "App-mode progress" under Implementation for how a static HTML page updates during the scan.
4. **Permission prompts arrive up front, with context.** Before the deep scan, the app deliberately touches Desktop, Documents, and Downloads in a fixed order so the standard macOS dialogs — attributed to *Dad Ware*, with our explanation text — all happen at the start, not scattered through a five-minute scan. Everything in the "no permission needed" tier below works regardless of what the user clicks. Denied folders are skipped and labeled, not silently zeroed.
5. **The progress page becomes the report.** When the scan finishes, the final write replaces the progress page with the existing single HTML report. A status line at the top says either "Full report" or "Partial report — Trash, Mail, and Messages are hidden. Here's how to unlock them."
6. **Optional upgrade.** If the user wants the full picture, the report's walkthrough opens System Settings → Privacy & Security → Full Disk Access directly (`open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`), and the toggle they flip is *Dad Ware's own entry* — the app they can see in their Applications folder. The next scan picks it up automatically.

The CLI channel follows the same flow minus steps 1-3: brew install or website download, run in Terminal, prompts attribute to Terminal (its audience understands this), progress prints to the terminal as it does today.

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
3. **Grants attach to the "responsible process."** A `.app` the user launches owns its own prompts and grants — this is why the app channel gets "Dad Ware would like to access…" dialogs and its own Full Disk Access entry. A CLI run from Terminal means *Terminal* owns every prompt and grant instead; that's inherent to the CLI channel and fine for its technical audience.
4. **Notarization, not the Mac App Store.** App Store apps must be sandboxed, and sandboxed apps cannot receive Full Disk Access or scan a disk — a store submission would kill the core function. The path is: Developer ID certificate → hardened-runtime codesign → notarize with `notarytool` → staple → self-distribute. This holds for the future Swift wrapper too.
5. **Grants are keyed to bundle ID + code signature.** Unsigned or ad-hoc builds get their grants reset on every rebuild; users of a signed app keep grants across updates. Pick the identifier once and never change it — which means the `askdad` rename (`docs/roadmap/ASKDAD-RENAME-PLAN.md`) must land *before* the first signed build, so the identity baked into the first grant users give (e.g. `com.dadware.askdad`) is the final one. (`tccutil reset All <bundle-id>` resets grants for testing.)
6. **Read-only changes nothing technically.** TCC gates reading — that is its entire purpose — so "we never delete files" earns no reduced prompting. Its value is persuasion: it's why the user should click Allow.

---

## Implementation

### Phase 1: Permission UX foundation

All of it works in today's CLI and carries forward unchanged into the wrapped app.

1. **Prompt choreography.** At scan start, show the one-line explainer (on the progress page in app mode, printed in CLI mode — including a "prompts will say Terminal" heads-up in the CLI case), then deliberately `os.listdir()` each auto-prompt folder in a fixed order so all dialogs fire up front with context.
2. **Per-folder detection.** Extend `utils/permissions.py`: distinguish TCC denial (EPERM on a folder the user owns) from ordinary POSIX errors, per folder. Record per-folder grant state in `scan_data['permission_status']`, not just the single FDA boolean.
3. **Honest-denial copy.** Implement the tier matrix in both renderers — every denied area gets its explanation and fix path in the terminal output and the HTML report. Never a silent zero.
4. **FDA deep link.** Where FDA instructions appear, offer to open the System Settings pane directly (behind a `[y/N]` in CLI mode).

### Phase 2: The `.app` bundle, app-mode experience, and both packages

**The bundle.** Switch the PyInstaller spec from a bare executable to a `.app` bundle (onedir mode — required for clean signing), bundle ID `com.dadware.askdad` (final after the rename — see constraint 5), with the `Info.plist` usage strings that put dad's voice in the system dialogs: `NSDesktopFolderUsageDescription`, `NSDocumentsFolderUsageDescription`, `NSDownloadsFolderUsageDescription`, `NSRemovableVolumesUsageDescription`, `NSNetworkVolumesUsageDescription` — e.g. "Dad Ware measures folder sizes to build your report card. It never changes or uploads anything."

**App-mode behavior.** Double-click launch means no terminal: no `print()` a user can see, and no `input()` that can ever be answered. Requirements:

- **Non-interactive by default in app mode:** largely done at the scanner level as of Aug 2026 — `select_volume()` detects the absence of a TTY and auto-selects instead of prompting (`utils/volumes.py`), so a double-clicked bundle already can't hang on `input()`. Remaining app-mode work: route status through the progress page instead of stdout, and detect app mode via a flag baked into the bundle launch (e.g. `--app-mode` as the bundle's launch argument).
- **App-mode progress:** open the browser *immediately* at launch on a progress page, before scanning starts. MVP mechanism: the progress HTML contains `<meta http-equiv="refresh" content="2">`, and the scanner rewrites the file every ~2 seconds from the existing `progress_callback` hook in `scan_storage()` (items found, current phase, elapsed time, the read-only line). The browser reloads it on each interval; the final write is the real report *without* the refresh tag, so it lands and stays. Zero dependencies, works offline, no server process. Upgrade path if refresh flicker grates: a stdlib `http.server` on localhost with the page polling a JSON status endpoint for smooth in-page updates — nice-to-have, not MVP. (A native progress window — e.g. Tkinter — is deliberately avoided: the product strategy is HTML-as-UI until the Swift app.)

**Sign, notarize, package.** Much of the tooling already exists (added Aug 2026 with the code-review refactor) but **none of it has ever executed** — it needs an Apple Developer ID first:

1. Developer ID Application certificate (Apple Developer Program, $99/yr — already on the backlog). Required secrets are listed in `docs/BUILDING.md`.
2. `sign_and_notarize.sh` already scripts the hardened-runtime codesign + `notarytool` flow, with `entitlements.plist` in place (FDA needs no entitlement). CI has a universal2 build job, gated to tags and manual dispatch.
3. Stapling: the script currently signs the bare executable and itself notes that stapling requires a `.app`/`.dmg`/`.pkg` container — extending it to the artifacts below is the remaining work.
4. Two artifacts from `package_for_distribution.sh`:
   - **DMG** containing the `.app` plus an Applications-folder shortcut — the primary beta download. Staple the DMG.
   - **CLI package** — the same scanner as a plain executable for the Homebrew tap (brew skips quarantine) and optionally a notarized website download (bare binaries can't be stapled, so the zip route requires the Mac to be online for Gatekeeper's ticket lookup on first run — acceptable for this channel's audience).
5. Verify on a clean machine (backlog item) — expected to also resolve the Tahoe launch failure.

### Phase 3: First-run onboarding

The closest macOS allows to "accept on install," built with the HTML we already generate:

1. On first launch (no `~/.dadware` state), before any scan, open a local **welcome page**: what Dad Ware does, the read-only promise, what macOS will ask and why — with a side-by-side of the report *without* FDA vs. *with* it (Trash, Mail, Messages visible). Honest sell; user chooses.
2. Two paths: "Run my first scan" (proceeds with Phase 1 choreography) and "Unlock the full report" (FDA pane deep link + illustrated 3-step walkthrough).
3. Every report header shows current status: "Full report ✓" or "Partial report — here's what's hidden and how to fix it."
4. Store onboarding-completed state in `~/.dadware/` so it runs once.

### Future work: the native Swift app

Out of scope for the MVP, listed so the MVP work doesn't paint us into a corner:

- The Swift app replaces browser-as-UI with real native UI (windows, live progress, the CleanMyMac-competitor experience). The Python scanner remains the engine underneath.
- **It must keep the same bundle ID** (`com.dadware.yourdad`) and Developer ID signing so users' existing permission grants carry over instead of resetting (constraint 5).
- Phases 1 and 3 (choreography, per-folder detection, onboarding content, honest-denial copy) carry over as-is; the usage strings and DMG pipeline from Phase 2 are reused directly.
- Distribution stays Developer ID + notarization — the Mac App Store remains off the table (constraint 4).
- The CLI channel continues alongside it for Homebrew users and the LLM-harness use case.

## Testing

- `tccutil reset` between runs to re-test the full grant flow; test all-denied, partially-granted, and FDA-revoked-after-grant states.
- Clean-machine matrix (ties into the existing backlog item): Intel + Apple Silicon; Sonoma, Sequoia, Tahoe. Verify the notarized `.dmg`/`.pkg` opens with no warnings, offline included (stapling), and that the Tahoe failure is gone.
- Unit tests: per-folder TCC detection (mock EPERM), honest-denial copy present in both renderers, onboarding state-file logic, app-mode never calls `input()` (multi-volume defaults instead of prompting), progress-page writes carry the refresh tag and the final report write doesn't.

## Out of Scope

- Mac App Store distribution — sandboxing makes the product impossible.
- Any privilege-escalation tricks (helper tools, launch daemons) to approximate FDA. Not worth the trust cost for a product whose brand is "safe."
- MDM / enterprise pre-approval profiles.
- The Swift wrapper itself — only its permission implications are covered here.
