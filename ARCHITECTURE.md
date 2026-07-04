# NitroCore v1.1.0 Architecture

## Overview

Modular Windows optimizer with GUI and CLI modes. Three layers: UI (Tkinter), Modules (optimization logic), Utils (infrastructure).

## Directory Structure

```
NitroCore1.0/
├── main.py                          # Entry point
├── LICENSE                          # MIT
├── VERSION                          # 1.1.0
├── ARCHITECTURE.md                  # This file
├── CONTRIBUTING.md                  # Dev guide
├── requirements.txt                 # Dependencies
├── setup.py                         # Package config
├── source/
│   ├── gui/                         # Tkinter UI
│   │   ├── window.py
│   │   ├── tabs.py
│   │   └── ...                      # Other UI components
│   ├── modules/                     # Optimizers
│   │   ├── registry.py
│   │   ├── temp_files.py
│   │   ├── disk_cleanup.py
│   │   ├── services.py
│   │   ├── performance.py
│   │   └── async_worker.py
│   └── utils/                       # Infrastructure
│       ├── config.py
│       ├── logger.py
│       ├── profiles.py
│       └── ...
└── tests/                           # Unit tests
    ├── conftest.py
    ├── test_registry.py
    └── ...
```

## Data Flow

### GUI Mode
User clicks button → AsyncWorker runs module in thread → Callback updates UI

### CLI Mode
CLI args parsed → Module instantiated → Result printed → Exit

## Module Responsibilities

- **registry.py**: Registry tweaks, hibernation, pagefile, visual effects
- **temp_files.py**: Delete temp dirs and browser cache
- **disk_cleanup.py**: Disk usage, file pruning
- **services.py**: Stop Windows services (profile-aware)
- **performance.py**: Power plans, process priorities
- **async_worker.py**: Thread-safe async execution

## Profiles

- **Gaming**: Aggressive optimizations (disable Update, BITS, Search)
- **Cybersecurity**: Conservative (keep Update for security)

Both profile-aware via `optimize_for_profile(profile: str)` method.

## Adding a Module

1. Create `source/modules/my_optimizer.py` with class
2. Implement `optimize()` and `optimize_for_profile(profile)`
3. Add to `TabbedInterface` in `tabs.py`
4. Write tests in `tests/test_my_optimizer.py`
5. Update profiles in `utils/profiles.py` if needed

## Error Handling

All module methods return result strings (not exceptions). Exceptions caught and logged. Registry writes wrapped in try-except.

## Logging

Logs to `%APPDATA%\NitroCore\logs\` with rotation. Also displayed in GUI Status tab with color coding.

## Security

- Admin privilege check
- System restore point creation before risky ops
- Audit trail in logs
- Single-instance enforcement
- Input validation
