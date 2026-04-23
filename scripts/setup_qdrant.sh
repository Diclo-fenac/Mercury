#!/bin/bash

echo "Setting up Qdrant for Mercury AI Assistant..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Stop existing Qdrant container if running
echo "Stopping existing Qdrant container..."
docker stop qdrant 2>/dev/null || true
docker rm qdrant 2>/dev/null || true

# Create Qdrant storage directory
QDRANT_STORAGE="$(realpath ~/Desktop/mercury/qdrant_sto)"
echo "Creating Qdrant storage directory at $QDRANT_STORAGE..."
mkdir -p "$QDRANT_STORAGE"

# Start Qdrant container
echo "Starting Qdrant container..."
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v "$QDRANT_STORAGE":/qdrant/storage:z \
  qdrant/qdrant:latest

# Wait for Qdrant to start
echo "Waiting for Qdrant to start..."
sleep 10

# Check if Qdrant is running
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is running successfully!"
    echo "   - REST API: http://localhost:6333"
    echo "   - gRPC API: http://localhost:6334"
    echo "   - Storage: $QDRANT_STORAGE"
    echo "   - Web UI: http://localhost:6333/dashboard"
else
    echo "❌ Failed to start Qdrant"
    echo "Check Docker logs: docker logs qdrant"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Update your .env file:"
echo "   QDRANT_HOST=localhost"
echo "   QDRANT_PORT=6333"
echo "   QDRANT_COLLECTION_NAME=products"
echo ""
echo "2. Create collection and index vectors:"
echo "   python scripts/setup_qdrant_collection.py"
echo ""
echo "3. Test the setup:"
echo "   python scripts/test_search.py"