"""Standard-user half of the staged start proof (release pipeline).

The release workflow starts this script AS a freshly created
non-administrator user (Start-Process -Credential) so the spawn it
performs happens under the same kind of token that hit WinError 740
in the field. It starts the staged NitroCoreOptimizer.exe exactly
the way the Technician's Toolkit launcher does — subprocess
(CreateProcess), working directory at the layout root — and writes
a JSON verdict the workflow step asserts on:

    {"user_is_admin": false, "spawn": "OK", ...}

Modes:
    selfcheck — start with --self-check; verdict carries the exit
                code and whether the proof file was written.
    plain     — start with no arguments (the real GUI path); the
                verdict records only that the spawn was accepted
                and the process was alive, then the process tree
                is stopped. (The program immediately asks for
                elevation, which nobody answers on a CI runner;
                spawn acceptance is the field failure's regression
                point, and it is what is asserted.)

Usage:
    python tools/staged_start_spawner.py <exe> <verdict_json> <mode> <selfcheck_out>
"""

import ctypes
import json
import os
import subprocess
import sys
import time


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return None


def main():
    exe, verdict_path, mode, selfcheck_out = sys.argv[1:5]
    verdict = {"user_is_admin": is_admin(), "mode": mode}
    cwd = os.path.dirname(os.path.abspath(exe))
    try:
        if mode == "selfcheck":
            env = dict(os.environ)
            env["NITROCORE_SELF_CHECK_OUT"] = selfcheck_out
            proc = subprocess.run(
                [exe, "--self-check"],
                cwd=cwd,
                env=env,
                timeout=180,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            verdict.update(
                spawn="OK",
                rc=proc.returncode,
                out_exists=os.path.isfile(selfcheck_out),
            )
        else:
            proc = subprocess.Popen([exe], cwd=cwd)
            verdict.update(spawn="OK", pid=proc.pid)
            time.sleep(2)
            verdict["alive_after_2s"] = proc.poll() is None
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
    except OSError as exc:
        verdict.update(
            spawn="OSError",
            winerror=getattr(exc, "winerror", None),
            str=str(exc),
        )
    with open(verdict_path, "w", encoding="utf-8") as handle:
        json.dump(verdict, handle, indent=1)
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
