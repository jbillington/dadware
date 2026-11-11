# Storage Scan Copy Inventory — for the dad-voice revision

Every user-facing string in the storage-scan experience, in the order the user meets it:
launch → volume pick → permission prompts → scan → terminal report → HTML report.
Fill in the **Revised copy** column, leave a row blank to keep it as-is.

**Status, Nov 7, 2026:** round one of the revisions is applied in the code (PR #29). **Current copy** is now what ships, and the **Revised copy** column is empty for the next round. Write `DELETE` alone in a Revised cell to remove a string; leave it blank to keep it. Struck-through rows were removed.

Notes for the reviewer:

- `{curly}` parts are dynamic values — keep a slot for them in any revision.
- Line numbers are as of Aug 28, 2026 and will drift; the string itself is the anchor.
- **Verified against the code Aug 28, 2026**, after the permission-UX and terminal-trim
  changes. Struck-through rows are strings that have been deleted — listed so a reviewer
  doesn't waste time rewriting copy that no longer ships.
- The CPU-scan experience (its terminal section, personality lines, and NEXT STEPS block) is
  **not** in scope here; it lives in the same files when you want a second pass.
- The AI prompt text (what gets pasted into ChatGPT/Claude) is its own document —
  `utils/llm_prompt.py` — and already has a backlog item for a rewrite, so it's excluded too.
- Current voice inconsistency worth noticing as you revise: the personality lines are
  lowercase dad-casual, the report card is teacher-formal ("Room for improvement"), and the
  scanner status lines are plain engineering ("→ scanning volume:"). Deciding which register
  each stage should use is the real review.

## 1. Launch

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 1.1 | Terminal banner | `askdad.py:172-175` | `────────` / ` Ask Dad for Mac v{VERSION}` / ` Build: {BUILD}` / `────────` | |
| 1.2 | First line after banner | `askdad.py:512` | `Alright, let me see what you've done to this computer. I'm going to start with selecting the Drive and then I'll scan through the mess you made.` | |

## 2. Volume selection

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 2.1 | Menu header (multiple volumes) | `utils/volumes.py:311` | `I got eyes on your drives, pick one:` | |
| 2.2 | Each menu row | `utils/volumes.py:236-239` | `{n}) {name} ({path}) - {total}, {used} used ({pct}%)` (+ ` [{skip_reason}]` when not scannable) | |
| 2.3 | Hidden-volumes note | `utils/volumes.py:246-249` | `First interesting find: drives that I won't bother scanning:` / `  - {name} ({path}) - {reason}` / `  If you want to scan these, later you can open the terminal app and run askdad --all-volumes and I'll check them out. Or askdad --volume PATH to scan one directly.` | |
| ~~2.4~~ | ~~Home-scan note~~ | — | **Removed Nov 7, 2026.** | |
| 2.5 | The prompt | `utils/volumes.py:322` | `Your choice? (Enter for {default}): ` | |
| 2.6 | Bad input | `utils/volumes.py:335` | `"{choice}" isn't a number from the list above, so I've stopped without scanning anything. Run me again and pick one.` (also shown when the input isn't a number at all) | |
| 2.7 | Ctrl+C / EOF | `utils/volumes.py:338` | `Ouch! You canceled me. Let's do this another time.` (Ctrl+C or Ctrl+D only) | |
| 2.8 | Single volume (no menu) | `utils/volumes.py:295` | `Only one drive here, so I'll dig through → {name} ({path}) - {total}, {used} used ({pct}%)` | |
| 2.9 | Non-interactive auto-select | `utils/volumes.py:305-306` | `→ Auto-selected {volume} [non-interactive session; use --volume PATH to choose a different volume]` | |
| 2.10 | Fallback when nothing scannable | `utils/volumes.py:282` | `Note: no plain storage volumes found; showing all mounted volumes.` | |
| 2.11 | No volumes at all | `utils/volumes.py:285` | `Error: No volumes found.` | |
| 2.12 | `--volume` path not found | `utils/volumes.py:270` | `Heads up: Volume '{path}' is not found or inaccessible. Choose again...` | |
| 2.13 | `--volume` points at a non-storage mount | `utils/volumes.py:266-268` | `Note: '{path}' looks like a {skip_reason}, not a storage device. Scanning it anyway since you asked for it.` | |

## 3. Permission choreography (new in Phase 1)

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 3.1 | Explainer before any dialog — **first run only** | `utils/permissions.py` `PROMPT_EXPLAINER` | `Alright, macOS is going to pop up questions to allow me to look through a few folders (Desktop, Documents, Downloads). Just approve it because I only read sizes, not contents, and this program has no AI in it or internet access, it's private to you.` | |
| 3.2 | CLI heads-up (first run, TTY only) | `utils/permissions.py` `CLI_PROMPT_HEADSUP` | `Heads-up: those dialogs will say "Terminal" wants access and you need to grant it so I can read the file sizes.` | |
| 3.2b | All granted (first run only) | `utils/permissions.py` `ALL_GRANTED_LINE` | `Desktop, Documents and Downloads are already open to me — no pop-ups needed.` | |
| 3.3 | Denied folders, at scan start | `askdad.py` (run_storage_scan) | `→ You did not give me access to: {folders} so I will have to skip them and won't include them. Next time approve the dialogs and give terminal Full Disk Access in settings.` / `  Make changes in System Settings → Privacy & Security → Files & Folders.` | |

## 4. Scanning

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 4.1 | Volume scan start | `askdad.py` | `Ok I'm going to look through this mess, wish me luck! → scanning volume: {path}` | |
| 4.2 | Live progress (rewrites in place) | `askdad.py:80-89` | `→ found {n:,} items... ({t}s elapsed)` | |
| 4.3 | Home-scan start | `askdad.py` | `→ scanning home directory for detailed breakdown: {path}` | |
| 4.4 | Library scan start | `askdad.py` | `→ scanning Mac app libraries...` | |
| 4.5 | Library scan partial | `askdad.py` | `   ⚠️  Mac library scan: {status}` | |
| 4.6 | Library scan Ctrl+C | `askdad.py` | `⚠️  Mac library scan interrupted by user` | |
| 4.7 | Library scan error | `askdad.py` | `⚠️  Mac library scan failed: {error}` | |
| 4.8 | `--no-mac-libraries` | `askdad.py` | `→ skipping Mac app libraries (--no-mac-libraries)` | |
| 4.9 | `--skip-protected` | `askdad.py` | `→ skipping protected directories (--skip-protected)` | |
| 4.10 | Cache scan start | `askdad.py` | `→ scanning hidden app caches...` | |
| 4.11 | Cache scan partial | `askdad.py` | `   ⚠️  Hidden cache scan: {status}` | |
| 4.12 | Snapshot check start | `askdad.py` | `→ checking local snapshots...` | |
| 4.13 | Snapshot check Ctrl+C / error | `askdad.py` | `⚠️  Snapshot check interrupted by user` / `⚠️  Snapshot check failed: {error}` | |
| 4.14 | Walk start | `scanners/storage.py:407-408` | `Scanning {path}...` / `→ digging through the attic...` | |
| 4.15 | Walk finished | `scanners/storage.py:613` | `→ found {n:,} items in {path}` | |

## 5. Full Disk Access notice (mid-run, when FDA missing)

**Restructured Aug 28, 2026.** Mid-run is now a two-line note only. The instructions
and the offer to open System Settings moved to the very end of the run (section 7b) —
macOS binds Full Disk Access at process start, so nothing toggled mid-scan can affect
the report being generated.

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 5.1 | Status line | `utils/permissions.py` `format_permission_status()` | `✅ Because you granted Full Disk Access to this terminal, I can measure every library` / `⚠️  This terminal does not have Full Disk Access, so I couldn't measure: {Lib1, Lib2}` + `   and won't be able to see your Trash and other apps' data. Change the setting and Ask Dad again if you want me to look through everything.` | |
| 5.2 | Carrying on | `askdad.py` | `   I'm getting back to my scan now.` | |
| ~~5.3~~ | ~~Instruction block mid-run~~ | — | **Moved to 7b.** `get_permission_instructions()` still exists in `utils/permissions.py` but is no longer printed anywhere — dead copy, worth deleting or reusing. | |
| ~~5.4~~ | ~~`--skip-protected` hint~~ | — | **Removed Aug 28, 2026.** | |

## 6. Terminal report

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 6.1 | Header | `renderers/terminal.py:60-62` | ` DAD'S REPORT CARD — Ask Dad v{VERSION}` / ` {hostname}  \|  User: {username}` / ` Date: {date}` | |
| 6.2 | Section title | `terminal.py:70` | `📦 STORAGE SCAN — {volume}` | |
| 6.3 | Folders header | `terminal.py:76` | `Top Folders (depth 2):` | |
| 6.4 | Files header | `terminal.py:89` | `Top 10 Largest Files:` | |
| 6.5 | Caches header | `terminal.py` | `Hidden App Caches: {total} total` — *(the three explainer lines were cut Aug 28, 2026; the report card explains what a cache is)* | |
| 6.6 | Caches caveats | `terminal.py:120-122` | `  (some cache folders are protected - sizes may be incomplete)` / `  (scan ran out of time - total is a floor, not the whole story)` | |
| 6.7 | Snapshots block | `terminal.py` | `Local Snapshots: {count}` / `  Oldest: {n} days old` / `  Older than macOS usually keeps. To reclaim now, run yourself:` / `    tmutil thinlocalsnapshots / 9999999999 4` — *(the two "why there's no size" lines were cut Aug 28, 2026; the report card carries that explanation)* | |
| 6.8 | Volume summary | `terminal.py:148` | `Total: {total}  \|  Used: {used} ({pct}%)  \|  Free: {free}` | |
| ~~6.9~~ | ~~Skipped-items counts~~ | — | **Removed Aug 28, 2026.** The terminal report no longer reports what the scan left out; the counts stay in the scan data for the report card to use. The terminal stays short on purpose. | |
| 6.10 | Dad quote block | `terminal.py:216` | `💬 Dad says:` then each comment in quotes | |
| 6.11 | Status line | `terminal.py:224` + `utils/formatters.py:39-46` | `Status: 🟢 all good` / `Status: 🟡 stable but cluttered` / `Status: 🔴 needs attention` | |
| 6.12 | Denied-folders notice | `terminal.py` | `🚪 Folders I couldn't check:` / `  No access to: {folders}` / `  Left out of the numbers above, not counted as zero.` / `  Change it: System Settings → Privacy & Security → Files & Folders` | |
| 6.13 | FDA notice | `terminal.py` | `⚠️  Couldn't measure everything:` / `  {libs} need Full Disk Access, so they're` / `  left blank above rather than counted as zero.` — *(the how-to moved to 7b Aug 28, 2026)* | |
| 6.14 | Tips header | `terminal.py:260` | `💡 Quick Wins:` then `  • {tip}` | |
| 6.15 | Footer | `terminal.py:269` | `Scan completed in {n} seconds` | |

## 7. Saving & opening the report

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 7.1 | Dev-mode note | `askdad.py:203` | `📁 Using test-reports directory: {dir}` | |
| 7.2 | Report link | `askdad.py:228-229` | `📊 Full report: file://{path}` / `   (opened in browser)` | |

## 7b. End-of-run Full Disk Access hand-off (when FDA missing)

**Added Aug 28, 2026.** Runs last, after the report is saved and opened, because a
Full Disk Access grant only applies to the *next* scan.

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 7b.1 | Header | `utils/permissions.py` `FDA_UPGRADE_HEADER` | `One thing that would make the next report better` | |
| 7b.2 | Body | `utils/permissions.py` `FDA_UPGRADE_BODY` | `Full Disk Access is switched off for Terminal, so parts of this report are blanks rather than numbers. Turning it on is a checkbox, and it only takes effect on the NEXT scan — macOS won't apply it to a program already running.` | |
| 7b.3 | Steps | `utils/permissions.py` `FDA_UPGRADE_STEPS` | `1. I open System Settings → Privacy & Security → Full Disk Access` / `2. Switch Terminal on (add it with + if it isn't listed)` / `3. Quit Terminal completely (⌘Q) and open it again` / `4. Run the scan once more — the blanks fill in` | |
| 7b.4 | The offer (TTY only) | `utils/permissions.py` `offer_full_disk_access_settings()` | `Open that settings pane for you now? (this report is already finished either way) [y/N] ` | |
| 7b.5 | After yes | same | `→ Opened System Settings. Flip Terminal on, quit Terminal (⌘Q), reopen it,` / `  and run the scan again to fill in the blanks.` | |
| 7b.6 | If it won't open | same | `→ Couldn't open it automatically. System Settings → Privacy & Security → Full Disk Access.` | |

## 8. Personality — the dad voice itself (storage lines)

All from `personality/dad.py`. The verdict is capped at two lines; info notes append after.

| # | Trigger | Current copy | Revised copy |
|---|---|---|---|
| 8.1 | Downloads > 10 GB | `Hey Downloads looks like a total mess. Time to do some organization in there.` | |
| 8.2 | Downloads > 5 GB | `Found some fatties in Downloads. You need a cleanup day.` | |
| 8.3 | Desktop > 5 GB | `Desktop has some hefty files staring you right in the face!` | |
| 8.4 | Free space < 10% | `living on the edge. let's back away from the cliff.` | |
| 8.5 | Free space < 20% | `getting tight. time to make some room.` | |
| 8.6 | Nothing wrong | `This puppy looks fine! I'm proud of how tidy you are.` | |
| 8.7 | Absolute fallback | `I think this computer is in good shape! Nicely done.` | |
| 8.8 | Caches > 20 GB (info note) | `Separately, {size} is a pretty large cache. These are storage that you can delete but may come back later. That's just apps being apps.` | |
| 8.9 | `{size} is eaten up by app caches but they just fill back up over time. That's apps being apps.` | |
| 8.10 | Stale snapshots, oldest known | `your mac's been holding {n} copies of itself from Time Machine. Oldest one {d} days back. sentimental, but expensive.` | |
| 8.11 | Stale snapshots, no age | `your mac's been holding on to {n} old copies of itself. sentimental, but expensive.` | |
| 8.12 | Tip: big Downloads | `Start with {path} folder` | |
| 8.13 | Tip: crowded Downloads | `Review {path} folder` | |
| 8.14 | Tip: Desktop | `Clean up {path} folder` | |
| 8.15 | Tip: low space | `Free up space urgently - system may slow down` | |
| 8.16 | Tip: one huge file | `Review large file: {name} ({size})` | |

## 9. HTML report — header & report card

All from `renderers/html.py`.

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 9.1 | Browser tab title | `Dad's Report Card - {date}` | |
| 9.2 | Page header | `DAD'S REPORT CARD` / `Ask Dad v{VERSION}  \|  {date}` | |
| 9.3 | Section title | `📊 Storage Report Card - {volume}` | |
| 9.4 | Grade comment ladder | `Excellent!` (≥90) / `Good job!` (≥80) / `Room for improvement` (≥70) / `Needs work` (≥60) / `Critical issues` (<60) — shown as `{score}/100 - {comment}` | |
| 9.5 | Storage headline | `{used} used of {total} — {free} free ({pct}%)` | |
| 9.6 | Metric tiles | `Top 10 Folders` / `Top 25 Files` / `Reclaimable` | |
| 9.7 | Reclaimable caption | `You can free up {pct}% of used space by deleting or offloading your top 25 largest files` | |
| 9.9 | Breakdown title | `Grade Breakdown` | |
| 9.10 | Free Space row | Title `Free Space (50% of grade)`; note `Use the report below to improve this because it is what slows your Mac down.` | |
| 9.11 | Home Folders Ratio row | Title `Home Folders Ratio (15% of grade)`; note `These are your files you saved, excluding Downloads and Desktop` | |
| 9.12 | Clutter row | Title `Clutter (20% of grade)`; note `This is all the junk in Downloads and on your Desktop.` | |
| 9.13 | Mac Apps row | Title `Mac Apps: Photos, Music, iMessages, & Mail ({15% of grade \| not counted in grade})`; note `These are harder to reduce in size, but there are strategies.` (the 9.14 reason follows it when not counted). The Messages "Attachments ... usually most of this" advice line under a D/F Messages row was removed. | |
| 9.14 | Library not-scored reasons | `needs Full Disk Access to measure - not counted toward the overall grade` / `scan incomplete - not counted toward the overall grade` / `not scanned - not counted toward the overall grade` | |
| 9.15 | Per-library badges | `(skipped: {reason})` / `(error)` / `(interrupted)` / `(needs Full Disk Access)` | |
| 9.16 | Partial-scan notice | `⚠️ Partial Scan: Some libraries were skipped due to time limits: {list}` | |
| 9.17 | Interrupted notice | `⚠️ Scan Interrupted: Library scan was interrupted. Results may be incomplete.` | |

## 10. HTML report — permission notices

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 10.1 | Denied folders | `🚪 Folders I couldn't check` / `No access to: {folders}` / `You told macOS not to let me look there — that's fine, and nothing is broken. Those folders are left out of the numbers above rather than counted as zero. If you change your mind: System Settings → Privacy & Security → Files & Folders, then run the scan again.` | |
| 10.2 | FDA notice | `⚠️ Permission Notice` / `Full Disk Access required for: {libs}` / `Can't see those libraries yet — they're marked "needs Full Disk Access" above. To grant access:` / `Open the Full Disk Access settings pane (or: System Settings → Privacy & Security → Full Disk Access)` / `Click the lock icon and enter your password` / `Click + and add Terminal.app (or your IDE)` / `Make sure the checkbox is checked ✅` / `Restart Terminal/IDE and run the scan again` / `Note: If you're running Ask Dad from Cursor, VS Code, or another IDE, add that application instead of Terminal.` | |

## 11. HTML report — Dad says & folders/files

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 11.1 | Quote block header | `💬 Dad says:` (each comment rendered in quotes), then the quick-win tips (section 8) as a short bullet list, then a `View next steps` link to the Next Steps block | |
| 11.2 | Chart headers | `Top 10 Home Folders` / `Top 10 Other Folders` (fixed titles, even with fewer than 10 rows; a drive report keeps `Folders`), each with a small hint `Click to view top items` | |
| ~~11.3~~ | ~~Truncation notes~~ | **Removed Nov 11, 2026.** The titles now say top 10. | |
| 11.4 | Expanded panel headers | `Subfolders` / `Top Files in {folder}` / `All Files ({n} total)` | |
| 11.5 | Files table | `Top Largest Files` / columns `File ↕` `Size ↕` `Actions` | |
| 11.6 | Buttons & tooltips | `Reveal in Finder` / tooltip `Copy command to open in Finder` / link tooltip `Click to view in browser` | |

## 12. HTML report — Hidden App Caches

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 12.1 | Header + tally | `Hidden App Caches` / `{total} across {n} folders` | |
| 12.2 | Intro | `This is where a chunk of your disk went, and it is normal but it is hidden.` | |
| 12.3 | Explainer point 1 | `Clearing a cache is like deleting a copy of something the app can get again. It's temporary relief, but the bloat will return.` | |
| 12.4 | Explainer point 2 | `Clearing a cache is a safe way to get space back today - just don't expect it to stay gone.` | |
| ~~12.5~~ | ~~Explainer point 3~~ | **Removed Nov 7, 2026.** | |
| 12.6 | Explainer point 4 | `Dragging an app to the Trash leaves its cache behind, so if you're getting rid of an app, those leftovers are the ones worth a look.` | |
| ~~12.7~~ | ~~Read-only line~~ | **Removed Nov 11, 2026.** The Next Steps Important box already says it. | |
| 12.8 | Remainder note | `Plus {size} in smaller caches not listed individually.` | |
| 12.9 | Caveats | `⚠️ Some cache folders are protected by macOS, so those sizes may be incomplete. Granting Full Disk Access lets Ask Dad see all of them.` / `⚠️ This scan ran out of time before measuring every folder, so the total above is a floor, not the whole story.` | |

## 13. HTML report — Local Snapshots

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 13.1 | Header + tally | `Local Snapshots` / `{n} local snapshots, the oldest {from today \| from yesterday \| N days old}` | |
| 13.2 | Intro | `A snapshot is a local Time Machine backup kept on the same drive.` | |
| 13.3 | Fresh-snapshot variant | `That's Time Machine working exactly as intended — it keeps about a day's worth and clears them out on its own. Nothing to do here.` | |
| 13.4 | Stale-snapshot variant | `Time Machine keeps about a day of these and usually tidies up after itself. Yours have been sitting longer than that, which normally means macOS hasn't needed the space back yet.` | |
| 13.5 | Table columns | `Taken` / `Age` / `macOS can reclaim it` (values `Today`, `1 day`, `{n} days`, `Yes`/`No`/`Unknown`) | |
| 13.6 | No-size explainer | `There's no honest way to determine the size of these snapshots.` | |
| 13.7 | OS-update note | `There {is/are} also {n} system update snapshot{s} that belong to macOS — best to leave these be.` | |
| 13.8 | Reclaim-now block | `You can get some space back today by connecting your Time Machine drive and letting a backup finish.` / `If you're in a hurry, this Terminal command asks macOS to thin them out. Ask Dad won't run it for you, so copy it and run it yourself:` + `tmutil thinlocalsnapshots / 9999999999 4` + `And if you don't use Time Machine, turn off Automatic Backup in System Settings so your Mac stops making these.` | |

## 14. HTML report — Quick Wins, Next Steps, AI, footer

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| ~~14.1~~ | ~~Tips header~~ | **Removed Nov 11, 2026.** The yellow Quick Wins box is gone; its tips moved into Dad says (11.1). | |
| 14.2 | Next Steps title | `📋 NEXT STEPS` (the block has the anchor id `next-steps`) | |
| 14.3 | Next Steps list | `Click folder bars above to see subfolders and top files` / `Click "Reveal in Finder" button - copies command to clipboard` / `Open Terminal (Cmd+Space, type "Terminal") and paste (Cmd+V), press Enter` / `Finder opens with the file/folder selected` / `Delete files manually (send to Trash for safe undo)` / `Start with largest items - easiest wins first` | |
| 14.4 | Read-only callout | `⚠️ Important: Ask Dad does not delete files for you, you must delete files manually from Finder. Don't empty Trash until you are sure you want it gone for good.` | |
| 14.5 | AI section | `💬 Ask AI About This Report` / `Get personalized advice from AI: Copy the prompt below and paste it into ChatGPT, Claude, or any AI assistant. The prompt includes all your system specs and scan results, so the AI can give you specific recommendations for your Mac.` / button `📋 Copy Prompt to Clipboard` / `✓ Copied!` | |
| 14.6 | AI follow-up tip | `💡 Tip: After pasting, you can ask follow-up questions like:` / `"Should I quit [specific app name]?"` / `"What happens if I delete [specific file/folder]?"` / `"How do I prevent this from happening again?"` | |
| 14.7 | Page footer | `Ask Dad v{VERSION}, a DadWare joint. Happy cleaning` | |
| 14.8 | Reveal-in-Finder toast (JS) | `✓ Command copied to clipboard!` / `Press Cmd+V in Terminal, then press Enter to open Finder.` | |
| 14.9 | Clipboard failures (JS) | `Failed to copy. Please manually select and copy the text.` / `Could not copy to clipboard. Please copy manually:\n{cmd}` | |
