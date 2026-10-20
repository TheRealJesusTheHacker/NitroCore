"""TEMPORARY field-diagnostic probe (removed after the investigation).

Attempts launcher-style spawns (subprocess.Popen == CreateProcess,
exactly what the Technician's Toolkit launcher does) of the shipped
NitroCoreOptimizer.exe in standalone and bundle-style layouts and
records the exact outcome of each attempt as JSON.
"""

import ctypes
import json
import os
import subprocess
import sys


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return None


out = {"user": os.environ.get("USERNAME"), "is_admin": is_admin(), "results": {}}


def attempt(label, argv, cwd):
    try:
        p = subprocess.Popen(argv, cwd=cwd)
        rec = {"spawn": "OK", "pid": p.pid}
        try:
            p.wait(timeout=3)
            rec["early_exit"] = p.returncode
        except subprocess.TimeoutExpired:
            rec["early_exit"] = "still running after 3s"
            p.kill()
        out["results"][label] = rec
    except OSError as e:
        out["results"][label] = {
            "spawn": "OSError",
            "winerror": getattr(e, "winerror", None),
            "errno": e.errno,
            "str": str(e),
        }


EXE_S = r"C:\diag\standalone\NitroCoreOptimizer.exe"
EXE_B = r"C:\diag\bundle\NitroCoreOptimizer.exe"

attempt("standalone_cwd_exedir", [EXE_S], r"C:\diag\standalone")
attempt("standalone_cwd_elsewhere", [EXE_S], r"C:\diag")
attempt("bundle_cwd_root", [EXE_B], r"C:\diag\bundle")
attempt("control_whoami", [r"C:\Windows\System32\whoami.exe"], r"C:\diag")

dest = sys.argv[1] if len(sys.argv) > 1 else r"C:\diag\result.json"
with open(dest, "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
