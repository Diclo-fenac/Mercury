#!/bin/bash

echo "Setting up Typesense for Walmart AI Assistant..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Stop existing Typesense container if running
echo "Stopping existing Typesense container..."
docker stop typesense 2>/dev/null || true
docker rm typesense 2>/dev/null || true

# Create Typesense data directory
echo "Creating Typesense data directory..."
mkdir -p ~/typesense-data

# Start Typesense container
echo "Starting Typesense container..."
docker run -d \
  --name typesense \
  -p 8108:8108 \
  -v ~/typesense-data:/data \
  -e TYPESENSE_DATA_DIR=/data \
  -e TYPESENSE_API_KEY=xyz \
  -e TYPESENSE_ENABLE_CORS=true \
  typesense/typesense:29.0

# Wait for Typesense to start
echo "Waiting for Typesense to start..."
sleep 5

# Check if Typesense is running
if curl -s http://localhost:8108/health > /dev/null; then
    echo "✅ Typesense is running successfully!"
    echo "   - URL: http://localhost:8108"
    echo "   - API Key: xyz"
    echo "   - Data directory: ~/typesense-data"
else
    echo "❌ Failed to start Typesense"
    echo "Check Docker logs: docker logs typesense"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Add to your .env file:"
echo "   TYPESENSE_HOST=localhost"
echo "   TYPESENSE_PORT=8108"
echo "   TYPESENSE_API_KEY=xyz"
echo ""
echo "2. Index products:"
echo "   python scripts/index_typesense.py"
echo ""
echo "3. Start the application:"
echo "   python main.py"
