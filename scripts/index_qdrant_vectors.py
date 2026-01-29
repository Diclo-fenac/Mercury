#!/usr/bin/env python3
"""
Index product vectors into Qdrant
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.vector.qdrant import QdrantClient
from app.addons.embeddings.gemini import GeminiEmbeddings
from app.settings import get_settings


async def main():
    """Index product vectors into Qdrant"""
    print("Indexing product vectors into Qdrant...")
    
    settings = get_settings()
    
    # Initialize clients
    qdrant = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION_NAME
    )
    
    embeddings = GeminiEmbeddings(api_key=settings.GOOGLE_API_KEY)
    
    try:
        # Connect to services
        await qdrant.connect()
        await embeddings.initialize()
        print("✅ Connected to Qdrant and Gemini")
        
        # Check if collection exists
        collection_name = settings.QDRANT_COLLECTION_NAME
        if not await qdrant.collection_exists(collection_name):
            print(f"❌ Collection '{collection_name}' does not exist")
            print("Run: python scripts/setup_qdrant_collection.py")
            return
        
        # Load products from JSONL
        products_file = Path(__file__).parent.parent / 'products.jsonl'
        
        if not products_file.exists():
            print(f"❌ Products file not found: {products_file}")
            return
        
        print(f"Loading products from {products_file}...")
        products = []
        
        with open(products_file, 'r') as f:
            for line in f:
                if line.strip():
                    product = json.loads(line)
                    products.append(product)
        
        print(f"Loaded {len(products)} products")
        
        # Process products in batches
        batch_size = 10  # Small batches for embedding API limits
        total_indexed = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(products) + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches}...")
            
            # Prepare points for this batch
            points = []
            
            for product in batch:
                # Create text for embedding
                text_parts = []
                if product.get('title'):
                    text_parts.append(product['title'])
                if product.get('description'):
                    text_parts.append(product['description'])
                if product.get('brand'):
                    text_parts.append(f"Brand: {product['brand']}")
                if product.get('category'):
                    text_parts.append(f"Category: {product['category']}")
                
                text = " ".join(text_parts)
                
                if not text:
                    continue
                
                # Generate embedding
                try:
                    vector = await embeddings.embed_text(text)
                    if not vector:
                        print(f"⚠️  Failed to generate embedding for product {product.get('id')}")
                        continue
                    
                    # Prepare point
                    point = {
                        'id': int(product.get('id', 0)) if str(product.get('id', '')).isdigit() else hash(product.get('id', '')) % 2147483647,
                        'vector': vector,
                        'payload': {
                            'product_id': str(product.get('id', '')),
                            'title': product.get('title', ''),
                            'brand': product.get('brand', ''),
                            'category': product.get('category', ''),
                            'description': product.get('description', ''),
                            'rating': float(product.get('rating', 0.0)),
                            'price': float(product.get('price', {}).get('selling', 0.0)) if isinstance(product.get('price'), dict) else float(product.get('price', 0.0))
                        }
                    }
                    
                    points.append(point)
                    
                except Exception as e:
                    print(f"⚠️  Error processing product {product.get('id')}: {e}")
                    continue
            
            # Index batch
            if points:
                success = await qdrant.upsert_points(collection_name, points)
                if success:
                    total_indexed += len(points)
                    print(f"✅ Indexed {len(points)} vectors (Total: {total_indexed})")
                else:
                    print(f"❌ Failed to index batch {batch_num}")
            
            # Small delay to respect API limits
            await asyncio.sleep(1)
        
        print(f"\n✅ Indexing complete! Total vectors indexed: {total_indexed}")
        
        # Get collection stats
        stats = await qdrant.get_collection_stats(collection_name)
        if stats:
            print(f"Collection stats:")
            print(f"   - Total points: {stats.get('total_points', 0)}")
            print(f"   - Total vectors: {stats.get('total_vectors', 0)}")
        
        await qdrant.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print("")
    print("Next steps:")
    print("1. Test the setup:")
    print("   python scripts/test_search.py")
    print("")
    print("2. Start the application:")
    print("   python main.py")


if __name__ == "__main__":
    asyncio.run(main())