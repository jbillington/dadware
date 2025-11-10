# Report Card Design: Simplified Storage Grading System

## Core Concept
Transform the storage report into a **graded report card** with actionable advice. Focus on storage management with clear metrics and prioritized action items.

---

## 1. Key Metrics (Display at Top)

### Storage Metrics Section
```
┌─────────────────────────────────────────────┐
│ 📊 STORAGE METRICS                          │
│                                             │
│ Top 10 Folders Total:  245.3 GB            │
│ Top 25 Files Total:     87.2 GB            │
│ Reclaimable:            12.5% of used space │
│                                             │
│ "You can free up 12.5% by deleting or      │
│  offloading your top 25 largest files"     │
└─────────────────────────────────────────────┘
```

**Calculations:**
- `sum_top_10_folders` = Sum of sizes of top 10 largest folders
- `sum_top_25_files` = Sum of sizes of top 25 largest files  
- `reclaimable_percent` = `(sum_top_25_files / used_bytes) * 100`

This metric shows the **percentage of used space that could be freed** by deleting/offloading the top 25 files.

---

## 2. Storage Grading System (Simplified)

### Component Grades

Storage is graded on **4 separate components**, then combined into a composite grade:

#### 1. Free Space Grade
**Based on:** Percentage of free space on volume

- **A (90-100):** >30% free
- **B (80-89):** 20-30% free
- **C (70-79):** 10-20% free
- **D (60-69):** 5-10% free
- **F (<60):** <5% free

**Calculation:**
```python
if free_percent >= 30: score = 100
elif free_percent >= 20: score = 80 + (free_percent - 20) * 2
elif free_percent >= 10: score = 60 + (free_percent - 10) * 2
elif free_percent >= 5: score = 40 + (free_percent - 5) * 4
else: score = free_percent * 8
```

#### 2. Home Folders Ratio Grade
**Based on:** Ratio of home folder usage to total used storage

- **A (90-100):** <30% of used space is in home folders
- **B (80-89):** 30-50% of used space is in home folders
- **C (70-79):** 50-70% of used space is in home folders
- **D (60-69):** 70-85% of used space is in home folders
- **F (<60):** >85% of used space is in home folders

**Calculation:**
```python
home_folders_ratio = (home_folders_total_bytes / used_bytes) * 100
# Lower ratio = better grade
```

**Meaning:** If home folders take up a small percentage of total used space, it means storage is well-distributed (system files, apps, etc. are using space appropriately). If home folders dominate, it suggests hoarding.

#### 3. Mac App Libraries Grades (Individual)
**Scanned libraries:**
- Photos library (`.photoslibrary`)
- Music library (`~/Music/iTunes` or `~/Music/Music`)
- Messages (`~/Library/Messages`)
- Mail (`~/Library/Mail`)
- Time Machine backups (`/Backups.backupdb`)
- Creative libraries (GarageBand, Logic Pro, Final Cut, etc.)

**Grading thresholds by library type:**

| Library Type | A | B | C | D | F |
|-------------|---|----|----|----|----|
| Photos | <50 GB | 50-100 GB | 100-200 GB | 200-300 GB | >300 GB |
| Music | <20 GB | 20-50 GB | 50-100 GB | 100-200 GB | >200 GB |
| Messages | <5 GB | 5-10 GB | 10-20 GB | 20-50 GB | >50 GB |
| Mail | <5 GB | 5-10 GB | 10-20 GB | 20-50 GB | >50 GB |
| Time Machine | <100 GB | 100-200 GB | 200-500 GB | 500-1000 GB | >1000 GB |
| Creative | <20 GB | 20-50 GB | 50-100 GB | 100-200 GB | >200 GB |

**Additional penalty:** If a library is >50% of total used space, subtract 20 points. If >30%, subtract 10 points. If >20%, subtract 5 points.

#### 4. Composite Storage Grade
**Weighted average of component grades:**

```python
weights = {
    'free_space': 0.4,        # 40% - most important
    'home_folders_ratio': 0.3, # 30% - organization indicator
    'mac_libraries': 0.3      # 30% - average of all library grades
}

composite_score = (
    free_space_score * 0.4 +
    home_folders_ratio_score * 0.3 +
    avg_library_scores * 0.3
)
```

---

## 3. Report Card Layout

### Page Structure

```
┌─────────────────────────────────────────┐
│ HEADER: Dad's Report Card              │
│ Overall Storage Grade: C+              │
│ "Room for improvement"                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STORAGE OVERVIEW                        │
│ (Current purple card with volume info)  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📊 STORAGE METRICS                      │
│ Top 10 Folders: 245.3 GB               │
│ Top 25 Files: 87.2 GB                  │
│ Reclaimable: 12.5% of used space      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STORAGE GRADE BREAKDOWN                 │
│                                         │
│ Free Space:        B (85/100)          │
│ Home Folders:      C (72/100)          │
│ Mac Libraries:     D (65/100)          │
│   • Photos:        C (75/100)          │
│   • Music:         B (82/100)          │
│   • Messages:      A (95/100)           │
│   • Mail:          D (68/100)          │
│                                         │
│ Overall:           C+ (74/100)          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 💬 DAD SAYS                             │
│ "downloads looks like a garage shelf"   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📋 YOUR HOMEWORK                        │
│ Priority 1: Free Up Space               │
│ 1. Delete [file] → Saves 3.0 GB        │
│ 2. Move [file] → Saves 2.0 GB           │
│ ...                                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📊 DETAILED DATA                        │
│ (Current folder bar chart, file lists)   │
└─────────────────────────────────────────┘
```

---

## 4. Mac App Library Scanners

### Implemented Scanners

All scanners are in `scanners/mac_libraries.py`:

1. **`scan_photos_library()`** - Finds all `.photoslibrary` bundles
2. **`scan_music_library()`** - Scans `~/Music/Music` and `~/Music/iTunes`
3. **`scan_messages()`** - Scans `~/Library/Messages`
4. **`scan_mail()`** - Scans `~/Library/Mail`
5. **`scan_time_machine_backups()`** - Scans `/Backups.backupdb` and volumes
6. **`scan_creative_libraries()`** - Scans GarageBand, Logic Pro, Final Cut libraries
7. **`scan_all_mac_libraries()`** - Runs all scanners and returns combined results

### Integration

The storage scanner (`scanners/storage.py`) now:
- Calculates `home_folders_total_bytes` (sum of all scanned folders)
- Calculates metrics: `sum_top_10_folders`, `sum_top_25_files`, `reclaimable_percent`
- Returns these in the scan results

Mac libraries are scanned separately and graded individually, then averaged for the composite grade.

---

## 5. Grading Functions

### Implementation

All grading functions are in `scanners/grading.py`:

- **`grade_free_space(free_percent)`** - Returns letter grade and score
- **`grade_home_folders_ratio(home_folders_bytes, total_used_bytes)`** - Returns letter grade, score, and ratio
- **`grade_library_size(library_size_bytes, library_type, total_used_bytes)`** - Returns letter grade, score, size in GB, and percent of used space
- **`calculate_storage_metrics(scan_data)`** - Calculates top 10 folders sum, top 25 files sum, and reclaimable percent
- **`calculate_composite_storage_grade(grades, weights)`** - Combines component grades with weighted average
- **`score_to_letter(score)`** - Converts 0-100 score to A-F letter

---

## 6. Actionable Advice System

### Priority-Based Action Items

**Critical actions (do first):**
1. Storage <10% free: "Delete top 5 files immediately - system at risk"
2. Reclaimable >20%: "You can free up X% by deleting top 25 files"

**High priority (this week):**
1. Downloads >10GB: "Clean Downloads folder - start with [top 3 files]"
2. Desktop >5GB: "Desktop cleanup - move files to Documents"
3. Large library (Photos >200GB, Music >100GB): "Consider offloading [library] to external storage"

**Medium priority (this month):**
1. Old backups: "Review Time Machine backups - archive or delete"
2. Large caches: "Clear [app] cache (saves X GB)"
3. Multiple large libraries: "Review Mac app libraries - consider offloading"

### Action Item Format

Each action item should be:
- **Specific:** "Delete `OmarHakimDrums2_96kHz_Multi_Pt1.zip` (3.0 GB)"
- **Actionable:** Direct link/button to reveal in Finder
- **Quantified:** Show space savings
- **Prioritized:** Numbered by impact

**Example:**
```
🎯 Your Action Plan (Save 18.5 GB)

1. [DELETE] Downloads/OmarHakimDrums2_96kHz_Multi_Pt1.zip
   → Saves 3.0 GB | Click to reveal in Finder

2. [MOVE] Photos Library (187 GB) → External Drive
   → Frees 187 GB | Consider offloading to external storage

3. [DELETE] Library/Caches/bigcache.dat
   → Saves 1.0 GB | Safe to delete
```

---

## 7. Visual Grade Display

### Grade Card Design

**Option A: Individual Grade Cards**
```
┌─────────────┬─────────────┬─────────────┐
│ Free Space │ Home Folders │ Mac Libs    │
│     B      │      C       │      D      │
│   (85/100) │   (72/100)   │   (65/100)  │
└─────────────┴─────────────┴─────────────┘
```

**Option B: Expandable Breakdown**
```
┌─────────────────────────────────────────┐
│ Storage Grade: C+ (74/100)              │
│                                         │
│ Free Space:        B (85/100)          │
│ Home Folders:      C (72/100)          │
│ Mac Libraries:     D (65/100)          │
│   ▼ Click to expand                    │
│     • Photos:      C (75/100)          │
│     • Music:       B (82/100)          │
│     • Messages:    A (95/100)          │
│     • Mail:        D (68/100)          │
└─────────────────────────────────────────┘
```

**Color coding:**
- Green: A-B grades (good)
- Yellow: C grade (needs attention)
- Red: D-F grades (action required)

---

## 8. Implementation Status

### ✅ Completed
- Mac app library scanners (`scanners/mac_libraries.py`)
- Grading functions (`scanners/grading.py`)
- Storage metrics calculation (in `scanners/storage.py`)
- Home folders ratio calculation

### 🔄 To Do
- Integrate Mac libraries scan into main storage scan flow
- Add grading to HTML report renderer
- Create visual grade cards in HTML
- Add "Your Homework" section with actionable items
- Test with real data and iterate

---

## 9. Key Principles

1. **Simplified grading** - Focus on storage, not all system metrics
2. **Multiple components** - Grade different aspects separately, then combine
3. **Actionable metrics** - Show reclaimable percentage, not just raw data
4. **Mac-specific** - Understand Mac app libraries and their typical sizes
5. **Weighted composite** - Free space is most important (40%), but organization matters too

---

## 10. Next Steps

1. **Integrate Mac libraries scan** into `yourdad.py` storage scan command
2. **Add grading to report generation** - Calculate grades when generating HTML report
3. **Create grade card UI** - Visual display of component and composite grades
4. **Add metrics section** - Display top 10 folders sum, top 25 files sum, reclaimable percent
5. **Build action item generator** - Create prioritized list based on grades and metrics
6. **Test and iterate** - Run on real systems and refine thresholds
