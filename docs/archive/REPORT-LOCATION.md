# Report Location Configuration

## Overview

Reports can be saved to two different locations depending on your use case:

1. **Production Mode (Default):** `~/.dadware/reports` - Hidden folder in home directory
2. **Development Mode:** `test-reports/` - Visible folder in project root

---

## Where Results Are Saved

When you run a scan, **two files** are created:

1. **HTML Report**: `{scan_type}_{timestamp}.html` - The visual report you see in the browser
2. **JSON Manifest**: `{scan_type}_{timestamp}.json` - Contains all the raw scan data

### Location

**Production Mode (default):**
- `~/.dadware/reports/`
- Example: `/Users/john/.dadware/reports/storage_2025-11-09_14-23.html`
- Example: `/Users/john/.dadware/reports/storage_2025-11-09_14-23.json`

**Development Mode (auto-detected in git repos):**
- `test-reports/` (in project folder)
- Example: `/path/to/dadware/test-reports/storage_2025-11-09_14-23.html`
- Example: `/path/to/dadware/test-reports/storage_2025-11-09_14-23.json`

---

## How It Works

### Automatic Detection

The script automatically detects if you're in development mode by checking if you're running from a git repository. If you are, reports will automatically go to `test-reports/` in your project folder.

### Manual Override

You can explicitly control where reports are saved using the `--test-reports` flag:

```bash
# Force test-reports directory (even outside git repo)
python yourdad.py scan storage --test-reports

# Force production directory (even in git repo)
python yourdad.py scan storage  # (without --test-reports, uses default)
```

---

## Usage Examples

### Development/UX Iteration

When working on UX improvements, reports will automatically go to `test-reports/`:

```bash
# In a git repository - automatically uses test-reports/
python yourdad.py scan storage

# Output will show:
# 📁 Using test-reports directory: /path/to/dadware/test-reports
# 📊 Full report: file:///path/to/dadware/test-reports/storage_2025-11-09_14-23.html
```

### Production Use

For end users or when you want reports in the standard location:

```bash
# Reports go to ~/.dadware/reports
python yourdad.py scan storage
```

---

## JSON Manifest Structure

The JSON file contains all the scan data in a structured format:

```json
{
  "report_id": "storage_2025-11-09_14-23",
  "generated_at": "2025-11-09T14:23:42.123456",
  "scan_results": {
    "storage": {
      "scan_type": "storage",
      "volume": "/Users/john",
      "volume_info": {
        "total_bytes": 536870912000,
        "used_bytes": 415560596480,
        "free_bytes": 121310315520,
        "total_human": "500.0 GB",
        "used_human": "387.4 GB",
        "free_human": "113.0 GB",
        "used_percent": 77,
        "free_percent": 23
      },
      "top_folders": [...],
      "top_files": [...]
    }
  },
  "personality_comments": [...],
  "report_files": {
    "html": "/Users/john/.dadware/reports/storage_2025-11-09_14-23.html"
  }
}
```

---

## Accessing Reports

### From Terminal

```bash
# List all reports (production)
ls ~/.dadware/reports/*.json

# List all reports (development)
ls test-reports/*.json

# View a specific JSON file
cat ~/.dadware/reports/storage_2025-11-09_14-23.json | python -m json.tool

# Or open in your editor
open ~/.dadware/reports/storage_2025-11-09_14-23.json
```

### From Finder

1. **Production reports**: Press `Cmd+Shift+G` in Finder, type `~/.dadware/reports`
2. **Test reports**: Navigate to your project folder → `test-reports/`

---

## Use Cases

The JSON manifest is useful for:
- **Programmatic access**: Parse scan results in other scripts
- **Data analysis**: Extract statistics or trends
- **Debugging**: See exactly what data was collected
- **Integration**: Use in other tools or workflows

### Example: Reading JSON in Python

```python
import json

# Load the manifest
with open('test-reports/storage_2025-11-09_14-23.json', 'r') as f:
    manifest = json.load(f)

# Access scan data
scan_data = manifest['scan_results']['storage']
top_folders = scan_data['top_folders']
top_files = scan_data['top_files']
volume_info = scan_data['volume_info']

print(f"Scanned: {scan_data['volume']}")
print(f"Free space: {volume_info['free_human']}")
print(f"Top folder: {top_folders[0]['path']} ({top_folders[0]['size_human']})")
```

---

## Benefits

- **Easy Access:** Test reports are right in your project folder, easy to find and reference
- **No Breaking Changes:** Production behavior unchanged (reports still go to `~/.dadware/reports` by default)
- **Automatic:** No need to remember flags during development
- **Flexible:** Can override with `--test-reports` flag when needed

---

## File Structure

```
dadware/
├── test-reports/          # Development reports (gitignored)
│   ├── storage_2025-11-09_14-23.html
│   └── storage_2025-11-09_14-23.json
├── yourdad.py
└── ...
```

---

## Notes

- The `test-reports/` folder is automatically added to `.gitignore`
- Reports in `test-reports/` are visible in Finder and your IDE
- You can easily delete test reports when done iterating
- Production reports remain in `~/.dadware/reports` for end users

---

**Last Updated:** November 28, 2025



