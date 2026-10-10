# winget packaging for NitroCore

Submitted to [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs):
**PR #450105** — New package: TheRealJesusTheHacker.NitroCore version 1.1.2
(manifests at `manifests/t/TheRealJesusTheHacker/NitroCore/1.1.2/`).

Once merged, install with: `winget install TheRealJesusTheHacker.NitroCore`

## Manifest reference (v1.1.2)

- PackageIdentifier: `TheRealJesusTheHacker.NitroCore`
- Installer: https://github.com/TheRealJesusTheHacker/NitroCore/releases/download/v1.1.2/NitroCoreOptimizer.exe
- InstallerSha256: `E265F14E91271958D4FEFE6DDC7E7E9ABEBAC6FD3DA0C525D870CE341F158A4E`
  (verified against the v1.1.2 release's SHA256SUMS.txt)
- Scope: machine (the app requires admin; self-elevates via manifest)
- InstallModes: interactive (the portable exe has no silent switches)

## Cutting a new winget version

1. Tag `vX.Y.Z` in this repo so the release workflow builds the .exe.
2. Download SHA256SUMS.txt from that GitHub Release; take the hash for NitroCoreOptimizer.exe.
3. In your winget-pkgs fork, copy the 1.1.2 manifest directory to the new version,
   update PackageVersion, InstallerUrl, InstallerSha256, ReleaseNotesUrl.
4. Open a PR against microsoft/winget-pkgs.
