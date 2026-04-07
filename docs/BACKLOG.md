# Backlog

**Last Updated:** April 4, 2026

Items are roughly priority ordered within each section. Check the box when done.

---

## Ready to Ship

Things blocking or needed for the POC release to testers.

- [ ] **Test executable on clean Mac.** The PyInstaller build has never been validated on a machine without the dev environment. Need to test on at least one Intel Mac and one Apple Silicon Mac.
- [ ] **Test the security warning flow.** Confirm right-click > Open actually works for unsigned executables on Sonoma/Sequoia. Document exact steps with screenshots if needed.
- [ ] **Update Homebrew formula.** `Formula/yourdad.rb` has placeholder URL, references old `scan` syntax, and hasn't been tested. Needs: real GitHub release URL, updated commands, test on clean system.
- [ ] **Set up Homebrew tap.** Create `homebrew-tap` repo, publish formula. This is the Reddit distribution path.
- [ ] **Create GitHub Release.** Tag v0.1-poc, upload ZIP, write release notes. Needed before sharing publicly.
- [ ] **Take screenshots.** HTML report card, terminal output, storage breakdown. Needed for Reddit post and GitHub release.

## Bugs

- [ ] **`package_for_distribution.sh` includes TECHNICAL.md.** That file was moved to docs/archive but the script still copies it. Will error on next package build.

## Code Quality

- [ ] **Add type hints.** Scanner return types are undocumented dicts. Adding TypedDicts or dataclasses would make the code easier to work with.
- [ ] **Replace `os.listdir()` with `os.scandir()` in storage scanner.** Minor performance improvement, avoids extra stat calls.
- [ ] **Standardize scanner return formats.** Storage and CPU scanners return differently shaped dicts. A consistent structure would simplify renderers.

## Features

- [ ] **Redesign report card layout.** Show component grades first (Free Space, Home Folders, Libraries), then the overall grade at the bottom. Make users read the breakdown before seeing the final score. Add a short comment to each component grade explaining what it means (e.g., "22% free. Getting tight." or "Downloads is clean. Nice work.").
- [ ] **`--json` flag.** Output scan results as JSON to stdout. Enables agent/automation use cases. Low effort, high value.
- [ ] **`--prompt` flag.** Output just the LLM-ready prompt to stdout. Lets AI agents request system context directly.
- [ ] **Lightweight TUI.** Replace the menu launcher with a curses-based TUI. Three screens: menu, progress, summary. See `docs/roadmap/LIGHTWEIGHT-TUI-PLAN.md`. No new dependencies (stdlib curses only).
- [ ] **Expand personality comments.** More variety in dad comments. Current set gets repetitive if you run it often.
- [ ] **Report history.** Simple list of past reports with dates and grades. Nothing fancy, just `yourdad history` listing what's in the reports folder.

## Future (Post-POC)

- [ ] **Duplicate file detection.** Find duplicate files by hash. This was the v0.2 plan. 20-30 hours.
- [ ] **Swift macOS app.** Native GUI wrapping the Python scanners. The long-term direction if the tool gets traction.
- [ ] **Code signing.** Apple Developer ID ($99/year) to eliminate the security warning. Worth it if there's real adoption.
- [ ] **MCP server.** Expose scans as MCP tools so AI agents can call Dad Ware directly. Depends on `--json` being done first.

## Done (This Session)

- [x] Simplify CLI: flatten `yourdad scan storage` to just `yourdad`
- [x] Move shared flags to top level (no more duplication across subparsers)
- [x] Refactor utils into dedicated modules (formatters, path_utils, subprocess_utils)
- [x] Fix `parse_size()` bug (unit matching checked 'B' before 'MB')
- [x] Fix diagnostic logging (was hardcoded on, now env var)
- [x] Write 101 unit tests
- [x] Update PyInstaller spec with new util modules
- [x] Update menu launcher for new CLI syntax
- [x] Simplify README (170 lines to 40)
- [x] Update all docs for new commands
- [x] Write user guide
- [x] Write competitive comparison doc
- [x] Write testing and launch plan
- [x] Write lightweight TUI plan
- [x] Clean up root directory, archive old files
- [x] Build new executable and ZIP
- [x] Add CLAUDE.md
