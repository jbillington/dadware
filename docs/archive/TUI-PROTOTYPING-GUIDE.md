# TUI Prototyping Guide - Dad Ware

**Practical workflow for building the Dad Ware TUI**

This guide provides a streamlined workflow from mockups to working TUI, using tools that avoid alignment issues and enable rapid iteration.

---

## Quick Workflow Overview

1. **ASCII Mockups** (30 min) → ASCIIFlow online tool
2. **Simple Prototype** (1-2 hours) → Python + Cursor
3. **Textual Setup** (15 min) → Install and configure
4. **Textual Prototype** (2-4 hours) → Dev mode with hot reload
5. **Terminal Testing** (30 min) → Verify across terminals
6. **Integration** (2-4 hours) → Connect to existing scanners

**Total Time:** ~6-12 hours over 2-3 days

---

## Phase 1: ASCII Mockups (30 minutes)

### Use ASCIIFlow (Not Manual ASCII)

**Why ASCIIFlow:**
- Online tool: https://asciiflow.com/
- Uses pure ASCII (`+`, `-`, `|`) - no Unicode alignment issues
- Easy to share and iterate
- Exports clean text

**Steps:**
1. Open ASCIIFlow in browser
2. Create mockups for:
   - Main menu screen
   - Scan progress screen
   - Report view screen
   - Help modal
3. Export each as plain text
4. Save to `docs/roadmap/tui-mockups/`:
   ```bash
   mkdir -p docs/roadmap/tui-mockups
   # Save: menu.txt, scan_progress.txt, report_view.txt, help_modal.txt
   ```

**Test immediately:**
```bash
cat docs/roadmap/tui-mockups/menu.txt
# Verify alignment looks correct in terminal
```

**Key:** Use ASCIIFlow's pure ASCII characters - they align correctly in any monospace font.

---

## Phase 2: Simple Interactive Prototype (1-2 hours)

### Build in Cursor

**Steps:**
1. Create `tui_prototype_simple.py` in project root
2. Ask Cursor: "Create a simple TUI prototype with a menu that matches the ASCII mockup in `docs/roadmap/tui-mockups/menu.txt`"
3. Use pure ASCII borders (`+`, `-`, `|`) - no Unicode
4. Test in terminal:
   ```bash
   python3 tui_prototype_simple.py
   ```

**Cursor Prompts:**
- "Add a progress bar simulation"
- "Add keyboard navigation with arrow keys"
- "Match the layout from the ASCII mockup"

**Test immediately after each change** - verify in terminal, not just editor.

---

## Phase 3: Install Textual (15 minutes)

```bash
pip install textual
python3 -c "import textual; print('Textual installed')"
```

**Create project structure:**
```bash
mkdir -p tui/{screens,widgets,utils}
touch tui/__init__.py tui/app.py
touch tui/screens/__init__.py tui/widgets/__init__.py
```

---

## Phase 4: Textual Prototype with Dev Mode (2-4 hours)

### Build in Cursor with Textual

**Steps:**
1. Create `tui/app.py` with basic Textual structure
2. Ask Cursor: "Create a Textual TUI app with a menu screen that matches `docs/roadmap/tui-mockups/menu.txt`"
3. Run in dev mode (hot reload):
   ```bash
   textual run tui/app.py --dev
   ```

**Dev Mode Benefits:**
- Hot reload on file changes
- Layout debugging
- Real-time terminal preview

**Workflow:**
1. Edit code in Cursor
2. Save file
3. See changes instantly (dev mode auto-reloads)
4. Test interactively
5. Iterate quickly

**Cursor Prompts:**
- "Add a scan progress screen that matches `docs/roadmap/tui-mockups/scan_progress.txt`"
- "Add keyboard navigation to the menu"
- "Style the menu to match the design document colors"

---

## Phase 5: Test Terminal Rendering (30 minutes)

**Test in multiple terminals:**
```bash
# Test in Terminal.app
textual run tui/app.py

# Test in iTerm2 (if installed)
# Open iTerm2 and run the same command

# Test with different font sizes
# Change terminal font size, run again
```

**Test color support:**
```bash
# Quick color test
python3 -c "from rich.console import Console; Console().print('[bold red]Red[/bold red] [bold green]Green[/bold green]')"
```

**Verify:**
- Borders align correctly
- Text doesn't overflow
- Spacing is consistent
- Colors render properly

---

## Phase 6: Integrate with Existing Code (2-4 hours)

**Connect to existing scanners:**
1. Ask Cursor: "Integrate the TUI with the storage scanner from `scanners/storage.py`"
2. Show real progress during scans
3. Display actual report data

**Example integration:**
```python
# In tui/screens/scan_screen.py
from scanners.storage import scan_storage

async def run_scan(self):
    # Call existing scan function
    # Show real progress
    # Display results
```

**Test integration:**
```bash
textual run tui/app.py --dev
# Start a scan, verify it works with real data
```

---

## Quick Reference: Commands

```bash
# Phase 1: Create mockups
# Use ASCIIFlow online, save to docs/roadmap/tui-mockups/

# Phase 2: Simple prototype
python3 tui_prototype_simple.py

# Phase 3: Install Textual
pip install textual

# Phase 4: Run in dev mode (hot reload)
textual run tui/app.py --dev

# Phase 5: Test in terminal
textual run tui/app.py

# Phase 6: Test integration
textual run tui/app.py --dev
```

---

## Recommended Timeline

**Day 1 (2-3 hours):**
- Create ASCII mockups in ASCIIFlow (30 min)
- Test mockups in terminal (10 min)
- Build simple Python prototype in Cursor (1-2 hours)
- Test simple prototype (30 min)

**Day 2 (4-6 hours):**
- Install Textual (15 min)
- Build Textual prototype in Cursor (2-3 hours)
- Run in dev mode, iterate quickly (1-2 hours)
- Test in multiple terminals (30 min)

**Day 3 (4-6 hours):**
- Integrate with existing scanners (2-3 hours)
- Add polish and features (2-3 hours)
- Final testing and refinement (1 hour)

---

## Key Tips

1. **Use ASCIIFlow** - Avoids Unicode alignment issues
2. **Test in terminal immediately** - Don't wait until the end
3. **Use Textual dev mode** - Rapid iteration with hot reload
4. **Use Cursor AI** - Generate code quickly, iterate fast
5. **Test across terminals early** - Catch rendering issues early
6. **Integrate with real data ASAP** - Don't wait until everything is perfect

---

## Troubleshooting

**Alignment issues:**
- Use ASCIIFlow (pure ASCII, no Unicode)
- Test in terminal immediately
- Use monospace fonts (SF Mono, Menlo, Courier)

**Textual not working:**
```bash
# Verify installation
python3 -c "import textual; print(textual.__version__)"

# Check Python version (needs 3.9+)
python3 --version
```

**Dev mode not reloading:**
- Make sure you're using `--dev` flag
- Check file is being saved
- Restart dev mode if needed

---

## Cursor Workflow Tips

**Start with AI assistance:**
- Ask Cursor to create initial prototype
- Use Cursor's suggestions to iterate quickly

**Iterate in small steps:**
- Make one change at a time
- Test immediately
- Use Cursor to explain what changed

**Use Cursor's codebase understanding:**
- "How does the existing menu work?"
- "Integrate the scan functions from scanners/"
- "Use the same formatting as renderers/terminal.py"

**Debug with Cursor:**
- Paste error messages
- Ask "Why is this failing?"
- Get suggested fixes

---

**Ready to start?** Begin with Phase 1 (ASCIIFlow mockups) and work through each phase systematically.
