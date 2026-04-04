# Dad Ware

Scans your Mac's storage and memory, gives you a report card with letter grades, and tells you what to clean up. **Read-only** — it never deletes anything.

## Setup

1. Download and extract the ZIP
2. Open Terminal
3. Run:
```bash
cd ~/Downloads/yourdad
chmod +x yourdad
./yourdad
```

If macOS shows a security warning, right-click `yourdad` → **Open** (first time only).

## Commands

```bash
./yourdad          # Scan storage (default)
./yourdad cpu      # Scan CPU and RAM
./yourdad all      # Scan both
```

A report opens in your browser automatically.

## Permissions (Optional)

To scan Photos, Messages, and Mail: **System Settings** → **Privacy & Security** → **Full Disk Access** → add **Terminal.app**.

Without this, the scan still works — protected libraries just show 0 bytes.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Permission denied" | `chmod +x yourdad` |
| Security warning | Right-click → Open (once) |
| Wrong folder | `cd ~/Downloads/yourdad` |

## Safety

This tool only scans and reports. It does not delete files, and it does not advise you what to delete. Any cleanup decisions are yours.

---

MIT License — Copyright (c) 2025 John Billington. See [LICENSE](LICENSE).

For development docs, see [TECHNICAL.md](TECHNICAL.md).
