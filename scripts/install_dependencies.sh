#!/bin/bash

echo "Installing dependencies for Mercury AI Assistant..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install Python and pip first."
    exit 1
fi

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  No virtual environment detected. Consider using one:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # Linux/Mac"
    echo "   # or"
    echo "   venv\\Scripts\\activate     # Windows"
    echo ""
    read -p "Continue without virtual environment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Check installation
echo ""
echo "Checking installations..."

# Check key packages
packages=("fastapi" "typesense" "google-generativeai")
all_good=true

for package in "${packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package - Installed"
    else
        echo "❌ $package - Failed to install"
        all_good=false
    fi
done

if [ "$all_good" = true ]; then
    echo ""
    echo "✅ All dependencies installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Setup Typesense: ./scripts/setup_typesense.sh"
    echo "2. Test system: python scripts/test_search.py"
    echo "3. Index products: python scripts/index_typesense.py"
    echo "4. Start app: python main.py"
else
    echo ""
    echo "❌ Some packages failed to install. Check the errors above."
    echo "You may need to:"
    echo "- Update pip: pip install --upgrade pip"
    echo "- Install system dependencies"
    echo "- Check your Python version (3.8+ required)"
fi