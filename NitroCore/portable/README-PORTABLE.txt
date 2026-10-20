NitroCore - Portable Edition
Sentinel Safeguard LLC

WHAT THIS IS
------------
The full NitroCore Windows system optimizer in portable form:
the same application, the same Gaming and Cybersecurity profiles,
the same preview mode and restore-point safety as the regular
release, built as a folder instead of a single file. There is no
installer and nothing to install. Unzip NitroCorePortable.zip
anywhere - a USB stick works - and run it from that folder.

HOW TO RUN IT
-------------
1. Unzip the whole NitroCorePortable.zip. Do not run the .exe
   from inside the zip: NitroCoreOptimizer.exe needs its
   _internal folder beside it, exactly as unzipped.
2. Run NitroCoreOptimizer.exe - a plain double-click is fine,
   and so is starting it from another program (for example the
   Technician's Toolkit launcher). NitroCore tunes system
   settings, so it asks for elevation itself when it starts
   (one Windows prompt); if you decline the prompt it shows
   "Access Denied" and exits instead of half-working.
3. Pick a profile (Gaming or Cybersecurity) and run a tab, or
   press Run All. High-impact steps offer a system restore
   point first, exactly as in the regular edition.

Preview mode works from the portable folder too - it changes
nothing and needs no elevation. From a terminal in this folder:

    NitroCoreOptimizer.exe --dry-run

WHAT "PORTABLE" DOES AND DOES NOT MEAN HERE (honest list)
---------------------------------------------------------
- No install: no setup program, no Start Menu entry, no
  uninstaller. Delete the unzipped folder and the program
  itself is gone.
- It is NOT fully self-contained. NitroCore still writes where
  NitroCore has always written: its rotating log under
  %APPDATA%\NitroCore\logs and registry-undo snapshots under
  %APPDATA%\NitroCore\registry_undo. Deleting the folder does
  not delete those, and it does not undo any tuning you applied
  (use Restore Previous Registry Values in the app, or the
  restore point it offered, for that).
- It still changes the machine it runs on - that is the tool's
  job. Registry tweaks, service changes, cleanups, and power
  plans apply to the PC in front of you, not to the folder.
- Windows only, and it needs administrator rights for anything
  except the --dry-run preview.

VERIFY YOUR DOWNLOAD
--------------------
Every release ships SHA256SUMS.txt covering both
NitroCoreOptimizer.exe and NitroCorePortable.zip. In PowerShell:

    certutil -hashfile NitroCorePortable.zip SHA256

Compare the output against the NitroCorePortable.zip line in
SHA256SUMS.txt from the same release. Release binaries are
currently unsigned, so Windows SmartScreen will warn on first
run - verify the hash before trusting the binary.
