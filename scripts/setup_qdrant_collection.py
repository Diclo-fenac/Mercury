#!/usr/bin/env python3
"""
Setup Qdrant collection for products
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.vector.qdrant import QdrantClient
from app.settings import get_settings


async def main():
    """Setup Qdrant collection"""
    print("Setting up Qdrant collection for products...")
    
    settings = get_settings()
    
    # Initialize Qdrant client
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION_NAME
    )
    
    try:
        # Connect to Qdrant
        await client.connect()
        print("✅ Connected to Qdrant")
        
        # Check if collection exists
        collection_name = settings.QDRANT_COLLECTION_NAME
        exists = await client.collection_exists(collection_name)
        
        if exists:
            print(f"⚠️  Collection '{collection_name}' already exists")
            response = input("Delete and recreate? (y/N): ")
            if response.lower() == 'y':
                await client.delete_collection(collection_name)
                print(f"✅ Deleted existing collection '{collection_name}'")
            else:
                print("Keeping existing collection")
                await client.close()
                return
        
        # Create collection with 768 dimensions (for Gemini embeddings)
        success = await client.create_collection(
            collection_name=collection_name,
            vector_size=768,  # Gemini embedding size
            distance="Cosine"
        )
        
        if success:
            print(f"✅ Created collection '{collection_name}' with 768-dimensional vectors")
            
            # Get collection info
            info = await client.get_collection_info(collection_name)
            if info:
                print(f"   - Points count: {info.get('points_count', 0)}")
                print(f"   - Vectors count: {info.get('vectors_count', 0)}")
        else:
            print(f"❌ Failed to create collection '{collection_name}'")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print("")
    print("Next steps:")
    print("1. Index product vectors:")
    print("   python scripts/index_qdrant_vectors.py")
    print("")
    print("2. Test the setup:")
    print("   python scripts/test_search.py")


if __name__ == "__main__":
    asyncio.run(main())