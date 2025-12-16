#!/bin/bash
# Setup script for Snort3-AI-Ops development environment

set -e

echo "=========================================="
echo "Snort3-AI-Ops Development Setup"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data logs models reports pcaps

# Copy example config if config doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config/config.example.yaml config/config.yaml
else
    echo "config.yaml already exists"
fi

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
else
    echo ".env already exists"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit .env file and add your API keys"
echo "3. Edit config/config.yaml as needed"
echo "4. Run tests: pytest tests/"
echo "5. Validate config: python main.py validate"
echo "6. Start the engine: python main.py start"
echo ""
echo "For more information, see README.md"
echo ""
