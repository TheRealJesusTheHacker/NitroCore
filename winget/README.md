# winget manifest drafts for NitroCore
# These go in a PR to https://github.com/microsoft/winget-pkgs
# Directory layout there: manifests/t/TheRealJesusTheHacker/NitroCore/1.0.0/
#
# BEFORE SUBMITTING:
# 1. Tag v1.0.0 in the NitroCore repo so the release workflow builds the .exe.
# 2. Download SHA256SUMS.txt from that GitHub Release and replace <FILL_SHA256_BELOW>.
# 3. Submit the three files below as a PR to microsoft/winget-pkgs.

# --- File 1: TheRealJesusTheHacker.NitroCore.yaml ---
# PackageIdentifier: TheRealJesusTheHacker.NitroCore
# PackageVersion: 1.0.0
# PackageLocale: en-US
# Publisher: JesusTheHacker
# PackageName: NitroCore
# License: MIT
# ShortDescription: Free Windows optimizer for gaming and cybersecurity workstations.
# ManifestType: version
# ManifestVersion: 1.6.0

# --- File 2: TheRealJesusTheHacker.NitroCore.installer.yaml ---
# PackageIdentifier: TheRealJesusTheHacker.NitroCore
# PackageVersion: 1.0.0
# InstallModes:
# - interactive
# Installers:
# - Architecture: x64
#   InstallerType: exe
#   InstallerUrl: https://github.com/TheRealJesusTheHacker/NitroCore/releases/download/v1.0.0/NitroCoreOptimizer.exe
#   InstallerSha256: <FILL_SHA256_BELOW>
# ManifestType: installer
# ManifestVersion: 1.6.0

# --- File 3: TheRealJesusTheHacker.NitroCore.locale.en-US.yaml ---
# PackageIdentifier: TheRealJesusTheHacker.NitroCore
# PackageVersion: 1.0.0
# PackageLocale: en-US
# Publisher: JesusTheHacker
# PackageName: NitroCore
# License: MIT
# ShortDescription: Free Windows optimizer for gaming and cybersecurity workstations.
# Description: NitroCore tunes Windows for gaming or cybersecurity tasks — temp and
#   browser cleanup, disk cleanup, registry tuning, service management, and the
#   Ultimate Performance power plan, all with restore-point safety and a preview
#   mode that shows every change before it is applied. Free and open source.
# Moniker: nitrocore
# Tags:
# - optimizer
# - gaming
# - windows-tweaker
# - performance
# ReleaseNotesUrl: https://github.com/TheRealJesusTheHacker/NitroCore/releases/tag/v1.0.0
# ManifestType: defaultLocale
# ManifestVersion: 1.6.0
