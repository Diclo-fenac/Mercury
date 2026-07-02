#!/bin/bash

echo "Setting up complete Mercury AI Assistant search system..."
echo "This will install Typesense + index all data"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Step 1: Install dependencies
echo "Step 1: Installing Python dependencies..."
./scripts/install_dependencies.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""

# Step 2: Setup Typesense
echo "Step 2: Setting up Typesense..."
./scripts/setup_typesense.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to setup Typesense"
    exit 1
fi

echo ""

# Step 3: Index Typesense
echo "Step 3: Indexing products in Typesense..."
python scripts/index_typesense.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to index Typesense"
    exit 1
fi

echo ""



# Step 7: Test system
echo "Final Step: Testing the system..."
python scripts/test_search.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Services running:"
echo "- Typesense: http://localhost:8108"

echo "Start the application:"
echo "  python main.py"
echo ""
echo "Test search:"
echo "  curl -X POST http://localhost:8000/api/v1/search/ \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"query\": \"laptop\", \"user_id\": \"test\"}'"