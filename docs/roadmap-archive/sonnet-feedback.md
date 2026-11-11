# Sonnet feedback on the storage scan

Written 2026-11-05 by Claude Sonnet 5.5 after reading `test-reports/storage_2026-11-05_21-41.html` and its `.json`.
Machine: MacBook Pro (MacBookPro14,2), Intel i7-7567U, 2 cores, 16 GB RAM, macOS 13.7.8, 250.7 GB disk (91% full).

## Speed

The run took **203.9 s** (`duration_seconds`). The only phase timings saved in the report are
hidden caches (36.7 s) and Trash (0.03 s). The remaining ~165 s is the volume walk plus the Mac library
measurements, and the report does not split it out. Run `python askdad.py --timings` for the real breakdown.

**Guess (not profiled): 60-90 s is realistic on this Mac; 45-60 s with more work.**

Where the time probably goes, and what to try:

- **Phases run one after another.** The ~37 s hidden-cache scan (`du` per folder) could run concurrently with the
  main walk. This alone saves about 35 s.
- **The walk is single-threaded Python on a 2-core Intel.** `os.scandir` releases the GIL while waiting on disk, so
  3-4 threads walking different top-level folders might give around 2x on the walk. Unverified.
- **Messages and Caches are sized separately and expensively.** A plain `du -sk` on just `~/Library/Messages` and
  `~/Library/Caches` took 22 s here. Measure them concurrently or reuse walk results.
- **Repeat runs could be much faster.** Caching folder sizes keyed on directory mtime might bring a second scan to 10-20 s.
  Unverified, and the cache invalidation needs care.

## Report content

1. **The Library total is partial and unlabeled.** The report shows Library at 36.3 GB, but the walk excludes
   `Library/Messages` (30.0 GB by `du`) and `Library/Caches` (15.4 GB). Real Library is closer to ~80 GB. The Library
   subfolder list has no Caches or Messages row. Either label the total as partial, or add the separately measured
   sizes back in with a note. `CHANGELOG.md` (around line 38) already flags this as an open decision: "the same
   gigabytes are visible in two places, and the report does not yet say so." In this report it went the other way
   (they are in neither place under Library).
2. **The biggest item is hidden.** Messages (~30-32 GB) is the largest single thing on the disk and does not appear in
   top folders or top files. It only shows up under Mac App Libraries.
3. **The advice fits the data.** "Living on the edge" matches 91% used with 22.4 GB free. The stale Time Machine
   snapshot (242 days old, purgeable) is a good catch.
4. **Easy wins the report surfaces** (all left alone, since this Mac is deliberately full of test data):
   `Install macOS Catalina.app` (7.7 GB, kept for an older Mac), `omarchy-4.0.2.iso` (6.2 GB), Messages cache (8.5 GB),
   Voice Memos recordings (~5 GB).

## Why Messages and Caches are excluded from the walk

`utils/path_utils.py:228` (`/Library/Caches/`) and `:238` (`/Library/Messages`) are excluded on purpose. There is no
code comment, so this is inferred from `CHANGELOG.md` and `docs/roadmap-archive/HIDDEN-STORAGE-PLAN.md`:

- **Caches:** a single "Caches" total is opaque. `scanners/hidden_storage.py` sizes each subfolder with a friendly app
  name instead. Caches are also "information, not a grade".
- **Messages and Mail:** macOS protects them (Full Disk Access). Without it a walk returns silent zeros. The separate
  Mac App Libraries scanner checks permissions first and reports "needs Full Disk Access" rather than a false 0 B.

## Other notes

- `excluded_count` was 6137 and `denied_count` was 9, so permissions were fine on this run.
- The 21.1 MB Trash and the permission checks all reported complete.

## Feedback on the AI prompt at the end of the report

Reviewed the same report's closing "paste this into an AI" prompt (about 4,400 characters).

### What works
- Clear sections, and the system specs give the AI real context.
- The snapshot note is honest that sizes can't be measured.
- The Hidden Caches section says the main scan excludes caches.
- It asks for specific actions for the user's Mac model.

### Moved elsewhere
- **Items 1-3** (ambiguous `Library`, undisclosed exclusions, two "Messages" labels) are now
  **Bug #10**, a "Fix first" entry at the top of `BACKLOG.md`.
- **The speed suggestions** are under "Scan Speed and Chart Design" in `BACKLOG.md`.

### Resolved Nov 11, 2026 (PR #33)

Items 4 to 6 and the suggested improvements below were handled when the storage prompt was rebuilt: largest files show their folder; the model is asked whether storage is upgradeable (instead of the scan guessing); the "Architecture: i386" and double-storage quirks were already fixed; "things I want to keep" became Step 1, where the model asks before it plans; risk is a one-sentence explanation per item, not a ranking; the username never appears (`~` paths) and a checkbox drops the file names; the fixed six-question tail is gone; and Quick Wins left the prompt. The text below is the original review.

### Remaining problems
4. **Largest files show only filenames.** `VB-ROYAL.blob` and `RM Mk2 001.nkx` mean nothing without a path.
   They are UJAM and Native Instruments sample libraries, and the AI can't tell. `llm_prompt.py` prints
   `os.path.basename(path)`; include the parent folder or app name.
5. **Q4 ("do I need to upgrade my storage?") has no hardware context.** On a 2017 MacBook Pro the internal
   drive can't be upgraded, so the useful answers are external or cloud storage. Say so, or say whether the
   internal storage is upgradeable.
6. **Small inaccuracies:**
   - `Architecture: i386` is misleading on a 64-bit x86_64 Mac; an AI may talk about 32-bit.
   - `Storage 1` and `Storage 2` are the same 250.69 GB drive listed twice.
   - Both look like display quirks from the system-info parsing.

### Suggested improvements
- **A "things I want to keep" field.** This Mac holds deliberate test data, music libraries and an
  installer for an older Mac. An AI will suggest deleting them unless told. A short user-editable line at the
  top would fix that.
- **Ask for safer answers.** Add something like "rank by risk, say how to verify before deleting, and don't
  guess about files you can't identify."
- **Make Quick Wins useful.** "Free up space urgently - system may slow down" repeats the CRITICAL status.
  List the actual top candidates instead.
- **Add a privacy note.** The prompt includes the username and full paths. Fine for the owner, but a short
  line, or an option to redact them, would help anyone sharing it.
- **Match the questions to the sections.** The six-question tail predates libraries, caches and snapshots
  (the `BACKLOG.md` item "Optimize the LLM prompt for the storage scan" covers this).
