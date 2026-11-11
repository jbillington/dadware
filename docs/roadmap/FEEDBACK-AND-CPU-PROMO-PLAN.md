# Feedback invitation and CPU-scan cross-promo

**Status:** implemented Nov 11, 2026 (see CHANGELOG). Still to do: rebuild and re-sign the `.app` for part A, and check it on a Mac whose `.zshrc` has no `askdad` of its own.
**Goal:** (1) beta testers know they can email John, in the terminal and in the report. (2) After a storage scan, users learn the CPU/RAM scan exists and how to run it.

## Why

The beta exists to get feedback, and today nothing asks for it. Separately, the CPU scan is invisible unless you read the docs: a tester who runs `askdad` never learns that `askdad cpu` exists.

## Decisions I made
1. **The email address.** use john@dadware.net 

2. **How `.app` users run the CPU scan: decided Nov 11, 2026.** `askdad cpu` only works where `askdad` is on the PATH (a source checkout, the zsh function, the Homebrew tap). The signed `.app` is a thin launcher: `make_app.sh` opens Terminal on `AskDad.command`, which runs the bundled binary (inside `Ask Dad.app/Contents/Resources/`) and then drops into a login shell. So `.app` users have a Terminal window but no `askdad` command. Fix, both parts:
   - **B. Ask at the end of the scan.** After a storage report, when stdin is a TTY, print `Want me to check your memory and CPU too? [y/N]`. On `y`, call `run_cpu_scan()` and save and open the CPU report. Works identically in the `.app`, Homebrew and source channels with no PATH dependence. Non-TTY, `--terminal` and `askdad all` runs skip it. Default is no.
   - **A. Put the bundled binary on the PATH.** In `make_app.sh`'s `AskDad.command`, `export PATH="$HERE:$PATH"` (with `HERE` the Resources folder) before the final `exec "$SHELL" -l`, so typing `askdad cpu` works in the window the app leaves open. Tested Nov 11 with a stand-in binary under a path containing a space ("Ask Dad.app"): a login shell found it and ran it. Needs a rebuild and re-sign of the app, and a real check on a Mac whose `.zshrc` does not define its own `askdad`.

  

## Design

### One place for the copy

New `utils/promo.py` holding:

- `FEEDBACK_EMAIL` (single constant, the only place the address lives - replace with john@dadware.net)
- `feedback_line()` and `cpu_promo_line(scan_type)` returning plain strings
- optional `mailto:` builder: `mailto:ADDRESS?subject=Ask%20Dad%20feedback%20(v1.0-beta)`. The subject carries the version only. **Never put scan data, paths or the report in the mailto body**: the tool's trust story is that nothing leaves the Mac without the user choosing to send it.

Both renderers import from it, so the terminal and the report cannot drift.

### Terminal

The CPU hint on a storage run is the `[y/N]` prompt from decision 2 (B), not just a printed command; the wording below shows the non-interactive fallback.

Printed at the very end of a run, after the report path and the permission offer, before or after the timing summary (the summary is a dev aid, so feedback goes last in front of the user).

Storage scan (`askdad`):

```
Next - Ask Dad to scan your memory and CPU.  Run:  askdad cpu

Send me an email!  I would love to hear if Ask Dad was useful or could be better. 
john@dadware.net 
```

CPU scan (`askdad cpu`): same feedback line, and a mirror promo, "Curious about your storage? Run: askdad".

`askdad all`: no CPU promo (both scans just ran), feedback line only.
`--terminal`, non-TTY or scheduled runs: skip both. A cron job does not want marketing in its log. Gate on `sys.stdout.isatty()`.

Voice: Dad's, short, no exclamation marks, one blank line above so it does not blur into the report.

### HTML report

- **Footer** (`render_ai_prompt_section()` already writes it, `renderers/html.py` ~line 2643): add a feedback paragraph above the version line, with a `mailto:` link and the plain address beside it (some browsers have no mail handler, so the address must be visible text).
- **CPU promo box**, storage report only: a small card above the footer, after the AI prompt section. Text: "Your Mac has a memory and CPU report too." plus the command in a monospace block with a Copy button (reuse the `copyPromptToClipboard()` pattern). A report cannot launch a command, so it shows one.
- **CPU report** gets the mirror card for storage, and the same feedback footer.
- Drive reports (`scan_scope == 'other_volume'`) get the feedback footer but **no CPU promo**: a thumb-drive report is not the place to talk about the Mac's memory.
- All text is static, so nothing needs `escape_html`, but the address still goes through it as a habit.

### Channel-aware wording

Decide how to tell which channel launched the run (an env var the `.app` launcher sets, or a frozen-binary check like `sys.frozen`/`utils/path_utils` dev-mode detection). Wording per channel:

| Channel | CPU promo text |
|---|---|
| CLI / source / Homebrew | "Run `askdad cpu`" |
| Signed `.app` | The end-of-scan `[y/N]` prompt (B) is the main route. The command text ("type `askdad cpu` in this Terminal window") is only printed once A has shipped, so it is never a command that fails. |

## Tests

- `feedback_line()` contains the configured address; changing `FEEDBACK_EMAIL` changes both renderers.
- The end-of-scan prompt: `y` runs the CPU scan and saves its report, `n`/Enter/EOF do not; no prompt without a TTY.
- `make_app.sh` (A): a shell test that `AskDad.command` puts its own folder on `PATH` before the final shell (the stand-in-binary check from decision 2).
- Terminal: storage run output ends with the CPU promo and feedback; `all`, `--terminal` and non-TTY runs do not carry the CPU promo.
- HTML: storage report has the CPU card and feedback link; CPU report has the storage card; a drive report has feedback but no CPU card.
- `mailto:` link contains the version and **no** scan data (assert on the full href).
- Regenerate `tests/fixtures/storage_scan.snapshot.html` and `cpu_scan.snapshot.html`, and read the diff: only the footer and the new card should change.
- `scripts/render_scenarios.py` gallery: eyeball the footer in all 15 states.

## Files touched

`utils/promo.py` (new), `askdad.py` (print at end of `storage`/`cpu` branches; the `[y/N]` prompt), `make_app.sh` (PATH line), `renderers/html.py` (footer, promo card), `renderers/terminal.py` only if the lines are easier to build there, `tests/`, the two snapshot fixtures, `docs/USER-GUIDE.md` (mention the CPU scan), `README.md`.


