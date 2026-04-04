# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for yourdad (Dad Ware)
# Build with: pyinstaller yourdad.spec
# Or use: ./build_executable.sh

block_cipher = None

a = Analysis(
    ['yourdad.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Ensure all modules are included
        'personality',
        'personality.yourdad',
        'scanners',
        'scanners.storage',
        'scanners.cpu',
        'scanners.mac_libraries',
        'scanners.grading',
        'renderers',
        'renderers.html',
        'renderers.terminal',
        'utils',
        'utils.formatters',
        'utils.path_utils',
        'utils.subprocess_utils',
        'utils.volumes',
        'utils.permissions',
        'utils.system_info',
        'utils.llm_prompt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='yourdad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress binary (smaller file size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console app (not GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Set to your Developer ID for code signing
    entitlements_file=None,
)


