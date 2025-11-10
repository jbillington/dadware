# Scan Results Location

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
      "top_folders": [
        {
          "path": "Library",
          "path_display": "Library",
          "size_bytes": 31625365920,
          "size_human": "29.4 GB"
        },
        ...
      ],
      "top_files": [
        {
          "path": "/Users/john/Downloads/bigfile.zip",
          "size_bytes": 9021562880,
          "size_human": "8.4 GB"
        },
        ...
      ]
    }
  },
  "personality_comments": [
    "downloads looks like a garage shelf. time to label a box."
  ],
  "report_files": {
    "html": "/Users/john/.dadware/reports/storage_2025-11-09_14-23.html"
  }
}
```

## What's in the JSON

- **report_id**: Unique identifier for this report
- **generated_at**: ISO timestamp when report was created
- **scan_results**: Complete scan data including:
  - Volume information (total, used, free space)
  - Top folders (with sizes)
  - Top files (with sizes and paths)
- **personality_comments**: Dad's commentary on the scan
- **report_files**: Paths to generated files

## Accessing the JSON

### From Terminal

```bash
# List all reports
ls ~/.dadware/reports/*.json

# Or in development mode
ls test-reports/*.json

# View a specific JSON file
cat ~/.dadware/reports/storage_2025-11-09_14-23.json | python -m json.tool

# Or open in your editor
open ~/.dadware/reports/storage_2025-11-09_14-23.json
```

### From Finder

1. **Production reports**: Press `Cmd+Shift+G` in Finder, type `~/.dadware/reports`
2. **Test reports**: Navigate to your project folder → `test-reports/`

## Use Cases

The JSON manifest is useful for:
- **Programmatic access**: Parse scan results in other scripts
- **Data analysis**: Extract statistics or trends
- **Debugging**: See exactly what data was collected
- **Integration**: Use in other tools or workflows

## Example: Reading JSON in Python

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

