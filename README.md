# ⚡ NitroCore — Windows System Optimizer

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NitroCore tunes up your Windows PC so games run smoother and security tools run faster.**

In plain terms: over time Windows collects junk files, runs background programs you don't need, and uses settings that favor battery life over speed. NitroCore cleans the junk, quiets the background noise, and flips the right switches — all from one simple dashboard. You don't need to know what the registry is. Just pick a profile, hit a button, and let it work.

> ### Screenshots
> _Screenshot placeholder — dashboard preview coming here._

---

## ✨ Features

- **🎮 Gaming & 🛡️ Cybersecurity profiles** — one-click optimization pipelines tuned for max FPS or for stable, patch-friendly security workloads.
- **🧹 Temp & browser cache cleanup** — clears system temp folders and Chrome/Firefox caches, with a before/after MB-freed report.
- **💽 Disk cleanup** — runs Windows' native cleanup plus DISM component cleanup; shows live drive-usage bars.
- **⚙️ Registry tuning** — disables hibernation, sets the pagefile to automatic, and trims visual effects for snappier windows.
- **🔇 Background service management** — stops and sets non-essential services (Update, BITS, Search) to manual on the Gaming profile; keeps patching alive on the Cybersecurity profile.
- **🔋 Performance tuning** — switches to the Ultimate Performance power plan and raises priority on key system processes.
- **📊 Live stats header** — CPU, RAM, disk, and power plan at a glance.
- **🛟 Restore-point safety net** — offers to create a Windows restore point before anything risky.
- **📝 Full operation logs** — every action is logged on screen and saved to `%APPDATA%\NitroCore\logs`.
- **🥚 Hidden Fallout mode** — click the title 7 times. You'll see.

---

## 📥 Installation

### Option A — Ready-to-run .exe (easiest)

1. Download `NitroCoreOptimizer.exe` from the [Releases](https://github.com/TheRealJesusTheHacker/NitroCore1.0/releases) page.
2. Right-click it → **Run as administrator**.
3. That's it.

### Option B — From source

Requires Python 3.9+ on Windows.

```bash
git clone https://github.com/TheRealJesusTheHacker/NitroCore1.0.git
cd NitroCore1.0/NitroCore
pip install -r requirements.txt
```

Then **run as administrator**:

```bash
python main.py
```

> The app must run elevated — it can't tune the system without admin rights. It will tell you if you forgot.

### Building the .exe yourself

```bash
pip install pyinstaller
pyinstaller nitrocore.spec
```

The build requests admin rights automatically (`uac_admin`), so the .exe self-elevates.

---

## 🕹️ Usage walkthrough

1. **Launch as administrator.** If you're not elevated, NitroCore will say so and exit.
2. **Pick your profile** at the top:
   - **Gaming** (orange) — aggressive: max performance, background services trimmed.
   - **Cybersecurity** (teal) — stable: visual tweaks and cleanup, Windows Update stays on.
3. **Explore the tabs** — Registry, Temp Files, Disk Cleanup, Services, Performance, Status. Each tab explains what it does and shows a risk level.
4. **Run something.** You can run individual actions, or hit **Run All** to execute the full pipeline for your profile.
5. **Say yes to the restore point.** Before anything that changes system settings, NitroCore asks if you want a restore point first. Always a good idea.
6. **Watch the Status tab.** Every step logs what it did, how long it took, and how much space it freed.

### 👁️ Preview mode (dry run)

Nervous about what it'll change? Turn on **"Preview only — don't change anything"** next to Run All, or launch with:

```bash
python main.py --dry-run
```

NitroCore will scan everything and print exactly what it *would* do — every registry value, every service change, every file it would delete — then finish with **"PREVIEW ONLY — no changes were made."** Nothing is modified, no restore point is created, and the preview doesn't even need admin rights.

---

## 🛟 Safety notes

- **Admin rights are required.** The app exits with a clear message if you launch it without them.
- **Restore points are offered, not forced.** Before registry edits, service changes, or disk cleanup, you'll get a dialog: _Create & Continue_, _Skip_, or _Cancel_. Nothing irreversible happens without you knowing.
- **Your personal files are never touched** — except Downloads cleanup, which only removes files **older than 30 days** and asks you to confirm first.
- **Logs live at** `%APPDATA%\NitroCore\logs\nitrocore.log` — if anything looks off, the full trail is there.

---

## ❓ FAQ

**Is NitroCore safe to run?**
Yes for normal use. It only touches temp files, caches, visual settings, power plans, and a small list of well-known background services. Risky steps are labeled by risk level and offer a restore point first.

**Will it delete my documents, photos, or game saves?**
No. Cleanup targets system temp folders and browser caches only. The one exception — old Downloads — asks for confirmation and only touches files 30+ days old.

**Why does it need administrator?**
Windows won't let any program change power plans, services, or system settings without admin rights. No admin = no tuning.

**Which Windows versions work?**
Windows 10 and 11, 64-bit.

**Something broke — how do I undo it?**
Boot into System Restore and roll back to the restore point NitroCore offered to create. That's exactly what it's for.

**My antivirus flagged it. Is it a virus?**
No. Optimizers that edit the registry and manage services trip heuristic scanners all the time. NitroCore is open source — every line is right here for you (or anyone) to read.

**Does it phone home or collect data?**
No. Everything runs locally on your machine. Logs stay on your disk.

---

## 📄 License

MIT — do what you want, just don't blame me. See [LICENSE](LICENSE).

---

_Built by [JesusTheHacker](https://github.com/TheRealJesusTheHacker). Tune your rig. Stay dangerous._
