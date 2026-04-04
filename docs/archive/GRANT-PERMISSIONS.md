# How to Grant Full Disk Access to yourdad

To scan Photos, Messages, and Mail libraries, macOS requires **Full Disk Access** permission.

## Steps to Grant Permission

### 1. Open System Settings
- Click the Apple menu (🍎) → **System Settings**
- Or press `Cmd + Space` and search for "System Settings"

### 2. Navigate to Privacy & Security
- In the sidebar, click **Privacy & Security**
- Scroll down to find **Full Disk Access**

### 3. Add Python/Terminal
You need to grant access to the application that runs the script:

**Option A: Grant to Terminal (Recommended)**
- Click the **+** button (or lock icon if locked)
- Navigate to `/Applications/Utilities/`
- Select **Terminal.app**
- Make sure the checkbox is **checked** ✅

**Option B: Grant to Python directly**
- Click the **+** button
- Navigate to where Python is installed (usually `/usr/bin/python3` or `/opt/homebrew/bin/python3`)
- You may need to use `Cmd+Shift+G` in the file picker to navigate to these paths
- Add Python and make sure it's checked ✅

**Option C: Grant to your IDE/Editor**
- If you're running the script from VS Code, Cursor, or another editor:
- Add that application to Full Disk Access
- For Cursor: `/Applications/Cursor.app`
- For VS Code: `/Applications/Visual Studio Code.app`

### 4. Restart Terminal/Application
- **Important**: Close and reopen Terminal (or your IDE) after granting permission
- Permissions only take effect after restarting the application

### 5. Verify Permission
Run this test command:
```bash
python3 -c "import os; print('Messages accessible:', os.path.exists(os.path.expanduser('~/Library/Messages')))"
```

If you see `Messages accessible: True`, the permission is working.

## Alternative: Use Terminal's `du` Command

If granting Full Disk Access doesn't work, the scanner will try to use the `du` command as a fallback, which may have different permission requirements.

## Troubleshooting

**Permission still not working?**
1. Make sure you **restarted Terminal/your IDE** after granting permission
2. Try running the script from Terminal.app directly (not from an IDE)
3. Check System Settings → Privacy & Security → Full Disk Access to ensure the app is checked ✅

**Still can't access?**
- Some Photos libraries may be in iCloud and not stored locally
- Messages may be synced to iCloud and not fully on disk
- The scanner will still show the libraries exist, just with 0 size

## Security Note

Full Disk Access is a powerful permission. Only grant it to applications you trust. The `yourdad` script is read-only and never modifies or deletes files.

