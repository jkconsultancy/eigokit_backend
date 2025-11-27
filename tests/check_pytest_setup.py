#!/usr/bin/env python3
"""
Diagnostic script to check pytest setup and available fixtures.
Run this to diagnose why mocker fixture might not be available.
"""
import sys
import subprocess

def check_environment():
    """Check the Python environment and pytest setup."""
    print("=" * 60)
    print("PYTEST ENVIRONMENT DIAGNOSTICS")
    print("=" * 60)
    
    print(f"\n1. Python executable: {sys.executable}")
    print(f"2. Python version: {sys.version}")
    
    # Check if pytest-mock is installed
    try:
        import pytest_mock
        print(f"3. pytest-mock: INSTALLED at {pytest_mock.__file__}")
    except ImportError:
        print("3. pytest-mock: NOT INSTALLED")
        print("   ERROR: pytest-mock must be installed for tests to work")
        return False
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"4. pytest: INSTALLED (version {pytest.__version__})")
    except ImportError:
        print("4. pytest: NOT INSTALLED")
        return False
    
    # Try to get available fixtures
    print("\n5. Checking available fixtures...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--fixtures", "tests/check_pytest_setup.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "mocker" in result.stdout:
            print("   ✓ mocker fixture is available")
        else:
            print("   ✗ mocker fixture NOT found in available fixtures")
            print("\n   Available fixtures:")
            for line in result.stdout.split('\n'):
                if 'fixture' in line.lower() or '--' in line:
                    print(f"     {line[:80]}")
    except Exception as e:
        print(f"   Could not check fixtures: {e}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    print("Make sure you're running tests from within the virtual environment:")
    print("  cd eigokit_backend")
    print("  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
    print("  python -m pytest tests/ -v")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    check_environment()

