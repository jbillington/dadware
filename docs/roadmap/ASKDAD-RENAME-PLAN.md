# Rename: `yourdad` → `askdad`

**Status:** Executed Aug 28, 2026 — see `CHANGELOG.md`. The `yourdad` references below are accurate to when the plan was written. Original constraint, satisfied: the rename had to land before the first signed build, because macOS keys permission grants to bundle ID + code signature, so the identity (`com.dadware.askdad`) had to be final before any user grants Full Disk Access to a signed Dad Ware (see `PERMISSIONS-PLAN.md`).

Plan for renaming the program from `yourdad` to `askdad`, aligning the codebase with the user-facing "Ask Dad for Mac" brand.

**Re-verified against the codebase 2026-08-16, after the code-review refactor landed on main.** Updated line references: banner at `yourdad.py:163`, report paths at `yourdad.py:38,52`, helper-app paths at `utils/permissions.py:20-21`, stale `scan cpu` hint at `renderers/html.py:2011`. The test suite is now **227 tests** (grew from 101 in the refactor — Phase 6's validation count below is updated). Occurrence counts by file (fresh grep, excluding historical docs and test fixtures): `tests/test_cli.py` 27, CI workflow 20, `scripts/generate_html_readme.py` 13, `install.sh` 10, `Formula/yourdad.rb` 9, `yourdad.spec` 5, `tests/test_version.py` 5, `build_executable.sh` 5, `sign_and_notarize.sh` 4, `package_for_distribution.sh` 4, `yourdad.py` 3, `tests/test_personality.py` 2, `scanners/grading.py` 2 (comments), plus single references in `tests/test_models.py`, `entitlements.plist`, the four package `__init__.py` files, `utils/subprocess_utils.py`, and `renderers/html.py`.

**New files in scope since the refactor** (add to the phases below): `sign_and_notarize.sh` and `entitlements.plist` (Phase 3 — build/install scripts; the entitlements comment and script paths reference `yourdad`), `tests/test_version.py` and `tests/test_models.py` (Phase 2 — test references), and comment-level mentions in `scanners/grading.py`. `utils/version.py` derives the build number from git and has no name coupling. The modernized `yourdad.spec` still has the same five rename points (`Analysis(['yourdad.py'])`, `name='yourdad'`, `personality.yourdad` hidden import).

**Re-verified again 2026-08-26, pre-execution.** Four additions for the executing session — the phases below are still correct, apply these on top:

1. **The HTML snapshot fixture will break tests and must be regenerated** (add to Phase 4). `tests/fixtures/cpu_scan.snapshot.html` contains the stale `python3 yourdad.py scan cpu` hint, and `test_normalized_snapshot_matches` in `tests/test_html_render.py` compares rendered output to the fixture **byte-for-byte** — so Phase 4's fix to the hint in `renderers/html.py` fails that test until the snapshot is regenerated:

   ```bash
   ./venv/bin/python -c "from tests.test_html_render import regenerate_snapshot as r; r('cpu_scan.json', 'cpu_scan.snapshot.html')"
   ```

   Review the regenerated file with `git diff` — the only change should be the hint text. `storage_scan.snapshot.html` has no `yourdad` reference and should not change.

2. **Three docs are missing from Phase 5's list.** `docs/BUILDING.md` (16 hits) and `docs/GRADING.md` (5 hits) are active reference docs — update them. `docs/CODE-REVIEW.md` (5 hits) is the record of a completed review, so it falls under the historical leave-as-is rule despite living in `docs/` root — skip it and exclude it from the Phase 6 grep (the command below already does).

3. **Phase 6's grep command was broken as originally written.** `--exclude-dir` matches directory *basenames*, not paths, so `--exclude-dir=docs/bugs` excluded nothing and ~89 historical hits leaked through. The command in Phase 6 below is corrected (`--exclude-dir=bugs --exclude-dir=roadmap`) and verified against the current tree.

4. **Occurrence counts have grown since 2026-08-16** — `tests/test_cli.py` is now 37 hits (was 27) and the CI workflow 21 (was 20) — and the cited line numbers (banner, `renderers/html.py` hint, `install.sh` echoes) have shifted. Treat every count and line reference in this plan as approximate: locate each rename point by grepping, and trust the Phase 6 grep as the completeness check, not the tallies above.

**Scope revised 2026-08-28.** Two decisions changed; the phases below are updated to match:

- **`~/.dadware/` stays.** Dadware is the *publisher* of the askdad program — a publisher-named state dir is the normal pattern and matches the bundle ID (`com.dadware.askdad`, publisher segment `dadware`). This also deletes the plan's only user-facing breakage: existing reports stay where the tool looks for them, and no migration shim is ever needed.
- **`personality/yourdad.py` renames to `personality/dad.py`, not `askdad.py`.** The module is Dad's personality, so it's named for the *persona*, not the program. This leaves room for future personas (`personality/mom.py`, …) sitting side by side behind the same `add_personality(scan_data) -> {comments, tips, status}` interface. Note for that future work: today the module fuses the analysis (thresholds, which folders to check) with the voice (the comment strings) in one function — before adding a second persona, the analysis moves into `scanners/grading.py` (which already inspects the same folders) so personas share one set of findings and only swap the lines. Filed in `BACKLOG.md` under Code Quality; not part of this rename.

## Decisions (locked)

| Question | Decision |
|---|---|
| `~/.dadware/` state dir | **Keep as-is.** Dadware is the publisher of askdad; the state dir carries the publisher name. Old reports remain visible; no migration. |
| `personality/yourdad.py` module | Rename to `personality/dad.py` — named for the persona, keeping the door open for other personas later. |
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
| `personality/yourdad.py` | `personality/dad.py` |
| `Formula/yourdad.rb` | `Formula/askdad.rb` |
| `~/.dadware/` | `~/.dadware/` (unchanged — publisher dir) |
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
git mv personality/yourdad.py personality/dad.py
git mv Formula/yourdad.rb Formula/askdad.rb
```

Tests will fail after this — that's the checkpoint.

### Phase 2 — Update Python imports and internal references

- `askdad.py`: `from personality.yourdad import add_personality` → `from personality.dad import add_personality`
- `askdad.spec`:
  - `Analysis(['yourdad.py'], ...)` → `['askdad.py']`
  - `EXE(name='yourdad', ...)` → `name='askdad'`
  - `hiddenimports` entry `'personality.yourdad'` → `'personality.dad'`
- `utils/subprocess_utils.py:7`: update comment about avoiding circular imports from `yourdad`
- `tests/test_cli.py`: 5 occurrences of `"yourdad.py"` → `"askdad.py"`; if any test asserts banner text, update it
- `tests/test_personality.py`: docstring `"""Tests for personality/yourdad.py"""` → `personality/dad.py`

Run `pytest` — should be green.

### Phase 3 — Update build/install scripts

- `build_executable.sh`: `yourdad.py` → `askdad.py` (3 spots), `yourdad.spec` → `askdad.spec`, `dist/yourdad` → `dist/askdad`, user-facing echo strings
- `package_for_distribution.sh`: `dist/yourdad` → `dist/askdad`, `yourdad.py` → `askdad.py`, zip naming `yourdad-${VERSION}-${BUILD}.zip` → `askdad-${VERSION}-${BUILD}.zip`
- `install.sh`:
  - `INSTALL_DIR="$HOME/.dadware"` — **unchanged** (publisher dir stays)
  - `chmod +x "$INSTALL_DIR/yourdad"` → `askdad`
  - symlink `~/.local/bin/yourdad` → `askdad`
  - **fix latent bug:** the script echoes `~/yourdad_reports/` but the program actually writes to `~/.dadware/reports/`. Point the echo at `~/.dadware/reports/`.
  - **fix second stale echo:** line 128 tells the user to `open ~/.dadware/index.html` — that file no longer ships (root `index.html` was deleted in the May 2026 hygiene pass). Remove or repoint the echo.
- `Formula/askdad.rb`:
  - Class `Yourdad` → `Askdad`
  - `bin.install "yourdad.py"` → `askdad.py`
  - Wrapper script content (path to interpreter and module)
  - Leave `homepage "https://github.com/jbillington/dadware"` as-is (repo not renamed)

Run `./build_executable.sh` end-to-end — confirm `dist/askdad`.

### Phase 4 — User-facing strings in code

- `askdad.py:163`: banner `"Dad Ware  |  yourdad v{VERSION}"` → `"Ask Dad for Mac v{VERSION}"`
- Report paths in `askdad.py` (`~/.dadware/reports`) — **unchanged** (publisher dir stays)
- `utils/permissions.py:20-21`: paths to `PermissionHelper.app` — the `~/.dadware/PermissionHelper.app` path stays; update only `/Applications/DadWare.app/...` → `/Applications/AskDad.app/Contents/Resources/PermissionHelper.app` (the helper app doesn't exist yet, but the app-bundle path needs to match the new naming for when it does)
- `renderers/html.py:2011`: hint `python3 yourdad.py scan cpu` → `askdad cpu` (also fixes the stale `scan` syntax)
- `scripts/generate_html_readme.py`:
  - line 293: extracted dir name in setup instructions
  - line 302: command example `./yourdad scan storage` → `./askdad`
  - line 356: reports path `~/.dadware/reports/` — **unchanged**

### Phase 5 — Docs (active only; historical left untouched)

Update `yourdad` references in:
- `README.md`, `CLAUDE.md`, `CONTEXT.md`, `BACKLOG.md`
- `docs/USER-GUIDE.md`, `docs/COMPETITIVE-COMPARISON.md`, `docs/TESTING-AND-LAUNCH.md`
- Note: README.md and USER-GUIDE.md gained "Options" sections (Aug 2026) with many `./yourdad` command examples — the grep in Phase 6 catches them, just expect more hits in those two files than the original estimate.
- Mentions of the reports location (`~/.dadware/reports/`) in any doc are **correct and stay** — only the command name and executable references change.
- `site/index.html` — command snippets, download link filename
- `.github/workflows/test-and-build.yml` — `python3 yourdad.py` → `python3 askdad.py`, `./dist/yourdad` → `./dist/askdad`

**Skip:** `docs/bugs/*`, `docs/roadmap/*` (other than this file). They are historical.

### Phase 6 — Validation

1. `./venv/bin/python -m pytest tests/ -v` → 227 green (1 skip)
2. `./build_executable.sh` → produces `dist/askdad`
3. `./dist/askdad --version` and `./dist/askdad cpu --terminal` → smoke test
4. `./package_for_distribution.sh` → produces `askdad-VERSION-BUILD.zip`
5. Open the bundled HTML report — confirm no `yourdad` strings in user-visible output
6. Final grep — outside the historical docs (`docs/bugs/`, `docs/roadmap/`, `docs/CODE-REVIEW.md`), the only remaining hits should be lines in *active* docs that intentionally mention the old name (e.g. "renamed from `yourdad`"), if you keep any:

```bash
grep -rn "yourdad" --include="*.py" --include="*.sh" --include="*.md" --include="*.spec" --include="*.rb" --include="*.yml" --include="*.html" \
  --exclude-dir=bugs --exclude-dir=roadmap --exclude-dir=test-reports --exclude-dir=venv --exclude-dir=__pycache__ \
  --exclude=CODE-REVIEW.md .
```

(Note `--exclude-dir` matches directory basenames — `--exclude-dir=docs/bugs` silently excludes nothing.)

## Coordination with the signed-app work

The rename must land **before** the first signed build (`PERMISSIONS-PLAN.md`, Milestone 3): macOS keys permission grants to bundle ID + signature, so the identity users first grant access to must be the final one. Sequencing details:

- This plan renames the *current* bare-executable `yourdad.spec`. The `.app`-bundle conversion (PyInstaller onedir, `Info.plist`, usage strings) happens afterward in Milestone 3 and should be built on the already-renamed `askdad.spec` with bundle ID `com.dadware.askdad`.
- `utils/permissions.py` helper-app paths: `~/.dadware/PermissionHelper.app` stays (publisher dir); the app-bundle path becomes `/Applications/AskDad.app/...` — the helper doesn't exist yet, but Milestone 3's bundle should adopt these paths as-is.

## Estimated effort

~1 hour focused. The risk isn't time — it's missing a string and shipping an inconsistent rebrand. The grep check in Phase 6 is the safety net.

## Migration notes

None needed. The state dir stays `~/.dadware/` (2026-08-28 scope revision), so existing reports remain exactly where the tool looks for them. Nothing a user has on disk moves or breaks.
