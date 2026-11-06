# Persona Plan — "Dad's guess at who you are"

**Status:** Concept — not scheduled. A brainstorm captured in Nov 2026 while it was fresh. Nothing here changes the current roadmap.
**Related:** `docs/GRADING.md` §9 (libraries become facts with context — "normal for *whom*" is this document's question), `scanners/hidden_storage.py` (`build_app_name_index()` and `DEVELOPER_PATHS` are the first two signal sources), `FAMILY-HELPER-CONCEPT.md` (the "looks only at sizes and settings, never at content" line, which this feature keeps).

---

## The idea

The scan already knows what apps are installed, what the big folders are called, and every file's extension and size. From that it can make a good guess at what the person *does* with the Mac — developer, photographer, student, gamer — and the guess is worth having for three reasons:

1. **Advice gets better.** A 90 GB Logic sound library is a musician's instrument, not clutter. A 40 GB `node_modules` pile is a developer's chore and nobody else's. Today the report has one set of thresholds for everyone, and `GRADING.md` §9 wants libraries described as "normal for a family library" — normal depends on who you are.
2. **The report gets more fun.** "Dad's guess: you're a photographer who dabbles in video. Am I close?" is a line people screenshot. It is a guessing game the user can win by correcting it.
3. **The LLM prompt gets a first sentence.** "I'm a web developer with a 2023 MacBook Pro" changes every answer the model gives. The user pastes it themselves; nothing leaves the Mac.

It is a feature of the *advisor*, not the scanner. It changes copy, thresholds and which chores apply. It measures nothing new.

---

## Where the signals come from

Every source is a name, an extension, a path or a size. **The tool never opens a file for its content.** That is the same line the family helper concept draws, and it is what makes the feature safe to put in front of a kid.

| Source | What it gives | Cost | Already collected? |
|---|---|---|---|
| App bundles in `/Applications`, `~/Applications` | Which apps are installed, each one's size | None | Yes — `build_app_name_index()` and the walk's `is_bundle` rows |
| The Dock | Which apps the person *reaches for*. `~/Library/Preferences/com.apple.dock.plist`, key `persistent-apps`, read with `plistlib` | One file read | No |
| File extensions from the walk | Counts and bytes by extension | None | No — the walk keeps a `stat_result` per file but does not tally extensions |
| `DEVELOPER_PATHS` and the dot-folder sweep | Xcode, Docker, npm, Cargo, Go, Ollama, Hugging Face, `.config`, `.vim`, `.zshrc` | None | Yes |
| Mac libraries | Photos, Music, Messages, Mail, Creative Apps sizes | None | Yes |
| `~/Library/Audio/Plug-Ins`, `~/Library/Fonts` | Audio plug-in count; installed font count | One `scandir` each | No |
| `~/Library/CloudStorage`, `~/Library/Mobile Documents` | Which cloud providers are set up (Dropbox, Google Drive, OneDrive, iCloud). Names only — these paths are deliberately never walked | One `listdir` | No |
| `/opt/homebrew`, `/usr/local/Cellar` | Homebrew present, and how many formulae | One `listdir` | Partly — `/opt/homebrew` appears as a folder row |
| Running processes (CPU scan) | What is open right now | None | Yes |
| iPhone/iPad backups | Device names and dates — "has an iPhone", "has three kids' iPads" | One plist per backup | Planned under "Metrics worth adding" |
| Login items / launch agents | Always-on tools (Alfred, Raycast, Dropbox, Steam) | One `launchctl list` | Planned under "Metrics worth adding" |

**What is deliberately not a source:** file *names* beyond their extension, folder names below the top two levels, the contents of any file, Mail, Messages, browser history, Photos faces or albums, Contacts, Calendar. Nothing under `~/Library/Containers`.

---

## The signal table

A persona is a bag of weighted signals. Each signal is one test over the sources above. The score is the sum of the weights of the signals that fire; the top one or two personas with a score over a floor are the guess. Weights are a first guess and belong in one table, not in code.

| Persona | Strong signals (3) | Medium signals (2) | Weak signals (1) |
|---|---|---|---|
| **Developer** | Xcode, VS Code, Cursor, JetBrains, Homebrew with 20+ formulae, `node_modules` folders, `.git` folders in Documents/Projects | Docker/OrbStack/Colima, iTerm/Warp/Ghostty, `.zshrc`/`.config`, Go/Cargo/Gradle caches, Postman, TablePlus | GitHub Desktop, Sublime, many `.json`/`.yaml`/`.md` |
| ↳ *iOS developer* | Xcode plus iOS DeviceSupport or CoreSimulator runtimes, `.xcodeproj` | TestFlight, Transporter, SF Symbols | |
| ↳ *Data / ML* | Jupyter (`.ipynb`), conda/miniconda, Ollama/LM Studio/Hugging Face caches, `.gguf`/`.safetensors`, large `.parquet`/`.csv` | RStudio/`.R`, Positron | Tableau |
| **Designer** | Figma, Sketch, Adobe XD, 50+ fonts in `~/Library/Fonts` | Illustrator, Photoshop, Affinity, `.fig`/`.sketch`/`.ai`/`.psd` by count | Zeplin, Principal, Spline, Pixelmator |
| **Photographer** | Lightroom catalog (`.lrcat`), Capture One, RAW files by bytes (`.cr2` `.cr3` `.nef` `.arw` `.raf` `.dng` `.orf`) | Photos library over 100 GB, Photoshop, Photo Mechanic | Many `.heic` only (that is everyone with an iPhone) |
| **Videographer / creator** | Final Cut, DaVinci Resolve, Premiere, `.mov`/`.mp4`/`.braw`/`.mxf` by bytes, Final Cut library bundles | OBS, Screenflow, Motion, After Effects, Frame.io | Handbrake, many Screen Recordings |
| **Musician / podcaster** | Logic, Ableton, Pro Tools, GarageBand library over 10 GB, audio plug-ins present, `.wav`/`.aif`/`.flac` by bytes | Audacity, Descript, Reaper, `.mid`/`.band`/`.logicx`, Native Instruments/Kontakt libraries | Spotify local files, Music library over 50 GB |
| **3D / maker** | Blender, `.blend`/`.stl`/`.obj`/`.fbx`, slicers (PrusaSlicer, Bambu Studio, Cura), `.gcode`/`.3mf` | Fusion 360, SketchUp, Rhino, `.dwg`/`.skp`, Unity/Unreal | Shapr3D |
| **Gamer** | Steam with `steamapps` over 20 GB, Epic, Battle.net, GOG | Minecraft folder, Roblox, Discord, controller apps | CrossOver/Whisky/GPTK, Parallels with a Windows VM and Steam inside |
| **Student** | Notability/GoodNotes/Zoom/Google Classroom together, folders named by course pattern at depth 2 only (`CS101`, `Fall 2026`) | Many `.pdf` and `.pptx` by count, Quizlet, Anki, Grammarly | `.pages` and `.key` by count |
| **Writer / academic** | Scrivener, Ulysses, Zotero, `.tex`/`.bib`, Obsidian vault | Many `.docx`/`.md` by count, Mendeley, Papers | Word, Notion |
| **Office / business** | Microsoft Office and OneDrive and Teams together, QuickBooks, `.xlsx` by count | Slack, Zoom, Google Drive, Keynote decks by bytes | Acrobat |
| **Windows switcher** | Parallels/VMware/UTM with a Windows disk image | OneDrive, Edge as a browser, Office | Many `.exe`/`.msi` in Downloads |
| **Mac power user** | Alfred/Raycast, Karabiner, Hammerspoon, BetterTouchTool, Homebrew | Bartender, iStat Menus, CleanShot, 1Password CLI | Many menu-bar login items |
| **AI tinkerer** | Ollama, LM Studio, `.gguf`/`.safetensors` by bytes, Hugging Face cache | Claude/ChatGPT desktop, Cursor, MCP configs under `~/.config` | — |
| **Everyday Mac** | *Default when nothing above clears the floor.* Safari, Photos, Messages, Mail; iPhone backups; Downloads full of `.dmg` | | |

Two personas can both be true ("developer who dabbles in video"). Report the top one and, if the second is within a third of its score, the dabble.

**Signals to treat with care.** Many `.heic` means "has an iPhone", not photographer. Many `.pdf` means almost nothing. Chrome's presence means nothing. Photos library size is weak alone — every family has one — and strong only beside RAW files or a Lightroom catalog.

---

## What the persona changes

The persona is an input to the advisor. Each use is small and separate, so any one of them can ship alone.

1. **"Normal" in the library facts.** `GRADING.md` §9 wants "Photos: 48 GB. Normal for a family library." The persona supplies the noun: for a photographer, 400 GB is normal and the advice is about an external drive, not iCloud.
2. **Which chores apply.** `node_modules` and DerivedData are chores for a developer and noise for everyone else. Steam is a chore only if the games are not played (last-opened dates). Old `.dmg` files are a chore for everyone.
3. **Dad's remark.** One persona-specific line in the comment pool: "fourteen versions of node and you still can't decide." "a Lightroom catalog *and* a Photos library. pick a lane, kid." The pool is small today (see Feature Pool); personas multiply it without more thresholds.
4. **The LLM prompt's first sentence.** "I'm a web developer" before the system specs.
5. **The report's opening.** "Dad's guess: photographer, with a side of video. Wrong? Tell me." The correction is a click that sets a flag; see below.

---

## Privacy and tone rules

These are the constraints that make the feature safe for the audience in `README.md` — kids and non-technical adults. They are not optional.

- **On-device, always.** The guess is computed from the scan and written to the local manifest. It never leaves the Mac unless the user pastes the prompt somewhere themselves.
- **Occupations and hobbies only.** The table above is the whole allowed set. The tool never infers, stores or prints anything about health, religion, politics, sexuality, relationships, finances, or legal matters — not from apps, not from extensions, not from folder names. An app in those areas is simply not a signal.
- **Never guess age, and never label someone a child.** Minecraft and Roblox say "gamer". GarageBand says "musician". The audience includes kids; the tool must not sort them.
- **It is a guess, and it says so.** "Dad's guess" and "Am I close?" in the copy. The user can correct it (`--persona developer`, or a click in the report that stores the choice in `~/.dadware/`), and a stated persona always beats the guess.
- **Opt-out is one flag.** `--no-persona` skips the inference, the opening line and the prompt sentence, and the report reads as it does today.
- **Names and content are never read.** Extensions, app names, Dock entries, top-two-level folder names, sizes. Nothing else. This is the family helper's rule and it holds here.
- **Playful, never judgmental.** The persona explains why a big folder is fine. It is never used to say a person has too much of something.

---

## Build notes

- **Tally extensions in the walk.** One dict update per file in `scan_storage()`'s `_record_item()`: `{ext: (count, bytes)}`. Free, and it is also the "bytes by kind" metric under "Metrics worth adding".
- **Read the Dock.** `plistlib.load` on `com.apple.dock.plist`; each `persistent-apps` entry has `tile-data/file-data/_CFURLString`. Not TCC-protected. Wrap in the same "a blocked read is reported, never a zero" posture the Trash scanner uses.
- **The signal table is data.** A list of `(persona, weight, test)` tuples in one module, `scanners/persona.py`, with the tests as small named functions (`has_app('Figma')`, `ext_bytes_over('.cr2', 5 GB)`, `dock_has('Xcode')`). Weights and names live in the table so tuning is a table edit.
- **Test it with fixtures.** A fixture scan per persona (the `tests/fixtures/storage_scan.json` shape), and a test that every persona in the table is reachable with its strong signals alone — the same "every letter is reachable" guard `test_grading.py` uses.
- **Order of work:** extension tally → Dock read → `scanners/persona.py` → the library "normal" noun → the opening line → the prompt sentence. The first two are metrics on their own even if the persona never ships.
