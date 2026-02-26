# CI/CD Setup - Dad Ware

**Status:** ✅ Complete  
**Date:** December 13, 2025

---

## What Was Set Up

### 1. Git Configuration

**Updated `.gitignore`:**
- ✅ `docs/` folder now gets committed to git
- ✅ `docs/roadmap/` excluded (contains planning docs)
- ✅ `docs/sessions/` excluded (contains session summaries)
- ✅ Build artifacts excluded (`build/`, `dist/`)

**Result:**
- Documentation in `docs/bugs/`, `docs/archive/`, `docs/TESTING-PLAN.md`, `docs/WORKFLOW.md` will be committed
- Planning docs in `docs/roadmap/` stay local
- Session summaries in `docs/sessions/` stay local

---

### 2. GitHub Actions Workflow

**File:** `.github/workflows/test-and-build.yml`

**What It Does:**
1. **Test Job:**
   - Runs on every push/PR
   - Sets up Python 3.9
   - Installs test dependencies
   - Runs pytest tests (if `tests/` directory exists)
   - Tests basic CLI commands (`--version`, `--help`)
   - Checks code quality

2. **Build Job:**
   - Runs after tests pass
   - Installs PyInstaller
   - Builds executable using `build_executable.sh`
   - Tests executable works
   - Uploads executable as artifact
   - Creates release asset on tags

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual trigger (workflow_dispatch)

---

### 3. Testing Infrastructure

**Files Created:**
- `requirements-dev.txt` - Development dependencies (pytest, etc.)
- `pytest.ini` - pytest configuration
- `tests/__init__.py` - Test package
- `tests/test_cli.py` - Basic CLI smoke tests
- `docs/TESTING-PLAN.md` - Comprehensive testing plan

**Test Structure:**
```
tests/
├── __init__.py
├── test_cli.py          # CLI smoke tests (✅ created)
├── test_scanners.py     # Scanner tests (planned)
├── test_reports.py      # Report tests (planned)
└── [more tests to be added]
```

---

## How to Use

### Run Tests Locally

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Test GitHub Actions

1. **Push to GitHub:**
   ```bash
   git add .github/
   git commit -m "Add CI/CD workflow"
   git push
   ```

2. **Check Actions Tab:**
   - Go to GitHub repository
   - Click "Actions" tab
   - See workflow running
   - Download executable artifact when build completes

### Manual Workflow Trigger

1. Go to GitHub repository
2. Click "Actions" tab
3. Select "Test and Build" workflow
4. Click "Run workflow"
5. Select branch and click "Run workflow"

---

## What Gets Tested

### Currently (Phase 1)
- ✅ CLI commands don't crash (`--version`, `--help`)
- ✅ Basic command structure works
- ✅ Executable builds successfully
- ✅ Executable runs basic commands

### Planned (Future Phases)
- Unit tests for formatters and utilities
- Integration tests for scanners
- Report generation tests
- Full end-to-end tests

---

## Build Artifacts

### On Every Build
- Executable uploaded as artifact: `yourdad-executable-macos`
- Available for 30 days
- Download from Actions tab

### On Release Tags
- Release zip created: `yourdad-macos.zip`
- Includes executable, README, BUILD-EXECUTABLE.md
- Uploaded as release asset

---

## Next Steps

1. **Push to GitHub** - Test the workflow
2. **Add More Tests** - Implement Phase 1 tests (2-4 hours)
3. **Monitor Workflows** - Ensure builds succeed
4. **Expand Tests** - Add unit and integration tests

---

## Troubleshooting

### Tests Fail Locally
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run with verbose output
pytest -v
```

### GitHub Actions Fails
- Check Actions tab for error messages
- Verify Python version (3.9)
- Check that all dependencies are in `requirements-dev.txt`

### Executable Build Fails
- Check PyInstaller is installed in workflow
- Verify `yourdad.spec` is correct
- Check for missing hidden imports

---

**Status:** ✅ Setup complete, ready to test on GitHub

