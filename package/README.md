# Dad Ware - Mac Cleanup Tool

**Version:** 0.1-poc  
**Last Updated:** December 13, 2025

---

## What is Dad Ware?

Dad Ware scans your Mac's storage and memory, then gives you a report card with:
- 📊 **Letter grades** (A-F) for storage health
- 💬 **Dad-style commentary** with helpful advice
- 💡 **Actionable tips** for freeing up space
- 📁 **Interactive HTML reports** with detailed file analysis

**Safety First:** This tool is **read-only** - it never deletes files. You control what gets deleted.

---

## Quick Start

### 1. Download and Extract

1. Download the `yourdad.zip` file from the link provided
2. Extract the ZIP file (double-click it)
3. You'll see a folder with:
   - `yourdad` (the executable file)
   - `README.html` (open this in your browser for instructions)
   - `README.md` (this file)

### 2. First Run - Security Warning

On first run, macOS may show a security warning. Here's how to fix it:

**Option 1 (Easiest):**
- Right-click the `yourdad` file
- Select **Open**
- Click **Open** in the security dialog
- This only needs to be done once

**Option 2 (Terminal):**
```bash
xattr -d com.apple.quarantine yourdad
```

### 3. Make It Executable

Open Terminal and run:
```bash
cd ~/Downloads/yourdad  # (or wherever you extracted it)
chmod +x yourdad
```

### 4. Run Your First Scan

```bash
# Scan storage (find large files and folders)
./yourdad scan storage

# Scan CPU and RAM usage
./yourdad scan cpu

# Scan both (opens both reports)
./yourdad scan all
```

The HTML report will open automatically in your browser!

---

## Permissions (Optional)

To scan Photos, Messages, and Mail libraries, you need **Full Disk Access**:

1. Open **System Settings** → **Privacy & Security**
2. Scroll to **Full Disk Access**
3. Click the lock icon and enter your password
4. Click **+** and add **Terminal.app**
5. Make sure the checkbox is checked ✅
6. Restart Terminal

**Note:** The scan will work without permissions, but protected libraries will show 0 bytes.

---

## Commands

### Storage Scan
```bash
./yourdad scan storage
```

### CPU/RAM Scan
```bash
./yourdad scan cpu
```

### Combined Scan
```bash
./yourdad scan all
```

---

## Report Locations

Reports are automatically saved to:
- `~/.dadware/reports/` (hidden folder in your home directory)

Each scan creates an HTML report that opens in your browser automatically.

---

## Troubleshooting

### "Permission denied"
Make sure you made the file executable:
```bash
chmod +x yourdad
```

### Security warning
Right-click the file → **Open** (first time only)

### "No such file or directory"
Make sure you're in the right folder:
```bash
cd ~/Downloads/yourdad  # (or wherever you extracted it)
```

---

## Safety & Disclaimer

**Read-Only by Design**: This tool never deletes files. It only scans and reports. You control what gets deleted.

**Important**: This software provides reports and information about what is taking up space on your computer. It does NOT provide advice about what to delete or archive. **You must determine, at your own discretion, what files or folders to delete or archive from your computer.** The authors are not responsible for any data loss or consequences resulting from decisions you make based on information provided by this software.

---

## License

Copyright (c) 2025 John Billington

This project is licensed under the **MIT License**.

**Permission is hereby granted, free of charge**, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED**, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the Software or the use or other dealings in the Software.

See the [LICENSE](LICENSE) file for the full license text.

---

## Technical Documentation

For developers and advanced users, see [TECHNICAL.md](TECHNICAL.md) for:
- Advanced commands and options
- Development setup
- Project structure
- Building from source
- Architecture details
- Contributing guidelines

---

**Made with ❤️ by a dad who's tired of explaining disk space**
