# Contributing to NitroCore v1.1.0

## Setup

```bash
git clone https://github.com/thedarkonejesus/NitroCore1.0.git
cd NitroCore1.0
pip install -r requirements-dev.txt
python main.py
```

## Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Follow code style: black, type hints, docstrings
3. Add tests: `pytest tests/`
4. Format: `black source/` and `pylint source/`
5. Commit: `git commit -m "Feature: Description"`
6. Push and open PR

## Code Style

```python
def optimize_for_profile(self, profile: str) -> str:
    """Apply optimizations scoped to profile.
    
    Args:
        profile: 'gaming' or 'cybersecurity'
    
    Returns:
        Status message
    """
    try:
        result = self._do_optimization()
        return f"Success: {result}"
    except Exception as e:
        logger.error(f"Failed: {e}")
        return f"Error: {e}"
```

## Testing

```bash
pytest tests/ -v --cov=source
```

Mock Windows APIs to avoid system modifications:

```python
from unittest.mock import patch

@patch('winreg.CreateKeyEx')
def test_registry_write(mock_create):
    mock_create.return_value = MagicMock()
    # Your test
```

## Adding a Module

### 1. Create module
```python
# source/modules/my_optimizer.py
class MyOptimizer:
    def optimize(self) -> str:
        """Run optimization."""
        return "Success: ..."
    
    def optimize_for_profile(self, profile: str) -> str:
        if profile == "gaming":
            # Aggressive
        else:
            # Conservative
        return self.optimize()
```

### 2. Add to GUI (tabs.py)
```python
from source.modules.my_optimizer import MyOptimizer

class TabbedInterface:
    def __init__(self, ...):
        self.my_opt = MyOptimizer()
    
    def _build_my_tab(self):
        panel = self._make_tab_panel("my_tab")
        self._add_tab_header(panel, "My Opt", "Description", risk="Low")
        self._add_action_button(panel, "Run", self._run_my_opt)
    
    def _run_my_opt(self):
        self._run_async("My Opt", self.my_opt.optimize)
```

### 3. Write tests
```python
# tests/test_my_optimizer.py
from source.modules.my_optimizer import MyOptimizer

def test_optimize():
    opt = MyOptimizer()
    result = opt.optimize()
    assert isinstance(result, str)
```

## CI/CD

GitHub Actions runs on push:
- `tests.yml`: Pylint, Black, Pytest (Python 3.8-3.11)
- `release.yml`: PyInstaller build on tag

## Release

Maintainers only:
1. Update VERSION file
2. Update main.py version
3. `git tag -a v1.1.0`
4. `git push origin v1.1.0`
5. GitHub Actions builds .exe automatically

## Questions?

Open an issue or discussion. We're here to help!
