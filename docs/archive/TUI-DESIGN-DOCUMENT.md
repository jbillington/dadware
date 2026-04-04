# TUI Design Document - Dad Ware

**Version:** 2.0  
**Date:** December 2025  
**Status:** Design Phase

---

## Executive Summary

This document outlines the design approach for converting the current simple menu (`yourdad`) into a full-screen Text User Interface (TUI) application. The TUI will provide a more polished, interactive experience while maintaining the personality-driven approach that makes Dad Ware unique.

---

## Current State & Goals

### Current Menu Limitations
- No keyboard navigation (must type numbers)
- No progress feedback during scans
- No way to view previous reports
- Limited interactivity

### TUI Goals
- Keyboard-first navigation
- Real-time progress during scans
- Report viewing within TUI
- Settings/configuration
- Beautiful layouts with colors and formatting
- Modal dialogs for confirmations

---

## Design Principles

1. **Keyboard-first** - No mouse required, all navigation via keyboard
2. **Personality-preserving** - Keep the dad-style commentary and humor
3. **Information-dense** - Show more info without clutter
4. **Progressive disclosure** - Start simple, reveal details on demand
5. **Follow terminal conventions** - Use common patterns from htop, ranger, ncdu, etc.

---

## State Machine

### Core States

```
SPLASH (optional)
  ↓
MENU (main menu)
  ├─[1]─► SCAN_CPU ──► SCAN_PROGRESS ──► REPORT_VIEW
  ├─[2]─► SCAN_STORAGE ──► SCAN_PROGRESS ──► REPORT_VIEW
  ├─[3]─► SCAN_ALL ──► SCAN_PROGRESS ──► REPORT_VIEW
  ├─[4]─► VIEW_REPORTS ──► REPORT_LIST ──► REPORT_VIEW
  ├─[5]─► SETTINGS ──► SETTINGS_PANEL
  ├─[?]─► HELP_MODAL (overlay)
  └─[Q]─► EXIT
```

### State Transitions

| From State | Action | To State |
|------------|--------|----------|
| MENU | Press `1-5` or navigate | SCAN_* / VIEW_REPORTS / SETTINGS |
| MENU | Press `?` | HELP_MODAL (overlay) |
| MENU | Press `Q` | EXIT |
| SCAN_* | Scan starts | SCAN_PROGRESS |
| SCAN_PROGRESS | Scan completes | REPORT_VIEW |
| SCAN_PROGRESS | Press `Esc` | MENU (cancel) |
| REPORT_VIEW | Press `Esc` | MENU |
| REPORT_VIEW | Press `O` | Open in browser |
| HELP_MODAL | Press `Esc` | Previous state |

---

## Keybindings (Following Terminal Conventions)

### Global Keybindings
- `?` - Show/hide help overlay
- `Q` - Quit application (with confirmation)
- `Esc` - Go back / Close modal / Cancel
- `Ctrl+C` - Force quit

### Navigation (Standard Terminal Patterns)
- `↑` / `↓` - Navigate items (like htop, ranger)
- `Enter` - Select/activate
- `Tab` - Toggle between panels/sections
- `1-9` - Direct selection (number keys)

### Context-Specific
- Report View: `O` (open in browser), `E` (export), `←` / `→` (navigate reports)
- Scan Progress: `Esc` (cancel), `P` (pause, if supported)

**Reference:** Study keybindings from htop, ranger, ncdu, btop for consistency.

---

## Layout Design Options

### Layout Patterns to Consider

#### 1. Single-Panel Layout
**Structure:**
- Header (fixed)
- Content area (scrollable)
- Footer (fixed)

**Pros:**
- Maximum content space
- Simple to implement
- Familiar (like htop, btop)

**Cons:**
- Navigation hidden in menus
- Less information visible at once

**Use when:** Focus is on content, minimal navigation needed

---

#### 2. Two-Panel Layout
**Structure:**
- Header (fixed)
- Navigation panel (left, 20-30% width)
- Content panel (right, 70-80% width)
- Footer (fixed)

**Pros:**
- Always visible navigation
- More information density
- Clear separation of concerns

**Cons:**
- Less space for content
- More complex layout

**Use when:** Navigation is important, multiple sections to access

---

#### 3. Tab-Based Layout
**Structure:**
- Header with tabs
- Content area (changes based on active tab)
- Footer

**Pros:**
- Clear section organization
- Easy to switch between views
- Familiar pattern

**Cons:**
- Limited to flat navigation
- Tabs take header space

**Use when:** Distinct sections (Menu, Reports, Settings)

---

#### 4. Modal/Overlay Pattern
**Structure:**
- Base screen (menu/content)
- Overlay modal for help/settings/confirmations

**Pros:**
- Doesn't lose context
- Quick to dismiss
- Focused interaction

**Cons:**
- Smaller space for modal content
- Can feel cramped

**Use when:** Help, confirmations, quick settings

---

### Layout Components to Design

**Header:**
- App name, version, build
- User context (greeting, last scan time)
- Optional: status indicators

**Navigation:**
- Menu items (list or buttons)
- Recent activity
- Status indicators

**Content Area:**
- Menu options
- Scan progress
- Report data
- Settings panels

**Footer:**
- Keybinding hints
- Status messages
- Optional: input prompt

---

## Design Decisions to Make

### 1. Navigation Pattern
- **Option A:** Single-panel with menu list (like htop)
- **Option B:** Two-panel with sidebar navigation (like ranger)
- **Option C:** Tab-based navigation (like many CLI tools)
- **Consider:** What feels most natural for the workflow?

### 2. Menu Display
- **Option A:** Simple list with arrow keys (like htop)
- **Option B:** Buttons with visual emphasis (like Textual examples)
- **Option C:** Command palette style (type to filter)
- **Consider:** How do users typically interact with terminal menus?

### 3. Progress Display
- **Option A:** Full-screen progress (focus on scan)
- **Option B:** Progress in footer (can still see menu)
- **Option C:** Progress overlay (non-blocking)
- **Consider:** Do users need to do other things during scan?

### 4. Report Viewing
- **Option A:** Inline in TUI (full terminal experience)
- **Option B:** Summary in TUI, full report in browser
- **Option C:** Always open browser (TUI just triggers)
- **Consider:** What's the primary use case?

### 5. Help System
- **Option A:** Modal overlay (press `?`)
- **Option B:** Full-screen help (separate screen)
- **Option C:** Contextual hints in footer
- **Consider:** How much help is needed?

---

## Visual Design System

### Colors
- **Primary:** Blue/Cyan for headers
- **Success:** Green for positive states
- **Warning:** Yellow/Orange for cautions
- **Error:** Red for errors
- **Text:** Default terminal color
- **Dimmed:** Gray for hints/secondary info

### Typography
- Monospace font (terminal default)
- Bold for headers
- Dimmed for hints/footers

### Borders & Boxes
- Use framework's border system (Textual provides this)
- Consistent border style throughout
- Panels for grouping content

---

## Technical Architecture

### File Structure
```
tui/
├── app.py              # Main TUI application
├── screens/            # Screen components
│   ├── menu.py
│   ├── scan_progress.py
│   ├── report_view.py
│   └── settings.py
├── widgets/            # Reusable widgets
│   ├── header.py
│   ├── footer.py
│   └── progress.py
└── utils/
    ├── state_manager.py
    └── keybindings.py
```

### Integration Points
- `scanners/` - Call scan functions, get progress callbacks
- `renderers/terminal.py` - Reuse formatting functions
- `personality/yourdad.py` - Get personality comments
- `utils/` - Reuse utility functions

---

## Success Criteria

### Must Have
- ✅ All current menu features work
- ✅ Keyboard navigation smooth
- ✅ Progress feedback during scans
- ✅ Can view reports in TUI
- ✅ Help accessible via `?`

### Nice to Have
- Recent activity tracking
- Settings/configuration
- Report history browsing
- Export functionality

---

## Resources

### Documentation
- **Textual Docs:** https://textual.textualize.io/
- **Rich Docs:** https://rich.readthedocs.io/

### Examples to Study
- **htop** - Process viewer (navigation, filtering)
- **ranger** - File manager (keyboard navigation, two-panel)
- **ncdu** - Disk usage (progress, navigation)
- **btop** - System monitor (progress, real-time updates)

---

## Appendix: Understanding Textual Framework

### What is Textual?

Textual is a Python framework for building Terminal User Interfaces (TUIs). It's built on Rich (for rendering) and provides a full-screen, widget-based system similar to web frameworks.

### Core Concepts

#### 1. App and Screens

**App** - The main application container:
```python
from textual.app import App

class DadWareApp(App):
    def compose(self):
        yield Header()
        yield Footer()
        # ... widgets
```

**Screens** - Separate views that can be pushed/popped:
```python
from textual.screen import Screen

class MenuScreen(Screen):
    def compose(self):
        yield Button("Scan")
```

**Screen Stack:**
- App maintains a stack of screens
- `push_screen()` - Add new screen on top
- `pop_screen()` - Remove current screen
- Similar to navigation in web apps

---

#### 2. Widgets and Composition

**Widgets** - Reusable UI components:
- `Button`, `Static`, `Input`, `ProgressBar`, etc.
- Each widget is a class that can be styled and positioned

**Composition** - Building UI from widgets:
```python
def compose(self):
    yield Header()           # Widget
    yield Container(         # Container widget
        Button("Scan"),      # Nested widget
        Button("Reports")
    )
    yield Footer()           # Widget
```

**Key Point:** Widgets are separate from content - you define structure, then populate with data.

---

#### 3. CSS-Like Styling

**Separation of Style and Content:**

Textual uses CSS-like styling that separates presentation from structure:

```python
class DadWareApp(App):
    CSS = """
    Button {
        width: 100%;
        margin: 1;
        background: $primary;
    }
    
    #menu-container {
        width: 60%;
        margin: 2 auto;
    }
    """
```

**How it works:**
- CSS is defined separately from widget composition
- Styles apply to widgets by type, ID, or class
- Similar to web CSS - style rules are separate from HTML structure

**Example:**
```python
# Structure (compose method)
def compose(self):
    yield Container(id="menu-container")
    yield Button("Scan", classes="primary")

# Style (CSS property)
CSS = """
#menu-container {
    width: 60%;
}

.primary {
    background: $primary;
}
```

**This is like HTML/CSS:**
- `compose()` = HTML structure
- `CSS` = CSS styling
- Content is separate from both

---

#### 4. Layout System

**Containers** - Layout widgets that arrange children:

**Horizontal** - Side-by-side:
```python
yield Horizontal(
    Button("Left"),
    Button("Right")
)
```

**Vertical** - Stacked:
```python
yield Vertical(
    Button("Top"),
    Button("Bottom")
)
```

**Grid** - Grid layout:
```python
yield Grid(
    Button("1"), Button("2"),
    Button("3"), Button("4")
)
```

**Key Point:** Layout is separate from content - containers define arrangement, widgets provide content.

---

#### 5. Event System

**Events** - User interactions trigger events:

```python
def on_button_pressed(self, event: Button.Pressed):
    # Handle button press
    pass

def on_key(self, event: Key):
    # Handle keyboard input
    pass
```

**Event Flow:**
- User action → Event → Handler method
- Events bubble up widget tree
- Handlers can stop propagation

---

#### 6. State Management

**Widget State:**
- Each widget can have internal state
- State changes trigger re-renders
- Similar to React components

**App State:**
- App can maintain global state
- Passed to screens/widgets as needed
- Can use dataclasses or simple dicts

**Example:**
```python
class MenuScreen(Screen):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
```

---

### Does Textual Abstract Layout from Content?

**Yes, similar to CSS/HTML:**

#### 1. **Structure vs. Style**
- **Structure:** `compose()` method defines widget hierarchy (like HTML)
- **Style:** `CSS` property defines appearance (like CSS)
- **Content:** Data passed to widgets separately

#### 2. **Layout vs. Content**
- **Layout:** Containers (Horizontal, Vertical, Grid) define arrangement
- **Content:** Widgets (Button, Static, etc.) provide actual content
- **Separation:** You can change layout without changing content widgets

#### 3. **Navigation vs. Content**
- **Navigation:** Screen stack and navigation logic separate
- **Content:** Each screen defines its own content
- **Abstraction:** Navigation structure separate from screen content

#### 4. **Widgets as Components**
- Widgets are reusable components
- Style and behavior defined in widget class
- Content passed in when used
- Similar to React components or web components

---

### Textual Architecture Summary

**Layers of Abstraction:**

1. **App Layer** - Main application, screen management
2. **Screen Layer** - Individual views/screens
3. **Widget Layer** - Reusable UI components
4. **Layout Layer** - Containers that arrange widgets
5. **Style Layer** - CSS that styles widgets
6. **Content Layer** - Data that populates widgets

**Key Insight:**
Textual provides separation similar to web development:
- **HTML** → `compose()` method (structure)
- **CSS** → `CSS` property (styling)
- **JavaScript** → Event handlers (behavior)
- **Data** → Passed separately (content)

**This means:**
- You can change layout without changing content
- You can change styling without changing structure
- You can change content without changing layout
- Navigation is abstracted from screen content

---

### Practical Example

**Structure (compose):**
```python
def compose(self):
    yield Container(id="main"):
        yield Horizontal(
            Container(id="nav"):
                yield Button("Menu"),
                yield Button("Reports"),
            Container(id="content"):
                yield Static("Content here")
        )
```

**Style (CSS):**
```python
CSS = """
#main {
    width: 100%;
    height: 100%;
}

#nav {
    width: 30%;
    border: solid $primary;
}

#content {
    width: 70%;
}
"""
```

**Content (data):**
```python
def on_mount(self):
    # Populate with actual data
    content_widget = self.query_one("#content Static")
    content_widget.update("Actual report data here")
```

**Navigation (separate):**
```python
def on_button_pressed(self, event):
    if event.button.id == "reports":
        self.app.push_screen(ReportScreen())
```

**Result:**
- Layout defined in `compose()`
- Styling defined in `CSS`
- Content populated separately
- Navigation handled separately

**This is the same separation as HTML/CSS/JS!**

---

### Key Takeaways

1. **Textual abstracts layout from content** - Yes, similar to CSS/HTML
2. **Widgets are components** - Reusable, styled separately
3. **CSS-like styling** - Separate style from structure
4. **Screen-based navigation** - Navigation separate from content
5. **Event-driven** - Behavior separate from presentation

**For Dad Ware:**
- Define layout structure in `compose()`
- Style with CSS
- Populate content from data
- Handle navigation separately
- Reuse widgets across screens

---

**Status:** Ready for design exploration and prototyping  
**Next Action:** Explore layout options, create mockups, then build prototype
