# Dad Ware / `yourdad` — Product Roadmap

**Vision:** A personality-driven Mac cleanup tool that makes system maintenance fun and approachable

---

## Overview

This roadmap shows the evolution from POC → MVP → v1.0, organized by version with effort estimates.

**Current Status:** 🚧 POC in progress (Core features implemented)

---

## Release Timeline

1. **POC** (15 hours)
   - Validate architecture, personality, and HTML reports
   - Core storage + CPU scans
   - Basic dad personality

2. **v0.1** (2-3 weeks)
   - Polish POC into production-ready version
   - Better UX, error handling, progress feedback
   - More personality rules

3. **v0.2** (2-3 weeks)
   - Duplicate file detection
   - Review workspace (symlink staging)
   - Bulk action support

4. **v0.3** (3-4 weeks)
   - Full-screen TUI (text user interface)
   - Menu system with keyboard navigation
   - Settings menu

5. **v0.4** (1-2 weeks)
   - Progress animations and feedback
   - Real-time status messages
   - Keyboard shortcuts

6. **v0.5** (2-3 weeks)
   - Additional scans (battery, network, login items)
   - Comprehensive system reports

7. **v1.0** (2-3 weeks)
   - Multiple personalities
   - Distribution (Homebrew, binary)
   - Auto-updates and final polish

---

## POC (Proof of Concept)

**Timeline:** 15 hours (4-5 coding sessions)
**Status:** 🚧 In progress (~80% complete)
**Goal:** Validate core concept - architecture, personality, HTML reports

### Features
- ✅ `yourdad scan storage` - volume selection + storage scan
- ✅ `yourdad scan cpu` - CPU/RAM snapshot
- ✅ `yourdad scan quick` - combined scan
- ✅ Terminal report with dad personality
- ✅ HTML report with sortable tables, file:// links
- ✅ Smart exclusions (system folders, app bundles)
- ✅ Basic dad comments (5-10 rules)
- ✅ **Report card grading system** - Letter grades (A-F) for storage health
- ✅ **Mac app library scanning** - Photos, Music, Messages, Mail, Time Machine, Creative apps
- ✅ **Permission detection** - Automatic permission checking with user guidance
- ✅ **Enhanced HTML reports** - Two-bar folder visualization, expandable details
- ✅ **Test reports directory** - Development-friendly report location
- 🔜 More dad comments (expand to 15-20 rules)

### Success Criteria
- Dad comments make people smile (not cringe)
- HTML report is useful for finding large files
- Scan completes in <30 seconds
- 3+ non-technical people understand it

**Detailed plan:** See `poc-plan.md`

---

## v0.1 (Polish & Production-Ready)

**Timeline:** 2-3 weeks after POC
**Status:** 📋 Not started
**Goal:** Production-ready version with polish and better UX

### Features
- ✅ Progress feedback during scans (status messages, counts)
- 🔜 More dad comments (15-20 rules, data-aware) - *In progress*
- ✅ Better error handling and messages
- ✅ Filter options (`--min-size`, `--depth`)
- 🔜 Report history management
- ✅ `--no-color` flag for terminal
- 🔜 Basic test coverage
- ✅ Installation script / package
- ✅ README with examples
- ✅ Permission detection and guidance
- ✅ Mac app library scanning
- ✅ Report card grading system

### Nice to Have
- 🔜 Config file for defaults (~/.dadware/config.json)
- 🔜 Auto-open HTML report (configurable)
- 🔜 JSON export format

---

## v0.2 (Duplicates & Review Workspace)

**Timeline:** 2-3 weeks after v0.1
**Status:** 📋 Not started
**Goal:** Add duplicate detection and make it easy for users to take action

### Features
- ✅ `yourdad scan dupes` - duplicate file detection
- ✅ Review workspace (symlink staging for safe inspection)
- ✅ Bulk action support (move to review, trash script generation)
- ✅ Enhanced HTML report (duplicates tab)
- ✅ Keep/delete recommendations for dupes

### Detailed Specs
- **Duplicate detection:** See `roadmap/duplicates-prd.md` (to be created from design.md)
- **Review workspace:** See `roadmap/review-workspace-prd.md`

**Key Capabilities:**
1. Hash-based duplicate detection (size → partial hash → full SHA-256)
2. Symlink review workspace for safe inspection in Finder
3. "Keep one, review others" workflow
4. Generate trash scripts user can run explicitly
5. HTML report with duplicates tab (sortable by size, group)

---

## v0.3 (Full-Screen TUI)

**Timeline:** 3-4 weeks after v0.2
**Status:** 📋 Not started
**Goal:** Add menu-driven interface with keyboard navigation

### Features
- ✅ Full-screen TUI (text user interface)
- ✅ Menu system (choose scan type from menu)
- ✅ Keyboard shortcuts (?, Tab, Esc, arrows)
- ✅ Recent activity panel
- ✅ "What's new" section
- ✅ Settings menu (personality, depth, export format)

### Detailed Specs
- See `roadmap/text-ui-prd.md`

**Key Capabilities:**
1. Launch screen with branded ASCII art
2. Menu-driven workflow (1. Storage, 2. CPU, 3. Duplicates, 4. Quick, 5. Settings)
3. Keyboard shortcuts for power users
4. Session history (last 5 commands)
5. Visual feedback (status line updates during scan)

**Tech Stack:** Python Textual (or Go Bubble Tea)

---

## v0.4 (Animations & Feedback)

**Timeline:** 1-2 weeks after v0.3
**Status:** 📋 Not started
**Goal:** Polish UX with animations and better progress feedback

### Features
- ✅ Progress animations (spinner, pulse, phase cards)
- ✅ Real-time status messages during scan
- ✅ Dad comments during scan phases (not just at end)
- ✅ Keyboard shortcuts (Esc to cancel, ? for help)
- ✅ Graceful cancellation (partial results)

### Detailed Specs
- See `roadmap/animations-prd.md`

**Key Capabilities:**
1. Phase-based animations (Init → Scan → Analyze → Report)
2. Data-aware status lines ("found Downloads folder... yep, it's a mess")
3. Truthy progress (counts, not fake percentages)
4. Keyboard controls (Esc, Ctrl+C, ?)
5. Personality-driven feedback throughout

---

## v0.5 (Additional Scans)

**Timeline:** 2-3 weeks after v0.4
**Status:** 📋 Not started
**Goal:** Expand scanning capabilities beyond storage and CPU

### Features
- ✅ `yourdad scan battery` - battery health and cycle count
- ✅ `yourdad scan network` - network diagnostics (Wi-Fi quality, speed)
- ✅ `yourdad scan login` - login items management
- ✅ `yourdad scan all` - comprehensive system report

### Detailed Specs
- **Battery:** Cycle count, condition, capacity, charging patterns
- **Network:** Wi-Fi signal strength, connected network, speed test
- **Login items:** Auto-start applications, launch agents, daemons

**Implementation:**
- Each scan is a new module in `scanners/`
- Follows standard scan result format
- Gets own personality comments
- Integrates with existing reports

---

## v1.0 (Multiple Personalities & Polish)

**Timeline:** 2-3 weeks after v0.5
**Status:** 📋 Not started
**Goal:** Ship 1.0 with multiple personalities and final polish

### Features
- ✅ Multiple personalities (Dad, Mr. B, Zen, Sarge, Spicoli)
- ✅ Personality picker in settings
- ✅ Themes (light/dark mode)
- ✅ Distribution (Homebrew formula, standalone binary)
- ✅ Auto-update mechanism
- ✅ Comprehensive documentation
- ✅ Video demos / screenshots

### Personality Options
1. **Your Dad** (default) - dry, witty, helpful
2. **Mr. B** - professional, concise, no-nonsense
3. **Zen Master** - calm, philosophical, mindful
4. **Drill Sergeant** - intense, motivational, urgent
5. **Spicoli** - laid-back, surfer dude, chill

**Distribution:**
- Homebrew: `brew install yourdad`
- Standalone binary (Python → PyInstaller)
- GitHub releases with auto-update

---

## Future (Post-v1.0)

**Ideas to explore after 1.0 ships:**

### Integration & Automation
- [ ] Scheduled scans (cron jobs, launch agents)
- [ ] Slack/Discord notifications
- [ ] Email reports (optional)
- [ ] Alfred/Raycast integration

### Advanced Features
- [ ] APFS clone detection (storage-efficient dupes)
- [ ] Incremental scans (cache previous results)
- [ ] Google Drive / iCloud cleanup
- [ ] Gmail attachment analysis
- [ ] Visual folder size treemap (HTML)
- [ ] Photo library analysis (Photos.app integration)

### Platform Expansion
- [ ] Windows port (NTFS, different system paths)
- [ ] Linux support (various distros)
- [ ] Cloud VM support (AWS, GCP instances)

### AI-Powered Features
- [ ] LLM advisor mode (optional, BYO API key)
- [ ] Intelligent cleanup suggestions
- [ ] Natural language queries ("show me videos over 1GB")
- [ ] Voice interface (VAPI integration)

---

## Feature Dependencies

Some features build on others. Here's the dependency tree:

```
POC (foundation)
  ↓
v0.1 (polish)
  ↓
v0.2 (dupes & review workspace) ← depends on v0.1 storage scan
  ↓
v0.3 (TUI) ← can work with any previous version
  ↓
v0.4 (animations) ← depends on v0.3 TUI
  ↓
v0.5 (more scans) ← parallel to v0.3/v0.4, can be done anytime
  ↓
v1.0 (personalities) ← depends on stable core
```

---

## Prioritization Framework

**Must Have (MVP):**
- Storage scan with large files
- Terminal + HTML reports
- Dad personality
- Read-only safety

**Should Have (v0.1-v0.2):**
- CPU scan
- Duplicate detection
- Review workspace
- Better UX polish

**Could Have (v0.3-v0.5):**
- Full TUI
- Animations
- Additional scans
- More polish

**Nice to Have (v1.0+):**
- Multiple personalities
- Distribution via Homebrew
- Auto-updates
- Themes

**Dream Features (Future):**
- AI advisor
- Platform expansion
- Cloud integration
- Visual treemaps

---

## Effort Summary

| Version | Features | Estimated Effort | Cumulative |
|---------|----------|------------------|------------|
| POC | Core validation | 15 hours | 15 hrs |
| v0.1 | Polish & production | 2-3 weeks | ~100 hrs |
| v0.2 | Dupes & review | 2-3 weeks | ~200 hrs |
| v0.3 | Full TUI | 3-4 weeks | ~350 hrs |
| v0.4 | Animations | 1-2 weeks | ~400 hrs |
| v0.5 | More scans | 2-3 weeks | ~500 hrs |
| v1.0 | Final polish | 2-3 weeks | ~600 hrs |

**Total to v1.0:** ~600 hours (15 weeks full-time, or 6 months part-time)

---

## Success Metrics by Version

### POC
- Personality validation (5+ people give positive feedback)
- HTML report is useful
- Scan completes in <30s

### v0.1
- 10+ daily active users
- Zero accidental deletions reported
- Average 5GB+ freed per scan

### v0.2
- 50+ users adopt duplicate detection
- Review workspace used by 80%+ of users
- Positive feedback on safe deletion workflow

### v1.0
- 500+ installs
- Featured in Mac productivity blogs
- 4+ star rating (if distributed via app store)
- Active community contributions

---

## Risk Mitigation

| Risk | Impact | Mitigation | When |
|------|--------|------------|------|
| Personality doesn't land | HIGH | Test early with real users, iterate | POC Phase 4 |
| Performance too slow | HIGH | Set timeouts, optimize scanner | POC Phase 2 |
| Users accidentally delete important files | CRITICAL | Read-only by design, review workspace | v0.2 |
| Scope creep delays launch | MEDIUM | Stick to version plans, defer features | All phases |
| Competition launches similar tool | MEDIUM | Move fast, ship POC quickly | POC |

---

## Decision Points

### After POC
- **Go/No-Go:** Does the personality work? Is it worth continuing?
- **Architecture:** Can we easily add new scans?
- **Performance:** Is <30s achievable?

### After v0.1
- **Distribution:** How to package and distribute?
- **Monetization:** Free forever? Donation model? Premium features?
- **Community:** Open source now or later?

### After v0.2
- **Platform:** Stick to Mac or expand?
- **Features:** Which v0.3+ features are most requested?

---

## Roadmap Files

**Detailed specs for future versions:**
- `roadmap/review-workspace-prd.md` - Symlink staging for safe deletion
- `roadmap/text-ui-prd.md` - Full-screen TUI design
- `roadmap/animations-prd.md` - Progress animations and feedback
- `roadmap/space-wasters-features.md` - Inspiration from DaisyDisk

---

**Last Updated:** November 9, 2025
**Next Review:** After POC completion

## Recent Updates (November 2025)

### Completed Features
- ✅ **Report Card System**: Comprehensive grading system with letter grades (A-F) for storage health
  - Free space grading
  - Home folders ratio grading
  - Home folders clutter grading (Downloads, Desktop)
  - Individual Mac app library grades (Photos, Music, Messages, Mail, Time Machine, Creative apps)
  - Composite overall grade with weighted scoring
- ✅ **Mac App Library Scanning**: Scans Photos, Music, Messages, Mail, Time Machine backups, and creative app libraries
- ✅ **Permission Detection & Guidance**: Automatic permission checking with clear user instructions
  - Permission detection module (`utils/permissions.py`)
  - Standalone permission checker script
  - Permission warnings in terminal and HTML reports
  - `--skip-protected` flag to skip protected directories
- ✅ **Enhanced HTML Reports**: 
  - Two-bar folder visualization (Home Folders vs Other Folders)
  - Expandable folder details with top files
  - Report card display with grade breakdown
  - Permission warning sections
- ✅ **Test Reports Directory**: Development-friendly report location with auto-detection
- ✅ **Distribution Infrastructure**: 
  - Homebrew formula
  - Installation script
  - Distribution documentation
  - Swift helper framework (for future Mac app)

### In Progress
- 🔜 Expanding dad personality comments (5-10 rules → 15-20 rules)
- 🔜 Report history management
- 🔜 Basic test coverage
