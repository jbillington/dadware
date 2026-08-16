# Dad Ware — Technical Code Review

> **Status: implemented — historical record.**
> Every recommendation below, including the product-level note, was carried out
> in the ten commits `db06f88` through `ecc32f4` (merged to `main` on 2026-08-15). This
> document is kept as the rationale for those changes; it is **no longer a
> to-do list**. Read it for *why*, not for *what's outstanding*.
>
> Highlights of the outcome:
> - Scanner walks the disk once instead of twice: **3.60s → 1.09s** on a
>   40,000-file tree, ~8 filesystem syscalls per file down to ~1.
> - `main()` de-duplicated, which fixed `all` silently ignoring `--top` and
>   `--min-size`.
> - Scan data is escaped before reaching the HTML report, closing the
>   injection hole noted in section 4.
> - Test suite grew from 101 to 227 tests, including golden-output snapshots
>   that pin the HTML report's behavior.
>
> Two items were deliberately **not** changed, because both would alter grades
> users already see and are product decisions rather than code defects — see
> [GRADING.md](GRADING.md): the home-folder clutter grade can never return a C,
> and it is excluded from the composite score.

*A review of the Python codebase (~6,900 lines) focused on efficiency, simplicity, and future maintainability. As originally written, no code changes accompanied this document — it was a findings and recommendations report only.*

**Overall verdict:** the code is clear and readable line-by-line, but it is heavily duplicated, the scanner does a lot of redundant disk I/O, and everything flows through untyped dicts. Those three things are what make it slow to run and risky to modify. All of them are fixable without changing the product at all.

---

## What's already good

- **Clean separation of concerns.** CLI → scanners → personality → renderers is the right shape, and modules genuinely stay in their lanes.
- **Zero-dependency stdlib approach is honored consistently.**
- **Defensive error handling** around filesystem access (permissions, symlinks, sparse files) shows real-world hardening.
- **The test suite covers the right things** — pure logic like grading thresholds and path exclusion — rather than testing trivia.

---

## 1. Efficiency: the scanner walks the disk twice (or more)

This is the biggest real-world performance issue. In `scanners/storage.py`:

1. `scan_storage()` walks the **entire volume** with `os.walk` (line 162), accumulating folder sizes as it goes.
2. Then, for each of the top 50 folders, it calls `scan_folder_contents()` (line 284), which calls `get_folder_size(max_depth=10)` on every subfolder — **recursively re-walking directory trees it just walked**.

On a large volume the second pass can cost as much as the first. Since the first walk already visits every file, it could populate per-folder file lists and subfolder aggregates in the same pass (a dict keyed by parent directory), eliminating the second walk entirely.

**The per-file syscall count is also 3–5× higher than it needs to be.** For each file the hot loop does: `os.path.islink()` (one `lstat`), `get_file_size()` → `is_docker_path()` + `is_sparse_file()` (which itself does `isfile` + `getsize` + `stat` — three more syscalls), then `os.path.getmtime()` (another `stat`). `os.walk` is built on `os.scandir`, whose `DirEntry` objects cache stat results — but the code discards them by taking only the names. Rewriting the walk around `os.scandir` directly, using `entry.is_symlink()` and a single `entry.stat()` per file, would cut syscalls per file from ~5 to 1. On a spinning disk or a huge SSD volume, that's the difference between a 2-minute and a 30-second scan.

Smaller efficiency notes:

- `is_sparse_file()` (`utils/path_utils.py:35`) runs on *every* file via `get_file_size()`. The extension check is cheap, but the ratio check stats the file again. Pass an already-obtained `stat_result` in instead.
- Pattern lists in `is_docker_path()` and `should_skip_path()` are rebuilt on every call — hoist them to module-level constants (also makes them documentable/configurable in one place).
- `scan_storage()` computes metrics inline (`storage.py:305-310`) that duplicate `grading.calculate_storage_metrics()` — same math, two places to drift.

---

## 2. Duplication: `yourdad.py`'s `main()` is three copies of the same program

`main()` is ~490 lines, and the `storage`, `cpu`, and `all` branches each repeat the identical ~50-line "make reports dir → timestamp → render HTML → write JSON manifest → open browser" block (lines 326-359, 384-417, 552-612).

Worse, the `all` branch re-implements the whole storage flow with **drift**: it hardcodes `top_n=500` and `min_size_bytes=0`, silently ignoring the user's `--top` and `--min-size` flags (`yourdad.py:430-436`), and it wraps the permission check and CPU scan in try/excepts that the standalone paths don't have. That's the classic copy-paste failure mode — a fix lands in one branch and not the other.

The restructure is mechanical:

```python
def save_and_open_report(scan_data, personality_data, prefix, args) -> None: ...
def run_storage_scan(args) -> dict | None: ...
def run_cpu_scan(args) -> dict | None: ...
```

Then `all` becomes literally `run_storage_scan(args)` + `run_cpu_scan(args)`, the drift bugs disappear by construction, and `main()` drops to ~150 lines of argument parsing and dispatch.

Other notable duplication:

- **Two `get_folder_size()` implementations** — `scanners/storage.py:36` and `scanners/mac_libraries.py:12`, nearly identical, differing only in sizing function and skip rules. One function with a `size_fn`/`skip_fn` parameter would replace both.
- **Downloads/Desktop detection exists twice** — `grading.grade_home_folders_clutter()` and `personality.add_personality()` both loop over `top_folders` doing substring matches. Extract a `find_folder(top_folders, name)` helper. The matching itself is buggy: `'Downloads' in folder_path` matches *any* path containing "Downloads" anywhere (e.g. `Backups/Old-Downloads-Archive/video`), and `merge_home_folders()` (`yourdad.py:157`) is even looser with case-insensitive substring checks — `'documents' in path` matches paths that merely mention documents. Matching on `os.path.basename(path) == name` is both correct and simpler.
- **Volume statvfs math exists twice** — `utils/volumes.get_volume_info()` and inline in `scan_storage()` (`storage.py:292-298`).

---

## 3. Extensibility: untyped dicts are the tax on every future change

Every layer communicates via nested dicts, so every consumer is littered with `folder.get('path', '') or folder.get('path_display', '')` and `scan_data.get('volume_info', {}).get('used_bytes', 0)`. Nothing catches a typo'd key, and the shape of "a scan result" is documented nowhere — it has to be reverse-engineered from the renderer.

Since the project is stdlib-only, `dataclasses` are free:

```python
@dataclass
class FolderInfo:
    path: str
    display: str
    size_bytes: int
    is_docker: bool = False
    top_files: list = field(default_factory=list)
```

with a `to_dict()` for JSON manifests. This is the single highest-leverage "humanizing" change: the data model becomes self-documenting, editors autocomplete it, and refactors like sections 1 and 2 become far safer. Adding type hints on function signatures (supported fine on the Python 3.9 CI target) compounds the benefit.

The same pattern issue appears in `identify_memory_hogs()` (`cpu.py:126-157`): a 30-line if/elif chain mapping process names to app families. As a data table — `APP_FAMILIES = [('chrome', 'Chrome'), ('safari', 'Safari'), ...]` — adding an app becomes a one-line change instead of an elif. Two of its branches are also dead: the `system_processes`/`helper_processes` lists are created and never used, and the `'WindowServer'` check can never match because `name` was lowercased first.

---

## 4. The 2,000-line HTML renderer

`render_html()` is essentially one giant f-string. It works, but it's the hardest file in the repo to modify safely — a stray `{` breaks the whole report, and CSS/markup/data-injection are interleaved. Without adding dependencies:

- **Split it into per-section functions** (`render_report_card()`, `render_folder_chart()`, `render_cpu_section()`, …) that each return an HTML fragment; `render_html()` just concatenates.
- **Move the CSS and JS into module-level constants** (plain strings, no f-string escaping needed — this alone removes hundreds of doubled `{{}}`).
- **One real risk worth checking:** scan data (file paths, process names) appears to be interpolated into HTML without escaping. A file named `<script>...` on disk would inject into the report. Route all dynamic strings through `html.escape()` (stdlib).

---

## 5. Correctness bugs found along the way

- **`renderers/terminal.py:24-26` mutates global color constants.** After one `render_terminal(use_color=False)` call, colors are permanently stripped for the rest of the process — the globals are never restored. Use a small palette dict chosen per-call instead of `global`.
- **`utils/path_utils.py:21`: `'Docker.raw'` can never match** — it's compared against `path.lower()`. Dead pattern; should be `'docker.raw'`.
- **`scanners/cpu.py:301`: `except Exception as e: return None`** (and a bare `except:` at line 250) swallow every error silently, so a failed CPU scan gives the user "Error: Could not scan CPU/RAM" with no way to learn why. Print `e` to stderr, or at least honor `DIAGNOSTIC_LOGGING` the way `yourdad.py` does.
- **`utils/formatters.py:4`: `format_size(bytes)`** shadows the `bytes` builtin and mutates its parameter; it also returns `-512.0 B`-style output for negative inputs (which `used_bytes` math can produce on unusual mounts). Rename the parameter and clamp.
- **`yourdad.py:1`:** shebang `#!/usr/bin/python3` should be `#!/usr/bin/env python3` — the hardcoded path doesn't exist on Macs using Homebrew/pyenv Python and is being phased out of macOS.
- **`getattr(args, 'test_reports', False)` in three places** — argparse always sets the attribute, so plain `args.test_reports` is fine.

---

## Suggested order of attack

1. **Extract the shared report-saving path and de-duplicate `main()`** — pure mechanical refactor, fixes the `--top`/`--min-size`-ignored bug in `all`, zero behavior risk elsewhere. Do this first because it shrinks the surface for everything after.
2. **Fix the small correctness bugs** (terminal globals, `Docker.raw`, silent excepts, HTML escaping) — each is a few lines.
3. **Introduce dataclasses for scan results** — the enabler for safe future work.
4. **Single-pass scanner rewrite on `os.scandir`** — the big performance win; do it after step 3 so the new walk produces typed objects and the tests can pin behavior.
5. **Split `html.py` into section functions** — do it last and opportunistically; it's the biggest file but the least risky to leave alone.

---

## Product-level note

The bones are genuinely good — read-only by design, personality as a differentiator, self-contained reports. The one product-level thing the code structure fights against is the interactive volume prompt in `select_volume()`, which blocks any scripted or scheduled use ("run every Sunday, email me the report card" is a very dad-appropriate feature). Making the CLI fully non-interactive by default would open that up for free.
