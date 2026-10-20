# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the NitroCore PORTABLE edition — a one-folder
# build of the exact same application as nitrocore.spec (same entry
# point main.py, same datas, same hiddenimports, same icon, same
# uac_admin elevation request). The only difference is layout:
#
#   * nitrocore.spec            -> one file:  dist/NitroCoreOptimizer.exe
#   * nitrocore-portable.spec  -> one folder: dist/NitroCoreOptimizer/
#     (NitroCoreOptimizer.exe + _internal/), which the release
#     workflow zips as NitroCorePortable.zip. No installer, nothing
#     to install: unzip anywhere and run the .exe from its folder.
#
# Build (from this NitroCore/ folder, on Windows):
#     pyinstaller --noconfirm nitrocore-portable.spec
# The release workflow builds it into a separate dist-portable/
# tree so it never collides with the one-file build:
#     pyinstaller --noconfirm --distpath dist-portable \
#         --workpath build-portable nitrocore-portable.spec
#
# Portable here means "no install" only. NitroCore still needs
# administrator rights to tune the system, and it still writes its
# logs and registry-undo snapshots under %APPDATA%\NitroCore —
# see portable/README-PORTABLE.txt, which ships inside the zip.

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
    [],
    exclude_binaries=True,
    name='NitroCoreOptimizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Same call as nitrocore.spec (M-7): UPX packing disabled — UPX
    # is a known AV-heuristic trigger. Slightly larger build, far
    # fewer false positives.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    # Same call as nitrocore.spec (M-7): no code signature yet.
    # Releases are verified via the published SHA256SUMS.txt; until
    # signing lands, SmartScreen will warn on first run.
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    uac_admin=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NitroCoreOptimizer',
)
