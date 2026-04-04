# Project Workflow - Dad Ware

**Standard process for working with the project and documenting sessions**

---

## Session Workflow

### After Each Chat Session

1. **Create Session Summary**
   - File: `docs/sessions/YYYY-MM-DD-session-summary.md`
   - Template: See `docs/sessions/SESSION-SUMMARY-TEMPLATE.md`
   - Include:
     - What was accomplished
     - Bugs fixed
     - Features added
     - Files modified
     - Next steps

2. **Update Roadmap**
   - File: `docs/roadmap/PRIORITIZED-ROADMAP.md`
   - Update "Last Updated" date
   - Update status of completed items
   - Add new priorities if needed
   - Update "Next Action" section

3. **Update Bug Log** (if bugs fixed)
   - File: `docs/roadmap/BUG-LOG.md`
   - Mark bugs as fixed
   - Add resolution notes

4. **Commit Changes**
   - Commit code changes
   - Commit documentation updates
   - Use descriptive commit messages

---

## File Organization

### Directory Structure

```
dadware/
├── docs/
│   ├── sessions/              # Session summaries (one per chat)
│   │   ├── 2025-11-28-session-summary.md
│   │   ├── 2025-12-13-session-summary.md
│   │   └── SESSION-SUMMARY-TEMPLATE.md
│   ├── roadmap/               # Planning documents
│   │   ├── PRIORITIZED-ROADMAP.md  # Main roadmap (single source of truth)
│   │   ├── BUG-LOG.md
│   │   ├── FEATURE-ENHANCEMENTS.md
│   │   └── [other planning docs]
│   ├── bugs/                  # Bug investigation docs
│   ├── archive/               # Historical/completed docs
│   └── WORKFLOW.md            # This file
├── SESSION-SUMMARY.md         # ❌ REMOVED - use docs/sessions/ instead
└── [code files]
```

### Roadmap Organization

**Single Source of Truth:**
- `PRIORITIZED-ROADMAP.md` - Main roadmap, updated after each session

**Supporting Documents:**
- `BUG-LOG.md` - All bugs tracked
- `FEATURE-ENHANCEMENTS.md` - Small enhancements
- `TUI-DESIGN-DOCUMENT.md` - TUI design (active)
- `TUI-ARCHITECTURE.md` - TUI architecture (active)
- `TUI-PROTOTYPING-GUIDE.md` - TUI prototyping (active)

**Archive When Complete:**
- Move completed planning docs to `docs/archive/`
- Keep only active/current planning in `docs/roadmap/`

---

## Session Summary Template

See `docs/sessions/SESSION-SUMMARY-TEMPLATE.md` for the standard format.

---

## Roadmap Update Process

1. **Review completed work** from session summary
2. **Update status** of items in roadmap
3. **Add new priorities** if needed
4. **Update "Last Updated"** date
5. **Update "Next Action"** section
6. **Keep it concise** - roadmap should be actionable, not historical

---

## Best Practices

1. **One roadmap document** - `PRIORITIZED-ROADMAP.md` is the single source of truth
2. **Session summaries** - One per chat session, stored in `docs/sessions/`
3. **Keep roadmap current** - Update after each session
4. **Archive old docs** - Move completed planning to `docs/archive/`
5. **Commit regularly** - Commit after each session

---

**Last Updated:** December 13, 2025

