# Report Location Configuration

## Overview

Reports can now be saved to two different locations depending on your use case:

1. **Production Mode (Default):** `~/.dadware/reports` - Hidden folder in home directory
2. **Development Mode:** `test-reports/` - Visible folder in project root

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

## Benefits

- **Easy Access:** Test reports are right in your project folder, easy to find and reference
- **No Breaking Changes:** Production behavior unchanged (reports still go to `~/.dadware/reports` by default)
- **Automatic:** No need to remember flags during development
- **Flexible:** Can override with `--test-reports` flag when needed

## File Structure

```
dadware/
├── test-reports/          # Development reports (gitignored)
│   ├── storage_2025-11-09_14-23.html
│   └── storage_2025-11-09_14-23.json
├── yourdad.py
└── ...
```

## Notes

- The `test-reports/` folder is automatically added to `.gitignore`
- Reports in `test-reports/` are visible in Finder and your IDE
- You can easily delete test reports when done iterating
- Production reports remain in `~/.dadware/reports` for end users

