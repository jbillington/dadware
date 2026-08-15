# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for yourdad (Dad Ware)
# Build with: pyinstaller yourdad.spec
# Or use: ./build_executable.sh

import os

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
        'scanners.models',
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
        'utils.version',
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
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    # UPX is a known cause of macOS code-signing/notarization breakage
    # (it rewrites the Mach-O in ways that can invalidate signatures or
    # trip Gatekeeper), and it isn't installed on this machine anyway
    # (silently skipped when absent). Disabled outright rather than
    # relying on "not installed" as the safety net.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console app (not GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    # PyInstaller cannot cross-compile: a 'universal2' output requires the
    # *building* Python itself to be a universal2 build. On a plain
    # x86_64-only (or arm64-only) Python, requesting 'universal2' makes the
    # build fail outright rather than silently produce a single-arch binary.
    # Default to None (native arch) for local/dev builds, and let CI opt in
    # explicitly by setting DADWARE_TARGET_ARCH=universal2 once it runs on
    # a universal2 Python (e.g. python.org installer or a universal2 venv).
    target_arch=os.environ.get('DADWARE_TARGET_ARCH') or None,
    # Signing identity and entitlements are read from the environment so
    # CI can sign during the build without any credentials being
    # hardcoded here. Both are None (unsigned, no entitlements) for local
    # dev builds where these vars aren't set. See sign_and_notarize.sh for
    # a standalone post-build signing/notarization path.
    codesign_identity=os.environ.get('DADWARE_CODESIGN_IDENTITY') or None,
    entitlements_file=os.environ.get('DADWARE_ENTITLEMENTS') or None,
)


