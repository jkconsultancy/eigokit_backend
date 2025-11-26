#!/bin/bash
# Installation script for EigoKit Backend
# Handles Python 3.13 compatibility issues

set -e

echo "EigoKit Backend - Installation Script"
echo "======================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "Detected Python version: $(python3 --version)"

# Check if Rust is installed (needed for Python 3.13)
if ! command -v rustc &> /dev/null; then
    echo ""
    echo "⚠️  WARNING: Rust compiler not found!"
    echo "Python 3.13 requires Rust to build some packages (like pydantic-core)."
    echo ""
    echo "Options:"
    echo "1. Install Rust: brew install rust (macOS) or visit https://rustup.rs/"
    echo "2. Use Python 3.11 or 3.12 instead"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Upgrade pip and build tools
echo ""
echo "📦 Upgrading pip and build tools..."
python3 -m pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
if python3 -c "import sys; exit(0 if sys.version_info < (3, 13) else 1)"; then
    # Python < 3.13 - normal install
    pip install -r requirements.txt
else
    # Python 3.13+ - try with pre-built wheels first, fallback to source
    echo "Python 3.13 detected - attempting installation..."
    pip install --upgrade pip setuptools wheel || true
    pip install -r requirements.txt || {
        echo ""
        echo "❌ Installation failed. This is likely due to missing Rust compiler."
        echo ""
        echo "To fix this:"
        echo "1. Install Rust: brew install rust (macOS) or visit https://rustup.rs/"
        echo "2. Then run: pip install -r requirements.txt"
        echo ""
        echo "Or use Python 3.11/3.12 instead:"
        echo "  python3.12 -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    }
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Create a .env file: cp .env.example .env"
echo "2. Fill in your Supabase credentials"
echo "3. Run the server: uvicorn app.main:app --reload"

