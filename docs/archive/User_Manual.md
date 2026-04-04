# Dad Ware User Manual

**Product:** Dad Ware (yourdad)
**Audience:** End users
**Version:** 0.1-poc

---

## 1) What Dad Ware Does

Dad Ware scans your Mac and generates easy-to-read reports about:

- Storage usage (largest folders and files)
- CPU and RAM usage (top processes and memory pressure)
- A letter-grade “report card” with tips and dad-style commentary

**Read-only by design:** Dad Ware never deletes files. You decide what to remove.

---

## 2) Getting Started

### 2.1 Download and Extract

1. Download the `yourdad.zip` file you were given.
2. Double-click to extract it.
3. You should see:
   - `yourdad` (executable)
   - `README.html`
   - `README.md`

### 2.2 First Run Security Warning (macOS)

macOS may block the app on first run. Use one of the following:

**Option A (recommended):**
1. Right-click `yourdad` → **Open**
2. Click **Open** in the dialog

**Option B (Terminal):**
```bash
xattr -d com.apple.quarantine yourdad
```

### 2.3 Make It Executable

```bash
cd ~/Downloads/yourdad  # or wherever you extracted it
chmod +x yourdad
```

---

## 3) Basic Usage

### 3.1 Storage Scan

```bash
./yourdad scan storage
```

What you get:
- Storage grade (A–F)
- Largest folders and files
- Home folder breakdown (Desktop, Downloads, Documents, etc.)
- Mac library sizes (Photos, Messages, Mail) if permission allows
- HTML report opened in your browser

### 3.2 CPU/RAM Scan

```bash
./yourdad scan cpu
```

What you get:
- Memory pressure status (low/medium/high)
- Total RAM usage
- Largest memory-consuming apps/processes
- HTML report opened in your browser

### 3.3 Full Scan (Storage + CPU)

```bash
./yourdad scan all
```

This runs both scans and opens two reports.

---

## 4) Choosing a Volume (Storage Scans)

If you don’t provide a volume, Dad Ware shows a menu of mounted volumes and prompts you to choose one. The home directory is always scanned separately to provide a detailed home-folder breakdown.

You can also specify a volume directly:

```bash
./yourdad scan storage --volume /Volumes/ExternalDrive
```

---

## 5) Report Files and Locations

Each scan creates **two files**:

- HTML report (visual report)
- JSON manifest (raw data)

**Default location:**
- `~/.dadware/reports/`

Example:
- `~/.dadware/reports/storage_2025-11-09_14-23.html`
- `~/.dadware/reports/storage_2025-11-09_14-23.json`

### 5.1 Opening Reports

Reports open automatically in your browser after the scan. You can also open them manually:

```bash
open ~/.dadware/reports/storage_2025-11-09_14-23.html
```

---

## 6) Permissions for Protected Libraries

To scan Photos, Messages, and Mail libraries, you need **Full Disk Access**.

### 6.1 Grant Full Disk Access

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the lock icon and authenticate
3. Click **+** and add **Terminal.app** (recommended)
4. Make sure it is checked ✅
5. Restart Terminal

If you don’t grant access, the scan still works, but protected libraries show as **0 bytes**.

---

## 7) Command Reference

### 7.1 `scan storage`

```bash
./yourdad scan storage [options]
```

Options:
- `--volume /path` : scan a specific volume
- `--top N` : number of top files to list (default: 500)
- `--min-size 500MB` : ignore files smaller than this
- `--terminal` : terminal output only (no HTML)
- `--no-color` : disable colored terminal output
- `--skip-protected` : skip protected libraries entirely
- `--no-mac-libraries` : skip Photos/Messages/Mail scans (faster)

### 7.2 `scan cpu`

```bash
./yourdad scan cpu [options]
```

Options:
- `--terminal` : terminal output only (no HTML)
- `--no-color` : disable colored terminal output
- `--export-memory memory.csv` : export all processes to a CSV during the scan

### 7.3 `scan all`

```bash
./yourdad scan all [options]
```

Options:
- `--volume /path` : scan a specific volume
- `--terminal` : terminal output only (no HTML)
- `--no-color` : disable colored terminal output
- `--skip-protected` : skip protected libraries entirely
- `--no-mac-libraries` : skip Photos/Messages/Mail scans (faster)

---

## 8) Export Memory Data to CSV

You can export memory/process data in two ways.

### 8.1 During a CPU Scan

```bash
./yourdad scan cpu --export-memory memory.csv
```

### 8.2 From an Existing Report

```bash
./yourdad export memory cpu_2025-11-26_16-54.json
```

Optional output path:

```bash
./yourdad export memory cpu_2025-11-26_16-54.json --output memory_export.csv
```

---

## 9) Understanding the Reports

Each report includes:

- **Grade (A–F):** overall storage or memory health
- **Highlights:** top folders/files or top processes
- **Dad commentary:** short tips and warnings
- **Actionable tips:** ideas for what to review or clean

**Screenshot placeholder:** Add a screenshot of the HTML report here.

---

## 10) Troubleshooting

### “Permission denied”

```bash
chmod +x yourdad
```

### “Security warning”

Right-click the file → **Open** (first run only)

### “No such file or directory”

Make sure you are in the folder where `yourdad` exists:

```bash
cd ~/Downloads/yourdad
```

---

## 11) Safety and Disclaimer

Dad Ware is **read-only**. It does not delete or modify files. You control any cleanup actions. Use the reports to decide what to remove.

---

## 12) Quick Cheat Sheet

```bash
# Storage scan
./yourdad scan storage

# CPU/RAM scan
./yourdad scan cpu

# Full scan
./yourdad scan all

# Export memory to CSV during scan
./yourdad scan cpu --export-memory memory.csv

# Export memory from an existing report
./yourdad export memory cpu_2025-11-26_16-54.json
```
