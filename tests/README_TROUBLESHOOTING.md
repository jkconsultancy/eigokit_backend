# Troubleshooting Test Failures

## Error: `fixture 'mocker' not found`

This error occurs when `pytest-mock` is not installed or not being loaded by pytest.

### Root Cause

The `mocker` fixture is provided by the `pytest-mock` plugin. If this plugin is not installed or not being discovered by pytest, the fixture will not be available.

### Solution

1. **Ensure you're in the virtual environment:**
   ```bash
   cd eigokit_backend
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Verify pytest-mock is installed:**
   ```bash
   pip list | grep pytest-mock
   # Should show: pytest-mock 3.15.1 (or similar)
   ```

3. **If not installed, install it:**
   ```bash
   pip install -r requirements.txt
   # or
   pip install pytest-mock
   ```

4. **Run tests using the venv Python:**
   ```bash
   python -m pytest tests/ -v
   # NOT: pytest tests/ -v (might use system pytest)
   ```

5. **Verify the mocker fixture is available:**
   ```bash
   python -m pytest --fixtures tests/ | grep mocker
   # Should show: mocker -- .../pytest_mock/plugin.py
   ```

### Diagnostic Script

Run the diagnostic script to check your environment:
```bash
python tests/check_pytest_setup.py
```

### Common Issues

- **Running pytest from outside venv**: Always activate the virtual environment first
- **Using system pytest**: Use `python -m pytest` instead of just `pytest`
- **pytest-mock not in requirements**: It's in `requirements.txt`, so `pip install -r requirements.txt` should install it
- **Different Python environment**: Make sure `which python` shows the venv Python path

