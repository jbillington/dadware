# Building the Executable - Dad Ware

This guide explains how to build a standalone executable that bundles Python and all dependencies. **End users don't need Python installed!**

---

## Why Build an Executable?

✅ **Solves QGIS conflicts** - Uses bundled Python, not system Python  
✅ **Easy distribution** - Single file, no dependencies  
✅ **User-friendly** - No Python installation required  
✅ **Works everywhere** - No PATH issues  

---

## Prerequisites

1. **Python 3.9+** installed on your build machine
2. **PyInstaller** installed:
   ```bash
   pip install pyinstaller
   ```

---

## Building the Executable

### Quick Build

```bash
./build_executable.sh
```

This will:
- Check if PyInstaller is installed
- Clean old builds
- Build the executable
- Show you where it is (`dist/yourdad`)

### Manual Build

```bash
pyinstaller yourdad.spec
```

The executable will be created at: `dist/yourdad`

---

## Testing the Executable

```bash
# Test storage scan (default)
./dist/yourdad

# Test CPU scan
./dist/yourdad cpu

# Test full scan
./dist/yourdad all
```

---

## Distribution

### For End Users

1. **Build the executable** (see above)
2. **Copy `dist/yourdad`** to wherever you want
3. **Share it** - users just need to:
   - Download the file
   - Right-click → Open (first time only - security warning)
   - Run: `./yourdad`

### Security Warning (First Run)

macOS will show a security warning because the executable isn't code-signed. Users need to:
1. Right-click the executable
2. Select "Open"
3. Click "Open" in the security dialog

**Note:** To avoid this, you'd need to code-sign the executable with an Apple Developer ID (costs $99/year).

---

## File Size

The executable will be approximately:
- **20-40 MB** (includes Python interpreter and all modules)
- Compressed with UPX (if available)

This is normal for PyInstaller executables - they bundle everything needed to run.

---

## Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Permission denied"
```bash
chmod +x build_executable.sh
chmod +x dist/yourdad
```

### Executable doesn't work
- Check that all modules are in `hiddenimports` in `yourdad.spec`
- Rebuild: `rm -rf build dist && ./build_executable.sh`

### Large file size
- This is normal - PyInstaller bundles Python interpreter
- Can't be much smaller without removing functionality

---

## Advanced: Code Signing (Optional)

To avoid security warnings, you can code-sign the executable:

1. Get an Apple Developer ID ($99/year)
2. Update `yourdad.spec`:
   ```python
   codesign_identity='Developer ID Application: Your Name (TEAM_ID)'
   ```
3. Rebuild

---

## Benefits Over Python Script

| Feature | Python Script | Executable |
|---------|--------------|------------|
| Python Required | ✅ Yes | ❌ No |
| QGIS Conflicts | ⚠️ Possible | ✅ None |
| PATH Issues | ⚠️ Possible | ✅ None |
| Distribution | ⚠️ Complex | ✅ Single file |
| User Experience | ⚠️ Technical | ✅ Simple |

---

## Next Steps

1. Build the executable: `./build_executable.sh`
2. Test it: `./dist/yourdad`
3. Share it with testers (Max, Graham, etc.)
4. Get feedback on usability
5. Consider code signing for production

---

**Last Updated:** December 2025

