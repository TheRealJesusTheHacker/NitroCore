# ⚡ NitroCore — app source

This folder is the NitroCore application itself.

👉 **Full documentation, features, install steps, safety notes, and FAQ are in the [main README](../README.md).**

## Quick start (from source)

Requires Python 3.9+ on Windows. Run from this folder **as administrator**:

```bash
pip install -r requirements.txt
python main.py
```

Without admin rights, the app will tell you and exit — it can't tune the system otherwise.

## Layout

- `main.py` — entry point, main window
- `source/gui/` — dashboard UI (tabs, widgets, layout)
- `source/modules/` — optimization modules (registry, temp, disk, services, performance)
- `source/utils/` — logging, restore points, platform helpers, async worker
- `assets/` — icons
