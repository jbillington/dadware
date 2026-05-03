# Ask Dad for Mac
*by DadWare*

## About the program
Ask Dad is a free tool for kids and adults who need to know why their Mac is running slow or why they are out of storage.  It is both a learning tool for the file system and a way to get a detailed report about your system performance and available storage. 

Use Ask Dad to scan your Mac's file system, measure available space and provide a HTML report card with letter grades and advice. The report card lets you visually see what folders are taking up space, highlights the largest files, and tells you what to clean up. The scan program is similar but provides an overview of memory pressure and CPU hogging processes for quick diagnoses.  

Under the hood Ask Dad is a python program that scans your hard drive and measures file sizes.  It is lightweight and doesn't have dependencies other than python.  It was made by a Dad who is an engineer. The code was written by AI but it contains no calls to AI services. The program is Read-Only so it never deletes your files, we leave that to you. 


## 📄 License and Trademarks

Ask Dad and DadWare are trademarks of John Billington.

You are free to use, modify, and distribute the open source code in this repository under the terms of the MIT License. However, you may not use the names Ask Dad, DadWare, or any associated branding (including logos) to market or distribute derivative works without prior written permission.

If you fork or build on this project, please use a different name for your version.

This project is licensed under the MIT License. 

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
