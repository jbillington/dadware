# UX Improvement Plan: Report Card Output

**Date:** November 2025  
**Status:** Planning  
**Owner:** John Billington

---

## Overview

This document outlines proposed user experience (UX) improvements for the `yourdad` application's HTML report card output. The goal is to enhance visual clarity, make size relationships more intuitive, and improve navigation through the file system hierarchy.

---

## 1. Storage Overview: Show Available Storage Percentage

### Current State
- Volume selection shows basic info (total, used, free) but not prominently
- No immediate visual feedback about storage health when scan starts
- Storage percentage not displayed at top of HTML report

### Proposed Improvement
Display **available storage percentage** prominently in both CLI and HTML report to give immediate context about disk health.

#### CLI Display (When Scan Starts)
- After volume selection, show storage overview before scanning begins
- Display format:
  ```
  Selected: /Users/john
  
  Storage Overview:
  _path": "/Users/john",
  - Total: 500 GB | 77% Used: 387 GB | 23% Free: 113 GB 
  - Available: 23% free
  ```
- Use color coding:
  - 🟢 Green: >20% free (healthy)
  - 🟡 Yellow: 10-20% free (warning)
  - 🔴 Red: <10% free (critical)

#### HTML Report Display (Top of Page)
- Add a **Storage Overview** section at the very top of the report (before personality comments)
- Display format:
  - Horizontal progress bar showing used vs free space
  - Large, prominent percentage display (e.g., "23% Free")
  - Color-coded based on available space
  - Total, Used, Free sizes in human-readable format
- Visual design:
  - Similar to macOS System Settings storage display
  - Progress bar with gradient (green → yellow → red)
  - Large percentage number as focal point

#### Technical Considerations
- Use `os.statvfs()` to get volume info (already available in `utils/volumes.py`)
- Display in CLI immediately after volume selection, before scanning starts
- Include in scan data structure for HTML report
- Calculate `free_percent = (free_bytes / total_bytes) * 100`

---

## 2. Top Folders: Horizontal Bar Chart with Expandable Details

### Current State
- Top folders are displayed in a table format with columns: Path, Size, Actions
- Size relationships are not immediately obvious
- Requires reading numbers to compare folder sizes
- No way to see folder contents without navigating away

### Proposed Improvement
Replace the tabular display with a **horizontal bar chart** where each folder is represented by a colored bar. Clicking a bar expands it inline to show subfolders and top files.

#### Visual Design

**Horizontal Bar Chart:**
- **Layout:** Vertical stack of horizontal bars, one per top folder
- **Bar Width:** Proportional to folder size (relative to total used disk space)
- **Color Coding:** Each top folder gets a distinct, accessible color
- **Bar Label:** Folder name and size displayed on or next to each bar
- **Top 10 Folders:** Each gets a unique color
- **"Other" Bar:** Combined size of remaining folders (gray, optional)

**Bar Structure:**
- **Bar Container:** Clickable area with hover state
- **Bar Fill:** Colored rectangle showing relative size
- **Bar Label:** Folder name and size (e.g., "Library - 29.4 GB")
- **Percentage:** Optional percentage of total disk space

#### Expandable Details (On Click)

When a folder bar is clicked, it expands inline to reveal:

**1. Subfolders Section:**
- List of top subfolders within the expanded folder
- Displayed as smaller horizontal bars or list items
- Each subfolder shows: name, size, and percentage of parent folder
- Indented to show hierarchy
- Clickable to expand further (nested expansion)

**2. Top 10 Largest Files:**
- Table or list showing the 10 largest files in this folder
- Columns: File name, size, modified date (optional)
- Sorted by size (largest first)
- Clickable file names to open in Finder

**3. "See All Files" Link:**
- Appears below the top 10 files
- Two implementation options:
  - **Option A (Inline):** Clicking expands to show all files in the same view
  - **Option B (Separate Page):** Clicking navigates to a dedicated folder index page
- Styled as a link (e.g., "View all 247 files in Library →")

**Visual States:**
- **Collapsed:** Just the bar with label
- **Expanded:** Bar + subfolders + top 10 files + "see all" link
- **Hover:** Bar highlights, cursor changes to pointer
- **Active/Selected:** Expanded bar has visual indicator (border, background, or icon)

#### Interactions

**Hover:**
- On bar: Highlight bar, show tooltip with:
  - Full folder path
  - Exact size (e.g., "28.5 GB")
  - Percentage of total disk space
  - Number of files/subfolders (optional)

**Click:**
- **Bar:** Toggle expand/collapse of folder details
- **Subfolder:** Expand that subfolder's details (nested expansion)
- **File name:** Open file in Finder (current behavior)
- **"See All Files" link:** 
  - Option A: Expand to show all files inline
  - Option B: Navigate to folder index page

**Keyboard:**
- Enter/Space on focused bar: Toggle expand/collapse
- Escape: Collapse all expanded folders

#### Technical Considerations
- Use HTML/CSS for bar rendering (flexbox or grid layout)
- Calculate bar widths as percentage of largest folder or total disk space
- Implement JavaScript for expand/collapse functionality
- Store folder hierarchy and file listings in scan data structure
- Support nested expansion (subfolders can expand within expanded parent)
- Color palette: Use distinct, accessible colors for top 10 folders
- Smooth animation for expand/collapse transitions
- Only one folder expanded at a time, or allow multiple? (Decision needed)

---

## 3. Top Files: Show Folder Name with Link

### Current State
- Files are listed with just their filename
- Full path is in the link, but not visible
- Users can't easily see which folder a file is in
- No way to navigate to the folder from the file list

### Proposed Improvement
Display the **parent folder name** underneath each file name, and make it a clickable link to the folder's index view.

#### Visual Design
- **File Name:** Displayed as primary text (larger, bold)
- **Folder Name:** Displayed below file name (smaller, lighter color, italic or regular)
- **Folder Link:** Clickable, styled as a link (blue, underlined on hover)
- **Layout:** Two-line layout per file row

#### Example Layout
```
OmarHakimDrums2_96kHz_Multi_Pt1.zip
  📁 in Downloads
```

#### Interactions
- **Click folder name:** Navigate to Folder Index View (see section 4)
- **Click file name:** Opens file:// link (current behavior)
- **Hover folder name:** Show tooltip with full folder path

#### Technical Considerations
- Extract parent folder from file path
- Store folder paths in scan data structure
- Implement click handler for folder navigation
- Style folder name as secondary text

---

## 4. Folder Index View (Optional - For "See All Files")

### Overview
A dedicated view that shows **all** files and subfolders within a specific folder, sorted by size. This view is only needed if implementing "Option B" for the "See All Files" link (separate page navigation).

### When It Appears
- Clicking "See All Files" link in expanded folder details (Option B only)
- Alternative to inline expansion of all files (Option A doesn't need this view)

### Visual Design
- **Header:** "All Files in [Folder Name]" with breadcrumb navigation
- **Back Button:** Return to main report card
- **Table:** Similar to Top Files table, showing:
  - File/Folder name
  - Size
  - Modified date (optional)
  - Actions (Reveal in Finder)
- **Sorting:** By default, sorted by size (largest first)
- **Subfolders:** Displayed with folder icon, clickable to drill down further
- **Pagination:** For folders with many files (e.g., 50-100 per page)

### Data Requirements
- Need to scan and store file listings for each folder
- Could be done on-demand (scan when clicked) or pre-scanned
- For POC: Pre-scan top 10 folders during initial scan
- For "See All": May need to scan on-demand if folder has many files

### Technical Considerations
- Store folder contents in scan data structure
- Implement JavaScript routing/navigation between views (if Option B)
- Use client-side filtering/display (no server needed)
- Consider pagination for folders with many files
- **Note:** If Option A (inline expansion) is chosen, this view may not be needed

---

## 5. Overall Visual Polish

### Current State
- Functional but basic design
- Could benefit from more visual hierarchy
- Colors and spacing could be refined

### Proposed Improvements

#### Typography
- [ ] Review font sizes and weights
- [ ] Improve line spacing for readability
- [ ] Consider font pairing (headers vs body)

#### Color Palette
- [ ] Refine color scheme to match "dadware" brand
- [ ] Ensure sufficient contrast for accessibility
- [ ] Use color to indicate status (warn, critical, ok)

#### Spacing & Layout
- [ ] Increase padding/margins for breathing room
- [ ] Improve alignment and visual hierarchy
- [ ] Consider responsive design for different screen sizes

#### Interactive Elements
- [ ] Add hover states for all clickable elements
- [ ] Improve button styling and feedback
- [ ] Add loading states for folder navigation

---

## Implementation Priority

### Phase 1: High Priority (Core UX)
1. **Storage Overview** - Show % available in CLI and HTML report ⭐ NEW
2. **Top Folders Horizontal Bar Chart** - Visual size representation with colored bars
3. **Expandable Folder Details** - Click to show subfolders and top 10 files
4. **"See All Files" Link** - Expand to show all files (inline or separate page)

### Phase 2: Medium Priority (Enhanced Navigation)
5. **Nested Subfolder Expansion** - Expand subfolders within expanded folders
6. **Folder Name in Top Files** - Context and navigation (if still needed)
7. **Folder Index View** - Separate page for "See All" (if Option B chosen)

### Phase 3: Low Priority (Polish)
8. **Visual Polish** - Typography, colors, spacing
9. **Responsive Design** - Mobile/tablet support

---

## Open Questions

1. **Bar Chart Scale:** Should bars be relative to largest folder, or to total disk space?
2. **Folder Index Data:** Pre-scan all folders, or scan on-demand when clicked?
3. **"See All Files" Implementation:** Option A (inline expansion) or Option B (separate page)?
4. **Multiple Expansion:** Allow multiple folders expanded at once, or only one at a time?
5. **"Other" Bar Calculation:** How to calculate size of "other" folders efficiently?
6. **Storage Display:** Show all mounted volumes in overview, or just the scanned one?
7. **Subfolder Expansion Depth:** How many levels deep should nested expansion go?

---

## Next Steps

1. **Review & Discuss** - Go through this plan and refine requirements
2. **Decide on "See All Files"** - Choose Option A (inline) or Option B (separate page)
3. **Mockups** - Create visual mockups for horizontal bar chart and expandable details
4. **Data Structure** - Design scan data structure to support folder contents and file listings
5. **Implementation** - Start with Phase 1 features (bar chart + expandable details)
6. **Testing** - Test with real data and user feedback

---

**Last Updated:** November 2025 (Refined with horizontal bar chart approach)  
**Next Review:** After discussion and feedback
