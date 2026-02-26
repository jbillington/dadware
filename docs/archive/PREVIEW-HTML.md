# How to Preview HTML Reports in Cursor

Cursor doesn't have a built-in HTML preview feature (unlike VS Code's Live Server). Here are several ways to preview your HTML reports:

## Quick Methods

### 1. **Right-Click in Cursor** (Easiest)
- Right-click on the HTML file in the file explorer
- Select **"Reveal in Finder"** (or "Show in Finder")
- Double-click the file to open in your default browser

### 2. **Use the Preview Script** (Recommended)
```bash
# Preview the sample report
python3 preview_report.py

# Or preview a specific report
python3 preview_report.py test-reports/storage_2025-11-09_14-23.html
```

### 3. **Open from Terminal**
```bash
# Open the file directly
open test-reports/sample_report_improved.html

# Or use the file:// URL
open "file://$(pwd)/test-reports/sample_report_improved.html"
```

### 4. **Use Cursor's Command Palette**
1. Press `Cmd+Shift+P` (or `Ctrl+Shift+P`)
2. Type "Open in Browser" (if you have an extension)
3. Or type "Terminal: Run Command" and use `open test-reports/sample_report_improved.html`

## Browser Extensions for Cursor

You can install extensions that add HTML preview:

1. **Live Preview** - Adds a preview pane (similar to VS Code)
   - Install from Cursor's extension marketplace
   - Right-click HTML file → "Show Preview"

2. **Open in Browser** - Adds "Open in Browser" command
   - Adds a context menu option
   - Works with `file://` URLs

## Using a Local Server (For Development)

If you need a local server (useful for testing file:// links):

```bash
# Python 3
python3 -m http.server 8000

# Then open: http://localhost:8000/test-reports/sample_report_improved.html
```

## Keyboard Shortcut (Custom)

You can add a custom keyboard shortcut in Cursor:

1. Go to **Settings** → **Keyboard Shortcuts**
2. Search for "Open in Browser" or create a custom command
3. Assign a shortcut like `Cmd+Shift+B`

## Recommended Workflow

For iterating on HTML reports:

1. **Edit** the HTML file in Cursor
2. **Save** the file
3. **Run** `python3 preview_report.py` in terminal (or use a shortcut)
4. **Refresh** browser to see changes

Or use a file watcher:
```bash
# Watch for changes and auto-open
fswatch -o test-reports/*.html | xargs -n1 -I{} python3 preview_report.py
```

## Why Cursor Can't Preview HTML Directly

- Cursor is based on VS Code but doesn't include all features
- HTML preview requires a rendering engine (browser)
- Security: `file://` URLs have limitations
- Best practice: Use actual browser for accurate preview

## Pro Tip

Add this to your shell config (`.zshrc` or `.bashrc`):
```bash
alias preview-html='python3 /path/to/dadware/preview_report.py'
```

Then just run `preview-html` from anywhere!

