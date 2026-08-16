# Rename: `yourdad` → `askdad`

**Status:** Proposed — scheduled as Roadmap Milestone 2, and **must land before the first signed build**: macOS keys permission grants to bundle ID + code signature, so the identity (`com.dadware.askdad`) has to be final before any user grants Full Disk Access to a signed Dad Ware (see `PERMISSIONS-PLAN.md`).

Plan for renaming the program from `yourdad` to `askdad`, aligning the codebase with the user-facing "Ask Dad for Mac" brand. Not yet executed.

## Decisions (locked)

| Question | Decision |
|---|---|
| `~/.dadware/` state dir | Rename to `~/.askdad/`. Clean POC break. No migration shim. |
| `personality/yourdad.py` module | Rename to `personality/askdad.py` for consistency. |
| Banner wording (`yourdad.py:176`) | `Ask Dad for Mac v{VERSION}` (matches README and CONTEXT.md). |
| Historical docs (`docs/bugs/`, `docs/roadmap/`) | **Leave as-is.** They describe past state and `yourdad` references are accurate to when written. |
| GitHub repo name (`dadware`) | **Leave as-is.** Out of scope for this rename. |

## Naming map

| Today | After |
|---|---|
| `yourdad.py` | `askdad.py` |
| `yourdad` (launcher) | `askdad` |
| `yourdad.spec` | `askdad.spec` |
| `dist/yourdad` | `dist/askdad` |
| `personality/yourdad.py` | `personality/askdad.py` |
| `Formula/yourdad.rb` | `Formula/askdad.rb` |
| `~/.dadware/` | `~/.askdad/` |
| `yourdad-VERSION-BUILD.zip` | `askdad-VERSION-BUILD.zip` |
| Banner: `Dad Ware  \|  yourdad v{VERSION}` | `Ask Dad for Mac v{VERSION}` |

## Scope

`grep yourdad` (excluding `docs/bugs/`, `docs/roadmap/`, `test-reports/`, `venv/`, `__pycache__/`) hits these files:

- **Source:** `yourdad.py`, `yourdad` (launcher), `personality/yourdad.py`, `personality/__init__.py`, `scanners/__init__.py`, `renderers/__init__.py`, `renderers/html.py`, `utils/__init__.py`, `utils/subprocess_utils.py`, `utils/permissions.py`
- **Build:** `yourdad.spec`, `build_executable.sh`, `package_for_distribution.sh`, `install.sh`, `Formula/yourdad.rb`
- **Tests:** `tests/test_cli.py`, `tests/test_personality.py`
- **Docs (will update):** `README.md`, `CLAUDE.md`, `CONTEXT.md`, `BACKLOG.md`, `docs/USER-GUIDE.md`, `docs/COMPETITIVE-COMPARISON.md`, `docs/TESTING-AND-LAUNCH.md`, `site/index.html`, `scripts/generate_html_readme.py`
- **CI:** `.github/workflows/test-and-build.yml`

## Phased execution

### Phase 1 — Rename source files (`git mv` to preserve history)

```bash
git mv yourdad.py askdad.py
git mv yourdad askdad
git mv yourdad.spec askdad.spec
git mv personality/yourdad.py personality/askdad.py
git mv Formula/yourdad.rb Formula/askdad.rb
```

Tests will fail after this — that's the checkpoint.

### Phase 2 — Update Python imports and internal references

- `askdad.py`: `from personality.yourdad import add_personality` → `from personality.askdad import add_personality`
- `askdad.spec`:
  - `Analysis(['yourdad.py'], ...)` → `['askdad.py']`
  - `EXE(name='yourdad', ...)` → `name='askdad'`
  - `hiddenimports` entry `'personality.yourdad'` → `'personality.askdad'`
- `utils/subprocess_utils.py:7`: update comment about avoiding circular imports from `yourdad`
- `tests/test_cli.py`: 5 occurrences of `"yourdad.py"` → `"askdad.py"`; if any test asserts banner text, update it
- `tests/test_personality.py`: docstring `"""Tests for personality/yourdad.py"""` → `personality/askdad.py`

Run `pytest` — should be green.

### Phase 3 — Update build/install scripts

- `build_executable.sh`: `yourdad.py` → `askdad.py` (3 spots), `yourdad.spec` → `askdad.spec`, `dist/yourdad` → `dist/askdad`, user-facing echo strings
- `package_for_distribution.sh`: `dist/yourdad` → `dist/askdad`, `yourdad.py` → `askdad.py`, zip naming `yourdad-${VERSION}-${BUILD}.zip` → `askdad-${VERSION}-${BUILD}.zip`
- `install.sh`:
  - `INSTALL_DIR="$HOME/.dadware"` → `"$HOME/.askdad"`
  - `chmod +x "$INSTALL_DIR/yourdad"` → `askdad`
  - symlink `~/.local/bin/yourdad` → `askdad`
  - **fix latent bug:** the script echoes `~/yourdad_reports/` but `yourdad.py` actually writes to `~/.dadware/reports/`. Set both to `~/.askdad/reports/`.
- `Formula/askdad.rb`:
  - Class `Yourdad` → `Askdad`
  - `bin.install "yourdad.py"` → `askdad.py`
  - Wrapper script content (path to interpreter and module)
  - Leave `homepage "https://github.com/jbillington/dadware"` as-is (repo not renamed)

Run `./build_executable.sh` end-to-end — confirm `dist/askdad`.

### Phase 4 — User-facing strings in code

- `askdad.py:176`: banner `"Dad Ware  |  yourdad v{VERSION}"` → `"Ask Dad for Mac v{VERSION}"`
- `askdad.py:35,49`: docstring and code path `~/.dadware/reports` → `~/.askdad/reports`
- `utils/permissions.py:20-21`: paths to `PermissionHelper.app` — update to `.askdad/PermissionHelper.app` and `/Applications/AskDad.app/Contents/Resources/PermissionHelper.app` (the helper app doesn't exist yet, but the path needs to match the new naming for when it does)
- `renderers/html.py:1732`: hint `python3 yourdad.py scan cpu` → `askdad cpu` (also fixes the stale `scan` syntax)
- `scripts/generate_html_readme.py`:
  - line 293: extracted dir name in setup instructions
  - line 302: command example `./yourdad scan storage` → `./askdad`
  - line 356: reports path `~/.dadware/reports/` → `~/.askdad/reports/`

### Phase 5 — Docs (active only; historical left untouched)

Update `yourdad` references in:
- `README.md`, `CLAUDE.md`, `CONTEXT.md`, `BACKLOG.md`
- `docs/USER-GUIDE.md`, `docs/COMPETITIVE-COMPARISON.md`, `docs/TESTING-AND-LAUNCH.md`
- `site/index.html` — command snippets, download link filename
- `.github/workflows/test-and-build.yml` — `python3 yourdad.py` → `python3 askdad.py`, `./dist/yourdad` → `./dist/askdad`

**Skip:** `docs/bugs/*`, `docs/roadmap/*` (other than this file). They are historical.

### Phase 6 — Validation

1. `./venv/bin/python -m pytest tests/ -v` → 101 green
2. `./build_executable.sh` → produces `dist/askdad`
3. `./dist/askdad --version` and `./dist/askdad cpu --terminal` → smoke test
4. `./package_for_distribution.sh` → produces `askdad-VERSION-BUILD.zip`
5. Open the bundled HTML report — confirm no `yourdad` strings in user-visible output
6. Final grep — outside `docs/bugs/` and `docs/roadmap/`, the only remaining `yourdad` references should be in this plan file:

```bash
grep -r "yourdad" --include="*.py" --include="*.sh" --include="*.md" --include="*.spec" --include="*.rb" --include="*.yml" --include="*.html" \
  --exclude-dir=docs/bugs --exclude-dir=docs/roadmap --exclude-dir=test-reports --exclude-dir=venv --exclude-dir=__pycache__
```

## Estimated effort

~1 hour focused. The risk isn't time — it's missing a string and shipping an inconsistent rebrand. The grep check in Phase 6 is the safety net.

## Migration notes

No backwards-compat shim. Anyone with a `~/.dadware/` from a previous run will not see their old reports under the new name. Acceptable for POC. If this changes (e.g. someone actually installed and is using it), add a one-shot migration: on first run, if `~/.dadware/` exists and `~/.askdad/` does not, `mv` the directory.
