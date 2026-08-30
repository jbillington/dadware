# Storage Scan Copy Inventory — for the dad-voice revision

Every user-facing string in the storage-scan experience, in the order the user meets it:
launch → volume pick → permission prompts → scan → terminal report → HTML report.
Fill in the **Revised copy** column, leave a row blank to keep it as-is.

Notes for the reviewer:

- `{curly}` parts are dynamic values — keep a slot for them in any revision.
- Line numbers are as of Aug 28, 2026 and will drift; the string itself is the anchor.
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
| 1.2 | First line after banner | `askdad.py:512` | `Starting storage scan (Build {BUILD})...` | |

## 2. Volume selection

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 2.1 | Menu header (multiple volumes) | `utils/volumes.py:311` | `Available volumes:` | |
| 2.2 | Each menu row | `utils/volumes.py:236-239` | `{n}) {name} ({path}) - {total}, {used} used ({pct}%)` (+ ` [{skip_reason}]` when not scannable) | |
| 2.3 | Hidden-volumes note | `utils/volumes.py:246-249` | `Not shown (not a storage device):` / `  - {name} ({path}) - {reason}` / `  Use --all-volumes to include them, or --volume PATH to scan one directly.` | |
| 2.4 | Home-scan note | `utils/volumes.py:321` | `Note: Home directory will be scanned separately for detailed breakdown.` | |
| 2.5 | The prompt | `utils/volumes.py:322` | `Pick one [{default}]: ` | |
| 2.6 | Bad input | `utils/volumes.py:335` | `Invalid choice: {choice}` | |
| 2.7 | Ctrl+C / EOF | `utils/volumes.py:338` | `Cancelled.` | |
| 2.8 | Single volume (no menu) | `utils/volumes.py:295` | `→ Using {name} ({path}) - {total}, {used} used ({pct}%)` | |
| 2.9 | Non-interactive auto-select | `utils/volumes.py:305-306` | `→ Auto-selected {volume} [non-interactive session; use --volume PATH to choose a different volume]` | |
| 2.10 | Fallback when nothing scannable | `utils/volumes.py:282` | `Note: no plain storage volumes found; showing all mounted volumes.` | |
| 2.11 | No volumes at all | `utils/volumes.py:285` | `Error: No volumes found.` | |
| 2.12 | `--volume` path not found | `utils/volumes.py:270` | `Warning: Volume '{path}' not found or inaccessible. Prompting for selection...` | |
| 2.13 | `--volume` points at a non-storage mount | `utils/volumes.py:266-268` | `Note: '{path}' looks like a {skip_reason}, not a storage device. Scanning it anyway since you asked for it.` | |

## 3. Permission choreography (new in Phase 1)

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 3.1 | Explainer before any dialog | `utils/permissions.py` `PROMPT_EXPLAINER` | `macOS may ask about a few folders (Desktop, Documents, Downloads) — I only read sizes, never contents, and I never change anything.` | |
| 3.2 | CLI heads-up (TTY only) | `utils/permissions.py` `CLI_PROMPT_HEADSUP` | `Heads-up: those dialogs will say "Terminal" wants access — that's macOS attributing the request to the app that launched me.` | |
| 3.3 | Denied folders, at scan start | `askdad.py` (run_storage_scan) | `→ no access to: {folders} — skipped and labeled in the report, never silently zeroed.` / `  macOS remembers that choice; change it in System Settings → Privacy & Security → Files & Folders.` | |

## 4. Scanning

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 4.1 | Volume scan start | `askdad.py` | `→ scanning volume: {path}` | |
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

## 5. Full Disk Access notice (mid-run, when FDA missing)

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 5.1 | Status line | `utils/permissions.py` `format_permission_status()` | `✅ Full Disk Access granted - all libraries accessible` / `⚠️  Full Disk Access required for {Library} library` / `⚠️  Full Disk Access required for: {Lib1, Lib2}` | |
| 5.2 | Instruction block | `utils/permissions.py` `get_permission_instructions()` | `To grant Full Disk Access:` / `1. Open System Settings — Click Apple menu → System Settings — Or press Cmd+Space and search "System Settings"` / `2. Go to Privacy & Security — Click "Privacy & Security" in the sidebar — Scroll down to "Full Disk Access"` / `3. Add Terminal (or your IDE) — Click the lock icon (enter password if needed) — Click the + button — Navigate to Applications → Utilities — Select "Terminal.app" — Make sure the checkbox is checked ✅` / `4. Restart Terminal — Close and reopen Terminal for changes to take effect` / `Shortcut: this command jumps straight to the right pane: open "x-apple.systempreferences:…AllFiles"` / `Note: If you're running from Cursor, VS Code, or another IDE, add that application instead of Terminal.` | |
| 5.3 | Deep-link offer (TTY only) | `utils/permissions.py` `offer_full_disk_access_settings()` | `Open System Settings → Full Disk Access now? [y/N] ` | |
| 5.4 | Continuing | `askdad.py` | `Continuing scan... (areas without access are labeled in the report)` / `Use --skip-protected to skip scanning protected directories entirely.` | |

## 6. Terminal report

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 6.1 | Header | `renderers/terminal.py:60-62` | ` DAD'S REPORT CARD — Dad Ware v0.1` / ` {hostname}  \|  User: {username}` / ` Date: {date}` — *(the `v0.1` is a filed bug; VERSION is 0.7)* | |
| 6.2 | Section title | `terminal.py:70` | `📦 STORAGE SCAN — {volume}` | |
| 6.3 | Folders header | `terminal.py:76` | `Top Folders (depth 2):` | |
| 6.4 | Files header | `terminal.py:89` | `Top 10 Largest Files:` | |
| 6.5 | Caches header + explainer | `terminal.py:106-112` | `Hidden App Caches: {total} total` / `  (working files apps keep out of sight - not counted in your grade)` / `  (safe to clear if you need space today, but they fill back up;` / `   worth clearing for good only when you delete the app itself)` | |
| 6.6 | Caches caveats | `terminal.py:120-122` | `  (some cache folders are protected - sizes may be incomplete)` / `  (scan ran out of time - total is a floor, not the whole story)` | |
| 6.7 | Snapshots block | `terminal.py:132-139` | `Local Snapshots: {count}` / `  Oldest: {n} days old` / `  (Time Machine copies kept on this drive - often why deleting` / `   files doesn't free up space. macOS doesn't report their size.)` / `  Older than macOS usually keeps. To reclaim now, run yourself:` / `    tmutil thinlocalsnapshots / 9999999999 4` | |
| 6.8 | Volume summary | `terminal.py:148` | `Total: {total}  \|  Used: {used} ({pct}%)  \|  Free: {free}` | |
| 6.9 | Skip count | `terminal.py:154` | `({n} items skipped due to permissions)` | |
| 6.10 | Dad quote block | `terminal.py:216` | `💬 Dad says:` then each comment in quotes | |
| 6.11 | Status line | `terminal.py:224` + `utils/formatters.py:39-46` | `Status: 🟢 all good` / `Status: 🟡 stable but cluttered` / `Status: 🔴 needs attention` | |
| 6.12 | Denied-folders notice | `terminal.py` | `🚪 Folders I couldn't check:` / `  No access to: {folders}` / `  Left out of the numbers above, not counted as zero.` / `  Change it: System Settings → Privacy & Security → Files & Folders` | |
| 6.13 | FDA notice | `terminal.py` | `⚠️  Permission Notice:` / `  Full Disk Access required for: {libs}` / `  Those libraries are marked in the report, not counted as zero` / `  Jump straight to the toggle:` / `  open "x-apple.systempreferences:…AllFiles"` | |
| 6.14 | Tips header | `terminal.py:260` | `💡 Quick Wins:` then `  • {tip}` | |
| 6.15 | Footer | `terminal.py:269` | `Scan completed in {n} seconds` | |

## 7. Saving & opening the report

| # | Where | Source | Current copy | Revised copy |
|---|---|---|---|---|
| 7.1 | Dev-mode note | `askdad.py:203` | `📁 Using test-reports directory: {dir}` | |
| 7.2 | Report link | `askdad.py:228-229` | `📊 Full report: file://{path}` / `   (opened in browser)` | |

## 8. Personality — the dad voice itself (storage lines)

All from `personality/dad.py`. The verdict is capped at two lines; info notes append after.

| # | Trigger | Current copy | Revised copy |
|---|---|---|---|
| 8.1 | Downloads > 10 GB | `downloads looks like a garage shelf. time to label a box.` | |
| 8.2 | Downloads > 5 GB | `downloads is getting crowded. regular cleanup day?` | |
| 8.3 | Desktop > 5 GB | `desktop isn't meant to be storage. it's a desk, not a box of junk.` | |
| 8.4 | Free space < 10% | `living on the edge. let's back away from the cliff.` | |
| 8.5 | Free space < 20% | `getting tight. time to make some room.` | |
| 8.6 | Nothing wrong | `looks fine. don't mess with success.` | |
| 8.7 | Absolute fallback | `everything looks good.` | |
| 8.8 | Caches > 20 GB (info note) | `{size} of that is apps keeping their own scratch paper. not junk, not yours to file - it just refills if you clear it.` | |
| 8.9 | Caches > 5 GB (info note) | `{size} is app caches. that's apps being apps. clear it if you need the room today, but don't expect it to stay gone.` | |
| 8.10 | Stale snapshots, oldest known | `your mac's been holding {n} copies of itself, oldest one {d} days back. sentimental, but expensive.` | |
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
| 9.2 | Page header | `DAD'S REPORT CARD` / `Dad Ware v0.1  \|  {date}` — *(v0.1 is the filed bug)* | |
| 9.3 | Section title | `📊 Storage Report Card - {volume}` | |
| 9.4 | Grade comment ladder | `Excellent!` (≥90) / `Good job!` (≥80) / `Room for improvement` (≥70) / `Needs work` (≥60) / `Critical issues` (<60) — shown as `{score}/100 - {comment}` | |
| 9.5 | Storage headline | `{used} used of {total} — {free} free ({pct}%)` | |
| 9.6 | Metric tiles | `Top 10 Folders` / `Top 25 Files` / `Reclaimable` | |
| 9.7 | Reclaimable caption | `You can free up {pct}% of used space by deleting or offloading your top 25 largest files` | |
| 9.8 | Caches aside | `Apps are also holding {size} in caches. What that means - it is not counted in your grade.` | |
| 9.9 | Breakdown title | `Grade Breakdown` | |
| 9.10 | Free Space note | `How much room is left on the drive. Half your grade, because it is the one that actually slows a Mac down.` | |
| 9.11 | Home Folders Ratio note | `How much of your used space is your own files rather than the system's. 15% of your grade.` | |
| 9.12 | Home Folders Clutter note | `Downloads and Desktop - the two folders that fill up fastest, and the quickest to clear. 20% of your grade.` | |
| 9.13 | Mac App Libraries note | `Your Photos, Music, Messages and Mail libraries, averaged. {15% \| not counted}.` | |
| 9.14 | Library not-scored reasons | `needs Full Disk Access to measure - not counted toward the overall grade` / `scan incomplete - not counted toward the overall grade` / `not scanned - not counted toward the overall grade` | |
| 9.15 | Per-library badges | `(skipped: {reason})` / `(error)` / `(interrupted)` / `(needs Full Disk Access)` | |
| 9.16 | Partial-scan notice | `⚠️ Partial Scan: Some libraries were skipped due to time limits: {list}` | |
| 9.17 | Interrupted notice | `⚠️ Scan Interrupted: Library scan was interrupted. Results may be incomplete.` | |

## 10. HTML report — permission notices

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 10.1 | Denied folders | `🚪 Folders I couldn't check` / `No access to: {folders}` / `You told macOS not to let me look there — that's fine, and nothing is broken. Those folders are left out of the numbers above rather than counted as zero. If you change your mind: System Settings → Privacy & Security → Files & Folders, then run the scan again.` | |
| 10.2 | FDA notice | `⚠️ Permission Notice` / `Full Disk Access required for: {libs}` / `Can't see those libraries yet — they're marked "needs Full Disk Access" above, never counted as zero. To grant access:` / `Open the Full Disk Access settings pane (or: System Settings → Privacy & Security → Full Disk Access)` / `Click the lock icon and enter your password` / `Click + and add Terminal.app (or your IDE)` / `Make sure the checkbox is checked ✅` / `Restart Terminal/IDE and run the scan again` / `Note: If you're running from Cursor, VS Code, or another IDE, add that application instead of Terminal.` | |

## 11. HTML report — Dad says & folders/files

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 11.1 | Quote block header | `💬 Dad says:` (each comment rendered in quotes) | |
| 11.2 | Chart headers | `Home Folders` / `Other Folders` | |
| 11.3 | Truncation notes | `Only top 10 home folders displayed` / `Only top 10 other folders displayed` | |
| 11.4 | Expanded panel headers | `Subfolders` / `Top Files in {folder}` / `All Files ({n} total)` | |
| 11.5 | Files table | `Top Largest Files` / columns `File ↕` `Size ↕` `Actions` | |
| 11.6 | Buttons & tooltips | `Reveal in Finder` / tooltip `Copy command to open in Finder` / link tooltip `Click to view in browser` | |

## 12. HTML report — Hidden App Caches

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 12.1 | Header + tally | `Hidden App Caches` / `{total} across {n} folders` | |
| 12.2 | Intro | `This is where a chunk of your disk went, and it is normal. Apps keep working files in folders Finder doesn't show you. Nothing here is a mistake you made, and none of it counts against your grade.` | |
| 12.3 | Explainer point 1 | `A cache is not the app, and not your files. Clearing Spotify's cache keeps your playlists. Clearing your browser's keeps your tabs and logins. You are deleting a copy of something the app can get again.` | |
| 12.4 | Explainer point 2 | `They fill back up. Delete one and the app quietly rebuilds it as you use it. So clearing a cache is a safe way to get space back today - just don't expect it to stay gone.` | |
| 12.5 | Explainer point 3 | `Mostly, leave them alone. If you are not short on space right now, there is nothing to do here. A full cache is an app doing its job.` | |
| 12.6 | Explainer point 4 | `The exception is an app you are getting rid of. Dragging an app to the Trash leaves its cache behind - macOS does not clean up after it. That is the one time clearing it actually stays cleared.` | |
| 12.7 | Read-only line | `Dad Ware never deletes anything. This is just so you know where it went.` | |
| 12.8 | Remainder note | `Plus {size} in smaller caches not listed individually.` | |
| 12.9 | Caveats | `⚠️ Some cache folders are protected by macOS, so those sizes may be incomplete. Granting Full Disk Access lets Dad Ware see all of them.` / `⚠️ This scan ran out of time before measuring every folder, so the total above is a floor, not the whole story.` | |

## 13. HTML report — Local Snapshots

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 13.1 | Header + tally | `Local Snapshots` / `{n} local snapshots, the oldest {from today \| from yesterday \| N days old}` | |
| 13.2 | Intro | `Ever deleted a pile of files and watched your free space not budge? This is usually why. A snapshot is a local Time Machine backup kept on the same drive, holding on to the old version of everything you removed.` | |
| 13.3 | Fresh-snapshot variant | `That's Time Machine working exactly as intended — it keeps about a day's worth and clears them out on its own. Nothing to do here.` | |
| 13.4 | Stale-snapshot variant | `Time Machine keeps about a day of these and usually tidies up after itself. Yours have been sitting longer than that, which normally means macOS hasn't needed the space back yet — it will reclaim them automatically when something actually needs room.` | |
| 13.5 | Table columns | `Taken` / `Age` / `macOS can reclaim it` (values `Today`, `1 day`, `{n} days`, `Yes`/`No`/`Unknown`) | |
| 13.6 | No-size explainer | `Why there's no size next to these. Snapshots share storage with each other, so there's no honest way to say "this one is 4 GB" — delete one and the rest appear to grow. Finder shows a single "purgeable" figure covering all of it, but macOS doesn't hand that number to tools like this one. Dad would rather tell you that than make a number up.` | |
| 13.7 | OS-update note | `There {is/are} also {n} system update snapshot{s}, not listed above. Those belong to macOS — one of them may be what your Mac is running from right now — so leave them be.` | |
| 13.8 | Reclaim-now block | `If you need the space back today, connect your Time Machine drive and let a backup finish — that's the clean way. In a hurry, this Terminal command asks macOS to thin them out (Dad Ware never runs anything itself; copy it and run it yourself):` + `tmutil thinlocalsnapshots / 9999999999 4` + `And if you don't use Time Machine any more, turn off Automatic Backup in System Settings so your Mac stops making new ones.` | |

## 14. HTML report — Quick Wins, Next Steps, AI, footer

| # | Where | Current copy | Revised copy |
|---|---|---|---|
| 14.1 | Tips header | `💡 Quick Wins:` (items are the tips from section 8) | |
| 14.2 | Next Steps title | `📋 NEXT STEPS` | |
| 14.3 | Next Steps list | `Click folder bars above to see subfolders and top files` / `Click "Reveal in Finder" button - copies command to clipboard` / `Open Terminal (Cmd+Space, type "Terminal") and paste (Cmd+V), press Enter` / `Finder opens with the file/folder selected` / `Delete files manually (send to Trash for safe undo)` / `Start with largest items - easiest wins first` | |
| 14.4 | Read-only callout | `⚠️ Important: This tool is read-only. You must delete files manually from Finder. Trash = safe undo.` | |
| 14.5 | AI section | `💬 Ask AI About This Report` / `Get personalized advice from AI: Copy the prompt below and paste it into ChatGPT, Claude, or any AI assistant. The prompt includes all your system specs and scan results, so the AI can give you specific recommendations for your Mac.` / button `📋 Copy Prompt to Clipboard` / `✓ Copied!` | |
| 14.6 | AI follow-up tip | `💡 Tip: After pasting, you can ask follow-up questions like:` / `"Should I quit [specific app name]?"` / `"What happens if I delete [specific file/folder]?"` / `"How do I prevent this from happening again?"` | |
| 14.7 | Page footer | `Dad Ware v0.1 - Read-only system analysis tool` — *(v0.1 is the filed bug)* | |
| 14.8 | Reveal-in-Finder toast (JS) | `✓ Command copied to clipboard!` / `Press Cmd+V in Terminal, then press Enter to open Finder.` | |
| 14.9 | Clipboard failures (JS) | `Failed to copy. Please manually select and copy the text.` / `Could not copy to clipboard. Please copy manually:\n{cmd}` | |
