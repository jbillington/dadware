# Lightweight TUI Plan

**Supersedes:** TUI-DESIGN-DOCUMENT.md, TUI-ARCHITECTURE.md, TUI-PROTOTYPING-GUIDE.md
**Status:** Proposed
**Effort:** 4-8 hours

---

## Why Not the Previous TUI Plan

The earlier docs spec a Textual-based app with state machines, worker threads, settings panels, activity tracking, and config files. That's a rewrite of the tool into a different product. Dad Ware is a scanner that runs, shows you a report, and gets out of the way. The TUI should match that simplicity.

## Principles

1. **No new dependencies.** Use only Python stdlib (curses). No Textual, no Rich. Dad Ware's zero-dependency runtime is a feature — the TUI shouldn't break it.
2. **Replace the menu script, not the CLI.** The `yourdad` menu launcher becomes the TUI. The `yourdad.py` CLI stays unchanged for scripting and automation.
3. **Same flow, better presentation.** Pick a scan → watch progress → see results. That's it.
4. **Falls back gracefully.** If curses isn't available or terminal is too small, fall back to the current menu behavior.

## What It Does

Three screens, no more:

### Screen 1: Menu

```
────────────────────────────────────
  Dad Ware  |  yourdad v0.1-poc
────────────────────────────────────

  [1]  Storage scan
  [2]  CPU / Memory scan
  [3]  Both

  [q]  Quit

────────────────────────────────────
```

Single keypress to select. No Enter required. That's the whole menu.

### Screen 2: Scan Progress

```
────────────────────────────────────
  Scanning storage...
────────────────────────────────────

  Volume: /
  Found: 14,832 items
  Elapsed: 12s

  ████████████░░░░░░░░  58%

  → scanning home directory...

────────────────────────────────────
  [Ctrl+C] Cancel
```

Reuses the existing `progress_callback` parameter that `scan_storage` already supports. The progress bar is just the callback output formatted into a curses window instead of `\r` prints.

### Screen 3: Summary

```
────────────────────────────────────
  Storage Report Card
────────────────────────────────────

  Overall Grade:  B

  Free Space:     A   (32% free)
  Downloads:      C   (8.2 GB)
  Desktop:        A   (340 MB)

  💬 "downloads is getting crowded.
      regular cleanup day?"

────────────────────────────────────
  [o] Open full report in browser
  [m] Back to menu
  [q] Quit
────────────────────────────────────
```

Shows the grades and dad comment inline. The full HTML report is one keypress away. No attempt to replicate the HTML report in the terminal — that's what the browser is for.

## What It Doesn't Do

- **No in-TUI report browsing.** The HTML report is better for that. The TUI shows the summary and lets you open it.
- **No settings panel.** There are 3 scans and a few flags. That's not enough to need a settings UI.
- **No report history.** Run a scan, see the result. If you want old reports, they're in `~/.dadware/reports/`.
- **No worker threads.** Scans are fast enough. The curses screen redraws on the progress callback. If a scan hangs, Ctrl+C works.
- **No mouse support.** Three numbered options don't need a mouse.

## Implementation

### File Structure

```
tui/
├── __init__.py
├── app.py          # Main loop: menu → scan → summary → repeat
├── screens.py      # draw_menu(), draw_progress(), draw_summary()
└── keys.py         # Keypress handling
yourdad             # Updated to launch tui.app instead of the old menu
```

~300-500 lines total. One person, one sitting.

### Integration

The TUI imports scanners directly (same as `yourdad.py` does):

```python
from scanners.storage import scan_storage
from scanners.cpu import scan_cpu
from personality.yourdad import add_personality
from scanners.grading import grade_free_space, grade_home_folders_clutter
from renderers.html import render_html
```

No subprocess calls. No IPC. No orchestration layer.

### Progress Callback

`scan_storage` already accepts a `progress_callback(items_found, elapsed_time)`. The TUI passes its own callback that redraws the progress screen:

```python
def on_progress(items_found, elapsed_time):
    draw_progress(stdscr, items_found, elapsed_time)
    stdscr.refresh()

scan_data = scan_storage(volume_path, progress_callback=on_progress)
```

### Opening the HTML Report

After rendering, use `webbrowser.open()` — same as the CLI does today. The TUI stays on the summary screen so the user can come back to it.

### Curses Basics

```python
import curses

def main(stdscr):
    curses.curs_set(0)          # hide cursor
    stdscr.clear()
    # draw menu, handle keys, loop

curses.wrapper(main)            # handles init/cleanup
```

`curses.wrapper` handles terminal setup and teardown, including restoring the terminal on crash. It's in stdlib on macOS.

## Build Order

1. **Menu screen with keypress input** — get the curses boilerplate working
2. **Wire up storage scan with progress** — prove the callback integration works
3. **Summary screen with grades** — pull from scan_data and personality_data
4. **CPU scan** — same pattern, different data
5. **"Both" option** — run storage then CPU, show two summaries
6. **Polish** — colors, alignment, edge cases (small terminals, missing curses)

## Testing

- `test_tui.py` tests the pure functions: screen content generation (given scan data, what strings are drawn), key handling logic.
- Don't try to test curses rendering itself — test the data transforms that feed into it.
- Manual testing in Terminal.app and iTerm2.
