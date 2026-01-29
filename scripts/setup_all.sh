#!/bin/bash

echo "Setting up complete Walmart AI Assistant search system..."
echo "This will install Typesense + Qdrant + index all data"
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

# Step 4: Setup Qdrant (optional)
echo "Step 4: Setting up Qdrant..."
read -p "Setup Qdrant for semantic search? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./scripts/setup_qdrant.sh
    if [ $? -ne 0 ]; then
        echo "❌ Failed to setup Qdrant"
        exit 1
    fi
    
    echo ""
    echo "Step 5: Creating Qdrant collection..."
    python scripts/setup_qdrant_collection.py
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create Qdrant collection"
        exit 1
    fi
    
    echo ""
    echo "Step 6: Indexing vectors in Qdrant..."
    echo "⚠️  This requires a valid GOOGLE_API_KEY in your .env file"
    read -p "Continue with vector indexing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python scripts/index_qdrant_vectors.py
        if [ $? -ne 0 ]; then
            echo "⚠️  Vector indexing failed, but system will work with Typesense only"
        fi
    else
        echo "⚠️  Skipping vector indexing. Semantic search will not be available."
    fi
else
    echo "⚠️  Skipping Qdrant setup. Only Typesense search will be available."
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
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "- Qdrant: http://localhost:6333"
    echo "- Qdrant Dashboard: http://localhost:6333/dashboard"
fi
echo ""
echo "Start the application:"
echo "  python main.py"
echo ""
echo "Test search:"
echo "  curl -X POST http://localhost:8000/api/v1/search/ \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"query\": \"laptop\", \"user_id\": \"test\"}'"