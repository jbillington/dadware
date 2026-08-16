# Permissions Plan (Signed Python .app MVP)

**Status:** Proposed
**Effort:** Phase 1: 3-4 hours. Phase 2: 4-8 hours (plus Apple Developer enrollment wait). Phase 3: 3-4 hours.
**Related:** BACKLOG "Sign and ship as `.app`" and the Tahoe launch bug (signing likely fixes it). `HIDDEN-STORAGE-PLAN.md` Phase 2 (Trash) depends on this plan.
**Goal:** Ship the signed Python-built executable as an MVP Mac app — HTML reports instead of SwiftUI — with a permission experience good enough that a non-technical user gets through it. Permissions must be designed *before* the executable is signed and submitted to Apple, because the app's identity (bundle ID + signature) is what macOS attaches permission grants to.

---

## What macOS Actually Allows (read this first)

These are hard platform constraints. The plan is shaped around them, not around the ideal UX.

1. **There is no install-time permission grant.** The TCC privacy system cannot be pre-approved by an installer, a `.pkg` script, or a dialog the app shows. The "accept everything when you install" flow does not exist on macOS (outside of enterprise MDM, which is irrelevant for consumers). The closest legal approximation is a **first-launch onboarding flow**, which is what Phase 3 builds.

2. **Permissions come in two tiers, and only one of them prompts automatically:**
   - **Auto-prompt folders** — Desktop, Documents, Downloads, removable volumes, network volumes. The first time the app touches one, macOS shows a yes/no dialog. This is the part of the wish that *does* work "with some sort of dialogue box," and the app controls the prompt text via `Info.plist` usage-description strings.
   - **Full Disk Access (FDA)** — required for Trash, Mail, Messages, Photos library internals, other users' files. **No API, no dialog, ever.** The user must manually flip a toggle in System Settings → Privacy & Security → Full Disk Access. An app can only: deep-link to that exact pane (`open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`), explain what to do, and detect when it's been granted (`utils/permissions.py` already does the detection).

3. **Grants attach to the "responsible process."** When `yourdad` runs from Terminal, the prompts and grants go to *Terminal.app* — the user is really granting their whole terminal disk access, and the grant doesn't travel with our app. Once we ship a proper signed `.app` bundle, the grants attach to *Dad Ware* itself. This — even more than Gatekeeper — is the reason the `.app` bundle matters.

4. **"Submit to Apple" must mean notarization, not the Mac App Store.** MAS apps are required to be sandboxed, and sandboxed apps cannot receive FDA or scan the disk — a store submission would kill the product's core function. The path is: Developer ID certificate → hardened-runtime codesign → notarize with `notarytool` → staple → distribute the DMG/zip ourselves. Users get a clean "Apple checked it for malware" open experience.

5. **Read-only doesn't reduce permission requirements.** TCC gates *reading* — that's the whole point of it — so "we never delete or move files" earns no technical discount. It is, however, the strongest trust message we have, and it belongs in every permission-related screen: *"Dad Ware only looks. It never deletes, moves, or uploads anything."*

6. **Permission grants are keyed to bundle ID + code signature.** Unsigned or ad-hoc-signed builds get their grants reset on every rebuild, which makes testing miserable and would make real users re-grant after updates. Pick the bundle ID once (e.g. `com.dadware.yourdad`) and never change it. (`tccutil reset All com.dadware.yourdad` resets grants for testing.)

## The Degradation Matrix (product decision, encoded in code)

Every scanner must know its permission tier and say something useful when denied — never a silent 0:

| Feature | Needs | Without it |
|---|---|---|
| Main storage walk, home folders | Auto-prompt folders | Prompts appear on first scan; a denial shows "Downloads skipped — you said no. Change your mind in System Settings." |
| Hidden caches sweep (HIDDEN-STORAGE Phase 1) | Nothing | Always works |
| Purgeable estimate, snapshots | Nothing | Always works |
| Trash, Mail, Messages, Photos internals | FDA | "Grant Full Disk Access to see this" + one-click deep link |

This matrix is the actual MVP scope decision: **the app must be genuinely useful with zero grants beyond the auto-prompts**, and FDA unlocks the bonus tier. Never hard-require FDA.

---

## Phase 1: Permission UX foundation (works in the CLI today)

No signing required; everything here carries forward into the `.app`.

1. **Prompt choreography.** Today the Desktop/Documents/Downloads prompts fire mid-scan, whenever the walk happens to reach each folder — dialogs with no context. Instead, at scan start, print one explanatory line ("macOS will ask about a few folders — Dad Ware only reads sizes, never contents or changes") and then deliberately `os.listdir()` each auto-prompt folder in a fixed order so all dialogs happen up front, with context.
2. **Per-folder detection.** Extend `utils/permissions.py`: distinguish "TCC-denied" (EPERM on a folder the user owns) from ordinary POSIX errors, per folder. Record grant state in `scan_data['permission_status']` per-folder, not just the single FDA boolean.
3. **Degradation copy.** Implement the matrix above in renderers — every denied area gets its one-line explanation and fix path in both terminal and HTML output.
4. **FDA deep link.** Where FDA instructions are printed, also run `open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"` (behind a "want me to open it? [y/N]" in CLI mode).

## Phase 2: The signed `.app` bundle

1. **PyInstaller `.app`.** Switch `yourdad.spec` from bare executable to a `.app` bundle (onedir mode — required for notarization-friendly signing). Bundle ID `com.dadware.yourdad`. The app's "UI" is: run scan (progress in a minimal window or just the log), then open the HTML report in the default browser — no SwiftUI.
2. **Info.plist usage strings.** These are the app's voice in the auto-prompt dialogs — dad tone, trust message:
   - `NSDesktopFolderUsageDescription`, `NSDocumentsFolderUsageDescription`, `NSDownloadsFolderUsageDescription`, `NSRemovableVolumesUsageDescription`, `NSNetworkVolumesUsageDescription` — e.g. "Dad Ware measures folder sizes to build your report card. It never changes or uploads anything."
3. **Sign + notarize.** Developer ID Application cert ($99/yr enrollment, already on the backlog), `codesign --options runtime` (hardened runtime; no special entitlements needed — FDA has no entitlement), `xcrun notarytool submit` + `xcrun stapler staple`. This is the "submitted to Apple" step.
4. **Ship.** DMG or zip on dadware.com / GitHub Releases. Verify on a clean machine (backlog item) — this should also resolve the Tahoe launch failure, which smells like unsigned-binary enforcement.

## Phase 3: First-run onboarding (the "install dialog" experience)

The closest macOS allows to accept-on-install, built with what we already have — HTML:

1. On first launch (no `~/.dadware` state), before any scan, generate and open a local **welcome page**: what Dad Ware does, the read-only promise, and what it will ask for — with a side-by-side of what the report shows *without* FDA vs. *with* FDA (Trash, Mail, Messages sizes). Honest sell, user chooses.
2. Buttons: "Run my first scan" (proceeds; auto-prompts fire with the Phase 1 choreography) and "Unlock the full report" → deep-links to the FDA pane with a 3-step illustrated walkthrough (drag Dad Ware into the list, toggle on, relaunch — macOS kills and restarts the app when FDA changes).
3. The app polls `check_full_disk_access()` and the report header always shows current status: "Full report ✓" or "Partial report — Trash and Mail hidden. Fix this →".
4. Store onboarding-completed state in `~/.dadware/` so it runs once.

## Testing

- `tccutil reset All com.dadware.yourdad` between runs to re-test the full grant flow; also test every-permission-denied and FDA-revoked-after-grant.
- Clean-machine matrix (ties into existing backlog): Intel + Apple Silicon, Sonoma/Sequoia/Tahoe; verify prompts attribute to Dad Ware (not Terminal) in the `.app` build, and grants survive an app update (same bundle ID + cert).
- Unit tests: per-folder TCC detection (mock EPERM), degradation copy presence in both renderers, onboarding state file logic.

## Out of Scope

- Mac App Store distribution (sandbox makes the product impossible — revisit only if the product changes).
- Requesting FDA-equivalent access via helper tools, launch daemons, or other escalation tricks. Not worth the trust cost for a tool whose brand is "safe."
- MDM/enterprise pre-approval profiles.
