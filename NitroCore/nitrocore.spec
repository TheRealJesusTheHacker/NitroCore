# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=['psutil', 'win32service', 'win32serviceutil', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'black', 'flake8'],
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
    name='NitroCoreOptimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # M-7: UPX packing disabled — UPX is a known AV-heuristic trigger and can
    # break PyInstaller onefile binaries. Slightly larger exe, far fewer
    # false positives.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    # M-7: no code signature yet. Releases are verified via the published
    # SHA256SUMS.txt. Signing (even an OV cert) is a manual release step —
    # see SECURITY.md "Release signing". Until then, SmartScreen will warn
    # on first run; that is expected.
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    uac_admin=True,
)
