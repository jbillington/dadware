# Progressive Disclosure Progress Reporting

**Status:** Ready to implement
**Priority:** Next up (after Phase 2 refactor — DONE)
**Estimated effort:** 4-6 hours

## Problem
The storage scan on a 250GB drive can take several minutes during the `os.walk` phase. Currently the only feedback is a monotone "found X items... (Ys elapsed)" counter that overwrites itself. Users think the scan is stuck.

## Solution
Show useful results as they emerge during the scan, themed in the dad voice. Progressive disclosure turns a boring wait into an engaging experience.

## Files to Modify
- `scanners/storage.py` — expand progress callback data, detect notable events
- `yourdad.py` — rewrite `report_scan_progress` to show progressive results
- `personality/yourdad.py` — add scan-progress dad quips

## Design

### 1. Expand the progress callback signature

Change `progress_callback(items_found, elapsed_time)` to pass a rich context dict:

```python
progress_callback({
    'items_found': int,
    'elapsed': float,
    'bytes_scanned': int,          # running total in bytes
    'current_dir': str,            # directory currently being walked
    'folder_sizes': dict,          # live folder_sizes accumulator
    'large_files': list,           # files >1GB found this tick
})
```

### 2. Running counter (always visible, overwrites via \r)

```
→ 14.2 GB scanned | 12,345 items | 47s | scanning: Documents/Projects
```
- GB scanned (NEVER MB or bytes — round to 1 decimal)
- Item count
- Elapsed seconds
- Current directory name (truncated to last 2 path components)

### 3. Event callouts (print with \n, shown once each)

```
  📂 Downloads: 14.7 GB — "that's a lot of 'I'll sort this later.'"
  📂 Desktop: 2.1 GB — "your desk has a desk on it."
  📁 Found 4.2 GB file: big-project-backup.zip — "that's not a file, that's a commitment."
  🐳 Docker: 22.4 GB — "docker's eating like a teenager."
```

Triggered when:
- A **known home folder** (Downloads, Desktop, Documents, Movies, Music, Pictures, Library) completes scanning (>100MB to be worth reporting)
- A **file >1GB** is discovered
- **Docker data** >1GB is detected
- **node_modules** >1GB is detected

### 4. Dad quips for progress events

#### Home Folders

| Folder | Condition | Dad says |
|---|---|---|
| Downloads | >10GB | "that's a lot of 'I'll sort this later.'" |
| Downloads | >5GB | "somebody's been busy downloading." |
| Downloads | <5GB | "not bad. you actually clean up." |
| Desktop | >5GB | "your desk has a desk on it." |
| Desktop | >2GB | "desktops are for working, not hoarding." |
| Desktop | <2GB | "nice and tidy." |
| Documents | >20GB | "the filing cabinet is full." |
| Documents | default | "noted." |
| Movies | >50GB | "that's a whole blockbuster shelf." |
| Music | >20GB | "quite the record collection." |
| Pictures | >10GB | "a lot of memories in there." |
| Library | >10GB | "system's got some baggage." |

#### Space Hogs

| Event | Dad says |
|---|---|
| Docker >10GB | "docker's eating like a teenager." |
| Docker >5GB | "docker's got an appetite." |
| node_modules >2GB | "node_modules. the black hole of disk space." |
| File >5GB | "that's not a file, that's a commitment." |
| File >1GB | "big fella right there." |

### 5. Folder detection during os.walk

Track which home folders we've seen. When `os.walk` moves to a new top-level folder (depth-1 component of `rel_path` changes), the previous folder is "done enough" to report:

```python
current_top_folder = None
for root, dirs, files in os.walk(path):
    rel_path = os.path.relpath(root, path)
    parts = rel_path.split(os.sep)
    top_folder = parts[0] if rel_path != '.' else None

    if top_folder != current_top_folder and current_top_folder is not None:
        # Previous folder is complete — include in callback
        ...
    current_top_folder = top_folder
```

### 6. Progress during "scanning folder contents" phase

After the walk, when scanning top 50 folders:
```
→ detailing folder 3/50: Downloads...
```

## Implementation Rules

1. Show GB scanned (never MB or bytes) as running counter
2. Show items found + elapsed time + current directory
3. Report home folders with size + dad quip as each completes
4. Report large files (>1GB) with dad quip as discovered
5. Report Docker/node_modules with dad quip when detected
6. Show "detailing folder N/50" during contents phase
7. All output themed in dad voice — lowercase, wry, domestic analogies
8. Don't repeat folder reports (each folder reported once)

## Verification
1. Run `python yourdad.py scan storage` on the main volume
2. Verify home folders report progressively during scan
3. Verify GB counter updates smoothly
4. Verify large files are called out
5. Verify final report still generates correctly
6. Verify `scan cpu` still works (no regression)
