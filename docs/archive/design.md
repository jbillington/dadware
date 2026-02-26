
---
**NOTE:** This file contains research and technical design notes for duplicate detection and review workflows.
Main product spec is in `yourdad-prd.md`. Features here will be integrated into v0.2+.
---

# Design Research: Duplicate Detection & Review Workflows

## 1) Purpose & Outcomes

* **Primary goal:** Help a non-technical Mac user quickly **free up space** by finding **large files** first.
* **Secondary goal:** Identify **duplicate files** and present a safe way to review/remediate them (no auto-deletes).
* **Safety:** “**Manifest first, stage second, delete manually**.” No destructive actions by default.

## 2) Core UX Flow

1. **Choose a volume**

   * On launch, list **mounted volumes** (internal + external).
   * User picks one (default = system volume).
   * We **auto-exclude** risky/system areas (see ignore list).
2. **Scan**

   * Two scanners run (configurable order, default = Large Files → Duplicates):

     * **Large Files**: find biggest items first.
     * **Duplicates**: size → partial hash → full hash (only for candidates).
3. **Review outputs**

   * Generate a single **HTML report** with two tabs:

     * **Large Files** (default tab): sortable, filterable table, total reclaimable estimate.
     * **Duplicates**: summary metrics (groups, space impact), plus a tab to view all groups.
   * Generate a **manifest** (JSON) for both features.
   * (Optional) Build a **symlink review workspace** so users can inspect items safely in Finder.
4. **User action**

   * Clear instructions **how to delete manually** (Reveal in Finder).
   * (Optional) also generate a **Trash script** the user can run explicitly later.

## 3) Scanning Scope & Default Exclusions (macOS-friendly)

* **Default include:** The selected **volume**, but **prioritize Home folders** (they’re where the space usually is).
* **Default exclude (safety & noise):**

  * `/System`, `/Library`, `/Applications`, `/usr`, `/bin`, `/sbin`
  * App bundles: anything ending in `*.app/` (treat as a single file and skip)
  * **Photos libraries**: `*.photoslibrary/`
  * **Music/TV libraries**: `~/Music/Music/Media`, `~/Movies/TV/Media` (skip by default)
  * **Mail** data: `~/Library/Mail/`
  * **Caches & temp**: anything under `*/Library/Caches/*`, `*/tmp/*`
  * **Hidden/system files** starting with `.` unless the user enables “show hidden”
* **iCloud caveat:** Some files are **not fully downloaded**. Default behavior:

  * **Skip cloud-only placeholders** to avoid surprise downloads.
  * In report, show a small “cloud” icon for items that are not local (so user knows to fetch before deleting if desired).
  * (Implementation note for later: detect via `mdls`—e.g., ubiquitous keys like `kMDItemIsUbiquitous`, `kMDItemDownloadingStatus`, `kMDItemDownloadedDate`—and/or size-mismatch vs. `kMDItemLogicalSize`.)

## 4) Algorithms & Heuristics

### 4.1 Large Files

* **Finder modes:**

  * **Top-N largest** (default: N=500)
  * **Min size threshold** (e.g., `--min-size 250MB`)
  * Optional “**cold files**” filter (not modified in ≥180 days)
* **Output:**

  * Columns: path, size, modified date, suggested action (none), notes (e.g., “Cloud only”).
  * Add a **running total** of potential space reclaimed (sum of selected rows).

### 4.2 Duplicates

* **Pipeline (fast & safe):**

  1. **Group by exact file size** (byte-accurate; skip unique sizes immediately).
  2. **Partial hash** candidates (e.g., first **4 MB**). This weeds out most false positives fast.
  3. **Full hash** (**SHA-256**) only for files still matching size + partial hash.
* **Grouping key:** `sha256` (full hash).
* **Keeper suggestion** (non-binding): prefer **newest mtime** or shortest path; mark the rest as candidates.
* **Output:** Per group: size, count, total reclaimable (size × (count−1)), list of member paths.

## 5) Manifests (source of truth)

Store one **JSON** manifest per feature (easier to extend later):

### 5.1 `manifest_large.json`

```json
{
  "scanned_volume": "/",
  "scanned_at_utc": "2025-11-09T13:45:00Z",
  "criteria": { "mode": "topN", "topN": 500, "min_size_bytes": null },
  "items": [
    {
      "path": "/Users/you/Movies/big.mov",
      "size_bytes": 2147483648,
      "mtime_iso": "2025-08-02T16:10:03-04:00",
      "is_cloud_only": false
    }
  ]
}
```

### 5.2 `manifest_dupes.json`

```json
{
  "scanned_volume": "/",
  "scanned_at_utc": "2025-11-09T13:55:00Z",
  "hash": "sha256",
  "partial_hash_bytes": 4194304,
  "groups": [
    {
      "group_id": "sha256:6c5f...a2",
      "size_bytes": 104857600,
      "count": 3,
      "reclaimable_bytes": 209715200,
      "members": [
        {
          "path": "/Users/you/Downloads/vid.mp4",
          "mtime_iso": "2025-06-10T09:12:30-04:00",
          "role": "keeper_suggested"
        },
        {
          "path": "/Users/you/Desktop/vid (copy).mp4",
          "mtime_iso": "2025-06-10T09:11:01-04:00",
          "role": "candidate"
        },
        {
          "path": "/Volumes/Media/vid.mp4",
          "mtime_iso": "2025-06-08T15:22:44-04:00",
          "role": "candidate"
        }
      ]
    }
  ],
  "summary": {
    "total_groups": 42,
    "total_members": 117,
    "total_reclaimable_bytes": 987654321
  }
}
```

## 6) Review Workspace (“Symlink Farm”)

* Create under the current working dir (or a user-provided path):

  * `_review/largest/` → symlinks named with **size-first** prefix for easy sorting (e.g., `002.13GB__big.mov → /abs/path`)
  * `_review/duplicates/<group_id>/` → symlinks to each member; include a tiny `README.txt` with:

    * “Suggested keeper: …”
    * “To free space, **delete the original**, not this symlink. Right-click → Show Original.”
* This adds clarity without touching originals or consuming extra space.

## 7) HTML Report (single file)

* **Two tabs:** “Large Files” (default) and “Duplicates”.
* **Table features:** client-side **sort**, **filter** (size threshold, date, cloud-only toggle).
* **Links & actions:**

  * Each row includes a **file://** link to the **original** (opens in Finder).
  * A small “copy” button that copies `open -R "/absolute/path"` to the clipboard (Reveal In Finder).
* **Summary bars:**

  * Large Files: **count**, **total size listed**, **top-N cut**.
  * Duplicates: **groups**, **files in groups**, **reclaimable estimate**.
* **Styling:** small embedded CSS, zero external dependencies (works offline).

## 8) CLI Shape (simple, friendly)

* One binary/script with subcommands:

  * `scan volume` → prompts user to pick a mounted volume.
  * `scan large --top 500 --min-size 250MB`
  * `scan dupes --partial 4MB --hash sha256`
  * `report html --out report.html` (reads manifests and builds a single report)
  * `stage review --out _review --what largest,dupes`
  * `generate-trash-script --from manifest_large.json --out trash_large.sh`
    (also allow from `manifest_dupes.json` filtered to non-keepers)
* **Defaults:** never delete; never require flags for the common path; **dry, safe, quiet**.

## 9) Performance Defaults

* **I/O is the bottleneck.** Keep CPU simple.
* **Partial hash size:** default **4 MB**, configurable.
* **Threading:** modest parallelism (e.g., 2–4 workers) to saturate SSD reads without thrashing.
* **Skip unreadable files** with a warning counter; don’t crash the run.

## 10) Permissions & Privacy

* Advise the user to grant **Full Disk Access** if scanning outside Home or on external volumes with protected content.
* Never upload or transmit data.
* Manifests live locally alongside the tool unless the user sets `--out`.

## 11) Edge Cases & Policies

* **Cross-volume duplicates:** still detected, but no hard-linking/cloning. We only **report** and symlink for review.
* **Cloud-only files:** show but **don’t hash**; mark clearly; skipping avoids auto-downloads.
* **Packages** (apps, Photos libraries, etc.): **skip entirely** by default for safety.
* **Symlinks & aliases:** follow only if user opts in (`--follow-symlinks`); otherwise treat as leaf items.

## 12) User Guidance (non-techies)

* Top of the report: a **3-step banner**:

  1. **Review** largest items / duplicate groups.
  2. Click the **link** or **Reveal** to open in Finder.
  3. **Delete manually** (send to Trash) from the original location.
     *(Optional: run the generated Trash script if you’re comfortable.)*
* Clear note: **Deleting symlinks does nothing**. Always delete the **original**.

## 13) Telemetry & Logging (local)

* A small local log (text) with start/end time, volume chosen, counts, errors skipped.
* No personal data beyond file paths in manifests.

## 14) Future Extensions (explicitly out of v1)

* **APFS clones** mode for dupes (storage-efficient but confusing for deletion UX).
* **Deeper iCloud metadata** (more reliable “cloud-only” detection).
* **Library-aware plugins** (Photos/Music aware, with inside-library safety).
* **Incremental scans** with on-disk hash cache.
* **Windows port** (NTFS hard links; symlink permissions).

---

## Defaults Summary (so there’s no ambiguity)

* Start screen: list mounted volumes → user picks one.
* Large Files tab **first**.
* Duplicates use: **size → 4 MB partial hash → SHA-256 full**.
* **JSON** manifests.
* Build **symlink review** trees under `_review/…`.
* One **HTML** report with **file://** links and **Reveal command copy** button.
* **No deletes** by default; optional **Trash script** generation.
* Skip system areas, app bundles, Photos libraries, Mail, caches; skip cloud-only files.

---

If you want, I can turn this into a repo skeleton (folders, README, empty Python modules, and the HTML template with the two-tab layout). Any questions or tweaks you want before you start wiring it up?
