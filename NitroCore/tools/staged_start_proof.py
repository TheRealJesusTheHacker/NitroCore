"""Staged start proof for the release pipeline (Windows runner).

The v1.1.4 field failure: NitroCore's executables carried a
requireAdministrator manifest, so the Technician's Toolkit launcher
(which starts tools with CreateProcess, like any ordinary program)
got WinError 740 and reported "could not be started" — the program
never ran at all. This proof exists so that failure mode can never
ship again unnoticed. The release workflow runs it after the builds
and before anything is published:

1. Neither built .exe may carry a requireAdministrator manifest.
2. The portable build is assembled in BOTH the standalone layout
   and a bundle-style layout (its .exe and _internal at a shared
   root, among the other tools' files) and started the way the
   Toolkit launcher starts it — subprocess (CreateProcess), working
   directory at the layout root — with --self-check as the designed
   first checkpoint. Exit code 0 plus the proof file the program
   writes are required, every time.

The same layouts are then started once more by the workflow as a
non-administrator user (tools/staged_start_spawner.py) — the exact
token class that hit WinError 740 in the field.

Usage:
    python tools/staged_start_proof.py <portable_dir> <onefile_exe> <proof_root>
"""

import os
import shutil
import subprocess
import sys

LEVELS = (b"requireAdministrator", b"highestAvailable", b"asInvoker")


def manifest_level(exe_path):
    with open(exe_path, "rb") as handle:
        data = handle.read()
    for level in LEVELS:
        if level in data:
            return level.decode()
    return "none found"


def fail(message):
    print(f"STAGED START PROOF FAILED: {message}", flush=True)
    raise SystemExit(1)


def run_self_check(exe, cwd, out_file):
    env = dict(os.environ)
    env["NITROCORE_SELF_CHECK_OUT"] = out_file
    try:
        proc = subprocess.run(
            [exe, "--self-check"],
            cwd=cwd,
            env=env,
            timeout=180,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        fail(f"spawn of {exe} (cwd={cwd}) raised {exc!r}")
    if proc.returncode != 0:
        fail(f"--self-check in {cwd} exited {proc.returncode}: {proc.stdout!r}")
    if not os.path.isfile(out_file):
        fail(f"--self-check in {cwd} did not write its proof file")
    with open(out_file, encoding="utf-8") as handle:
        content = handle.read()
    if "self-check OK" not in content:
        fail(f"proof file in {cwd} has unexpected content: {content!r}")
    print(f"  OK: {exe} from cwd={cwd} -> {content.strip()}", flush=True)


def main():
    portable_dir, onefile_exe, proof_root = sys.argv[1], sys.argv[2], sys.argv[3]
    portable_exe = os.path.join(portable_dir, "NitroCoreOptimizer.exe")
    for exe in (portable_exe, onefile_exe):
        level = manifest_level(exe)
        print(f"manifest level of {exe}: {level}", flush=True)
        if level == "requireAdministrator":
            fail(f"{exe} requests requireAdministrator — launchers cannot start it")

    standalone = os.path.join(proof_root, "standalone")
    bundle = os.path.join(proof_root, "bundle")
    for layout in (standalone, bundle):
        if os.path.exists(layout):
            shutil.rmtree(layout)
        shutil.copytree(portable_dir, layout)
    # Bundle-style root: other tools' files sit beside NitroCore's exe
    # and its _internal folder, exactly as the Toolkit assembles it.
    for folder in ("Charon", "Beerus", "ArgusData"):
        os.makedirs(os.path.join(bundle, folder), exist_ok=True)
    for decoy in (
        "Argus.exe",
        "TechniciansToolkit.exe",
        "README-PORTABLE-NitroCore.txt",
    ):
        with open(os.path.join(bundle, decoy), "w", encoding="utf-8") as handle:
            handle.write("decoy\n")

    run_self_check(
        os.path.join(standalone, "NitroCoreOptimizer.exe"),
        standalone,
        os.path.join(standalone, "selfcheck.out"),
    )
    run_self_check(
        os.path.join(standalone, "NitroCoreOptimizer.exe"),
        proof_root,
        os.path.join(proof_root, "selfcheck-elsewhere.out"),
    )
    run_self_check(
        os.path.join(bundle, "NitroCoreOptimizer.exe"),
        bundle,
        os.path.join(bundle, "selfcheck.out"),
    )
    print("STAGED START PROOF PASSED (runner identity)", flush=True)


if __name__ == "__main__":
    main()
