# Code Refactor Plan

**Goal:** Improve architecture and DRY without changing external behavior of `yourdad scan`.

## File → Purpose Table

| File | Purpose |
|------|---------|
| `yourdad.py` | CLI entry point; orchestrates scans, report generation, and file I/O |
| `scanners/storage.py` | Storage scanning: finds large files/folders, calculates sizes, scans volumes |
| `scanners/cpu.py` | CPU/RAM scanning: process monitoring, memory pressure detection |
| `scanners/mac_libraries.py` | Mac app library scanning: Photos, Music, Messages, Mail, Time Machine, Creative apps |
| `scanners/grading.py` | Report card grading: converts metrics to letter grades (A-F) |
| `renderers/html.py` | HTML report generation: creates interactive web reports |
| `renderers/terminal.py` | Terminal report generation: creates ANSI-colored CLI output |
| `personality/yourdad.py` | Personality engine: generates dad-style comments and tips from scan data |
| `utils/volumes.py` | Volume utilities: detects/selects mounted volumes, gets volume info |
| `utils/permissions.py` | Permission checking: tests Full Disk Access for protected directories |
| `utils/system_info.py` | System info collector: gathers Mac model, CPU, RAM, OS version |
| `utils/llm_prompt.py` | LLM prompt generator: formats scan data for AI consultation |
| `generate_sample_report.py` | Dev utility: generates sample reports from JSON for testing |
| `preview_report.py` | Dev utility: opens HTML reports in browser |

## Identified Duplication

1. **`format_size()`** - duplicated in 6 files:
   - `scanners/storage.py`
   - `scanners/mac_libraries.py`
   - `scanners/grading.py`
   - `utils/volumes.py`
   - `renderers/html.py`
   - `renderers/terminal.py`

2. **`get_folder_size()`** - duplicated in 2 files with different logic:
   - `scanners/storage.py` (uses `should_exclude()`)
   - `scanners/mac_libraries.py` (uses `should_skip_path()`)

3. **`get_status_emoji()` and `get_status_text()`** - duplicated in:
   - `renderers/html.py`
   - `renderers/terminal.py`

4. **Path filtering logic** - similar but separate:
   - `should_exclude()` in `scanners/storage.py`
   - `should_skip_path()` in `scanners/mac_libraries.py`

## Main Coupling Points

- **CLI → Scanners → Renderers → Personality** (linear flow)
- Renderers depend on `scanners.grading` for grade calculations
- Scanners depend on `utils` modules (volumes, permissions)
- Personality depends on scan_data structure
- LLM prompt depends on system_info and personality

## Refactor Checklist

### 1. Create `utils/formatters.py` - Consolidate formatting functions
- [ ] Move `format_size()` from 6 locations to single shared module
- [ ] Move `parse_size()` from storage.py
- [ ] Move `get_status_emoji()` and `get_status_text()` from both renderers
- [ ] Update all imports to use shared module

### 2. Create `utils/path_utils.py` - Consolidate path/folder utilities
- [ ] Merge `get_folder_size()` from storage.py and mac_libraries.py into unified function
- [ ] Merge `should_exclude()` and `should_skip_path()` into unified path filtering
- [ ] Add configurable skip patterns and exclusion rules
- [ ] Return consistent (size, count) tuple

### 3. Standardize scanner return structures
- [ ] Define common result schema (status, size_bytes, size_human, count, etc.)
- [ ] Ensure all scanners return compatible dicts
- [ ] Add `scan_type` field consistently

### 4. Extract report generation orchestration from `yourdad.py`
- [ ] Create `core/report_builder.py` to handle:
  - Scan execution flow
  - Personality injection
  - Report file I/O (JSON manifest, HTML generation)
  - Browser opening logic
- [ ] Reduce `yourdad.py` to CLI parsing and delegation

### 5. Create `core/scan_result.py` - Data model
- [ ] Define ScanResult dataclass/class for type safety
- [ ] Standardize scan_data structure across scanners
- [ ] Add validation helpers

### 6. Consolidate duplicate status/emoji logic
- [ ] Move `get_status_emoji()` and `get_status_text()` to `utils/formatters.py` (from step 1)
- [ ] Update renderers to import from shared location

### 7. Extract common report metadata logic
- [ ] Move `get_reports_dir()` and `is_development_mode()` from `yourdad.py` to `core/report_builder.py` or `utils/paths.py`
- [ ] Centralize timestamp formatting and report naming

### 8. Add `utils/__init__.py` exports for cleaner imports
- [ ] Export common functions: `from utils import format_size, parse_size`
- [ ] Update all files to use centralized imports

## Expected Impact

- **Reduces code duplication** by ~200-300 lines
- **Improves maintainability** (single source of truth for formatters)
- **Makes testing easier** (shared utilities can be tested once)
- **No external behavior changes** (pure refactor)

## Notes

- All changes should maintain backward compatibility
- Test after each step to ensure `yourdad scan` still works identically
- Consider adding type hints during refactor for better IDE support

