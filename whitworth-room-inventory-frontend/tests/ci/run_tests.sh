#!/usr/bin/env bash
set -euo pipefail

echo "=== Detecting repo language and running tests ==="

# Detect what languages are needed by checking for project files
HAS_GO=false
HAS_PYTHON=false
HAS_NODE=false

if [ -f "go.mod" ]; then
    HAS_GO=true
elif ls *.py 1> /dev/null 2>&1 || compgen -G "./tests/*.py" > /dev/null 2>&1 || [ -f "pyproject.toml" ]; then
    HAS_PYTHON=true
elif [ -f "package.json" ]; then
    HAS_NODE=true
fi

# Install only what's needed
echo "=== Installing required languages ==="
if [ "$HAS_GO" = true ]; then
    echo "Installing Go..."
    apk add --no-cache go
elif [ "$HAS_PYTHON" = true ]; then
    echo "Installing Python..."
    apk add --no-cache python3 py3-pip py3-virtualenv nodejs npm
elif [ "$HAS_NODE" = true ]; then
    echo "Installing Node.js..."
    apk add --no-cache nodejs npm
fi

echo "=== Running tests ==="

# Go tests
if [ "$HAS_GO" = true ]; then
    echo "Running Go tests..."
    go mod tidy || true
    go test ./...
# Python tests
elif [ "$HAS_PYTHON" = true ]; then
    echo "Running Python tests..."
    python3 -m venv venv || virtualenv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install pytest
    pip install requests
    # frontened installs
    npm install express
    # upgrade eventlet to fix Python 3.12 compatibility due to alpine:3.21 specified in pipeline
    if grep -q "eventlet" requirements.txt 2>/dev/null; then
        pip install "eventlet>=0.35.0"
    fi
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    fi
    if compgen -G "tests/*.py" > /dev/null 2>&1; then
        pytest -q tests/*.py
    else
        echo "No Python test files found, skipping pytest"
    fi
# Node.js tests
elif [ "$HAS_NODE" = true ]; then
    echo "Running Node.js tests..."
    npm install jest supertest
    npm test || npx jest --silent tests/*.js
fi

echo "=== All tests completed ==="