# Context

The distilled brain. Summaries from chats, key decisions, open questions, tool URLs, research links.

---

## What this project is

**Ask Dad for Mac** 
A personality-driven, read-only Mac cleanup tool. Scans storage and memory, returns letter grades (A–F) with dad-style commentary and actionable advice. The user makes cleanup decisions; the tool never deletes.

Built by a real Dad for kids and non-technical adults who want to understand *why* their Mac is slow or full. Doubles as a learning tool for the Unix filesystem.

## Key decisions

- **Python stdlib only at runtime.** No external deps. PyInstaller bundles into a single executable so end users don't need Python installed.
- **macOS-only.** Relies on `vm_stat`, `system_profiler`, `sysctl`, the Apple permission model, and Apple library structures. Cross-platform is not a goal.
- **Read-only by design.** The tool never deletes; it doesn't even recommend specific deletions. This is a trust/safety constraint, not a feature gap.
- **No AI calls at runtime.** Code was written with AI assistance but the binary makes no network calls. `utils/llm_prompt.py` *generates* a prompt the user can paste into an LLM — it does not call one.
- **Dev vs prod mode auto-detection.** Presence of `.git` directory triggers dev mode (reports go to `test-reports/`); otherwise prod mode (reports to `~/.dadware/reports/`).
- **Disk-accurate sizing.** Uses `st_blocks * 512` for Docker containers and sparse files (qcow2, vmdk) so reported size matches Finder/disk usage rather than logical file size.
- **Non-recursive allowlist scanning** for Mac libraries — prevents hangs on iCloud/CloudStorage paths. `Mobile Documents` and `CloudStorage` are explicitly skipped.
- **Self-contained HTML reports.** Inline CSS/JS, no external assets — shareable as standalone files.

## Distribution model


**Currently for Proof of Concept:**

* **Landing page: **`site/index.html` — deployed on Vercel. links to the  **ZIP from GitHub Release** — `package_for_distribution.sh` produces `yourdad-VERSION-BUILD.zip` containing the PyInstaller executable, `README.md`, `USER-GUIDE.md`, and a generated `README.html`. Primary path for non-technical users.

**Next**: Apple Developer ID allows users to dowload the executable and run it. 

**Later**: MacOS App in Appstore (will wrap the program in Swift)

## Build pipeline

```
yourdad.py + modules
   │  build_executable.sh (PyInstaller, uses yourdad.spec)
   ▼
dist/yourdad
   │  package_for_distribution.sh
   │    ├── copies README.md (root)
   │    ├── copies docs/USER-GUIDE.md
   │    └── runs scripts/generate_html_readme.py → README.html
   ▼
package/  →  yourdad-VERSION-BUILD.zip
```

`build/`, `dist/`, `package/` are all gitignored and regenerated. Don't edit anything in `package/` — it gets wiped on every build. Edit the canonical README at root.

## Repo layout

```
ask-dad/
├── README.md, BACKLOG.md, CONTEXT.md, SESSION.md, CLAUDE.md, LICENSE
├── yourdad.py            # main CLI
├── yourdad                # interactive menu launcher
├── yourdad.spec           # PyInstaller spec
├── build_executable.sh, package_for_distribution.sh, install.sh
├── scanners/, renderers/, personality/, utils/   # source
├── tests/                 # 101 tests, pytest
├── scripts/generate_html_readme.py
├── Formula/yourdad.rb     # Homebrew
├── site/index.html        # Vercel landing page
└── docs/
    ├── USER-GUIDE.md      # bundled into distribution
    ├── COMPETITIVE-COMPARISON.md, TESTING-AND-LAUNCH.md
    ├── bugs/, roadmap/    # historical engineering notes
    └── archive/           # gitignored; deep history
```

## Open questions

- **CPU/RAM grading thresholds.** Storage grades have been tightened (free space: A>40%, F<10%). Memory grading hasn't gotten the same scrutiny.
- **Test plan**: how to get a beta group to test on new macs and old macs and make sure it works. 
- **Marketing:** how to get an audience interested in using it. 


## Reference / URLs

- Project repo: github.com/jbillington/dadware
- Landing page: deployed via Vercel from `site/index.html`
- Homebrew formula source: `Formula/yourdad.rb`
- PyInstaller docs: https://pyinstaller.org/

## Glossary

- **Full Disk Access (FDA)** — macOS permission required to scan Photos, Mail, Messages libraries. Tool degrades gracefully without it.
- **Memory pressure** — macOS metric (green/yellow/red) derived from `vm_stat`. More meaningful than raw "RAM used" on macOS due to compressed memory.
- **POC** — proof-of-concept release; current version is `0.1-poc`.
