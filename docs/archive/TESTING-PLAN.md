# Testing Plan - Dad Ware

**Purpose:** Automated testing strategy to validate functionality after updates

---

## Testing Strategy

### Test Levels

1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test scanner integration
3. **CLI Tests** - Test command-line interface
4. **Report Tests** - Test report generation
5. **Executable Tests** - Test built executable

---

## Test Categories

### 1. Unit Tests

**What to Test:**
- Formatting functions (`format_size`, `parse_size`)
- Path utilities (`should_exclude`, `is_docker_path`)
- Volume detection (`list_volumes`, `select_volume`)
- Memory pressure calculation
- File size calculation (logical vs. actual)

**Files to Test:**
- `utils/formatters.py` (when created)
- `utils/path_utils.py` (when created)
- `utils/volumes.py`
- `scanners/cpu.py` - `get_memory_pressure()`
- `scanners/storage.py` - `is_docker_path()`, `is_sparse_file()`

**Test Framework:** pytest

---

### 2. Integration Tests

**What to Test:**
- Storage scanner end-to-end
- CPU scanner end-to-end
- Mac libraries scanner
- Report generation (JSON + HTML)
- Personality injection

**Test Scenarios:**
- Scan small test directory
- Scan with exclusions
- Scan with Docker paths (should skip)
- Scan with sparse files (should use actual size)
- Generate report and verify structure

**Test Framework:** pytest with fixtures

---

### 3. CLI Tests

**What to Test:**
- All scan commands work
- Volume selection (single vs. multiple)
- Export commands
- Error handling
- Help text

**Test Commands:**
```bash
yourdad.py scan cpu
yourdad.py scan storage
yourdad.py scan all
yourdad.py export memory <file>
yourdad.py --version
yourdad.py --help
```

**Test Framework:** pytest with subprocess

---

### 4. Report Tests

**What to Test:**
- JSON report structure
- HTML report generation
- Report file naming
- Report directory creation
- Browser opening (optional)

**Test Scenarios:**
- Generate report and verify JSON structure
- Verify HTML contains expected elements
- Verify report files are created in correct location
- Verify report naming includes timestamp

**Test Framework:** pytest with file checks

---

### 5. Executable Tests

**What to Test:**
- Executable builds successfully
- Executable runs without Python
- Executable produces same output as script
- Executable handles errors correctly

**Test Scenarios:**
- Build executable
- Run executable with test commands
- Compare output to script output
- Test on clean system (if possible)

**Test Framework:** GitHub Actions + pytest

---

## Test Implementation Plan

### Phase 1: Basic Tests (Quick - 2-4 hours)

**Priority:** High - Catch regressions early

1. **CLI Smoke Tests**
   - Test all commands run without crashing
   - Test help and version commands
   - Test error handling

2. **Report Generation Tests**
   - Test JSON report is created
   - Test HTML report is created
   - Test report structure is valid

3. **Basic Scanner Tests**
   - Test storage scanner on small directory
   - Test CPU scanner runs
   - Test scanners return expected data structure

**Files to Create:**
- `tests/__init__.py`
- `tests/test_cli.py`
- `tests/test_reports.py`
- `tests/test_scanners.py`

---

### Phase 2: Unit Tests (4-6 hours)

**Priority:** Medium - Improve code quality

1. **Formatting Tests**
   - Test `format_size()` with various inputs
   - Test `parse_size()` with various formats
   - Test edge cases (0, negative, very large)

2. **Path Utility Tests**
   - Test `should_exclude()` with various paths
   - Test `is_docker_path()` detection
   - Test `is_sparse_file()` detection

3. **Volume Tests**
   - Test `list_volumes()` returns expected format
   - Test `select_volume()` with single/multiple volumes

**Files to Create:**
- `tests/test_formatters.py`
- `tests/test_path_utils.py`
- `tests/test_volumes.py`

---

### Phase 3: Integration Tests (4-6 hours)

**Priority:** Medium - Test real workflows

1. **End-to-End Scanner Tests**
   - Test full storage scan workflow
   - Test full CPU scan workflow
   - Test scan with real data (mocked or small)

2. **Report Integration Tests**
   - Test scan → report → HTML workflow
   - Test personality injection
   - Test report file structure

**Files to Create:**
- `tests/test_integration.py`
- `tests/fixtures/` - Test data fixtures

---

### Phase 4: Executable Tests (2-4 hours)

**Priority:** High - Ensure distribution works

1. **Build Tests**
   - Test executable builds successfully
   - Test executable size is reasonable
   - Test executable structure

2. **Runtime Tests**
   - Test executable runs commands
   - Test executable produces correct output
   - Test executable error handling

**Files to Create:**
- `tests/test_executable.py`
- GitHub Actions workflow

---

## Test Framework Setup

### Requirements

**File: `requirements-dev.txt`**
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_cli.py              # CLI tests
├── test_scanners.py         # Scanner tests
├── test_reports.py          # Report tests
├── test_formatters.py       # Formatting tests
├── test_path_utils.py       # Path utility tests
├── test_volumes.py          # Volume tests
├── test_integration.py      # Integration tests
├── test_executable.py       # Executable tests
└── fixtures/                # Test data
    ├── test_directory/
    └── sample_reports/
```

### pytest Configuration

**File: `pytest.ini` or `setup.cfg`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    cli: CLI tests
    slow: Slow tests
```

---

## GitHub Actions Workflow

### Build and Test Workflow

**File: `.github/workflows/test-and-build.yml`**

```yaml
name: Test and Build

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python3 -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=. --cov-report=term-missing
      - name: Test CLI
        run: |
          python3 yourdad.py --version
          python3 yourdad.py --help

  build:
    runs-on: macos-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install PyInstaller
        run: |
          python3 -m pip install pyinstaller
      - name: Build executable
        run: |
          chmod +x build_executable.sh
          ./build_executable.sh
      - name: Test executable
        run: |
          ./dist/yourdad --version
          ./dist/yourdad --help
      - name: Upload executable
        uses: actions/upload-artifact@v3
        with:
          name: yourdad-executable
          path: dist/yourdad
```

---

## Quick Test Checklist

### Before Committing

- [ ] Run `pytest tests/` - All tests pass
- [ ] Run `python3 yourdad.py --version` - Works
- [ ] Run `python3 yourdad.py scan cpu` - Works
- [ ] Check for linting errors
- [ ] Verify no regressions

### Before Release

- [ ] All tests pass
- [ ] Executable builds successfully
- [ ] Executable tested on clean system
- [ ] Manual testing on real system
- [ ] Documentation updated

---

## Test Data

### Test Directories

Create small test directories for testing:
- `tests/fixtures/test_directory/` - Small directory tree
- `tests/fixtures/test_directory_large/` - Larger directory (for performance)
- `tests/fixtures/test_directory_docker/` - Directory with Docker paths

### Mock Data

Use mocks for:
- System calls (`ps`, `vm_stat`, etc.)
- File system operations (for unit tests)
- Subprocess calls

---

## Coverage Goals

- **Unit Tests:** 80%+ coverage of utility functions
- **Integration Tests:** All major workflows covered
- **CLI Tests:** All commands tested
- **Report Tests:** Report generation validated

---

## Continuous Integration

### GitHub Actions

1. **On Push/PR:**
   - Run all tests
   - Check code coverage
   - Build executable
   - Test executable

2. **On Release:**
   - Build executable
   - Create release artifacts
   - Upload to releases

---

## Next Steps

1. **Phase 1 (Quick):** Set up pytest, create basic CLI and report tests
2. **Phase 2:** Add unit tests for formatters and utilities
3. **Phase 3:** Add integration tests
4. **Phase 4:** Add executable tests and GitHub Actions

---

**Status:** Planning phase  
**Priority:** High - Should be implemented before major refactoring

