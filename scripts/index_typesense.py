#!/usr/bin/env python3
"""
Index products from JSONL into Typesense
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.search.typesense import TypesenseClient
from app.settings import get_settings


PRODUCTS_SCHEMA = {
    "name": "products",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "brand", "type": "string", "facet": True},
        {"name": "category", "type": "string", "facet": True},
        {"name": "sub_category", "type": "string", "optional": True, "facet": True},
        {"name": "description", "type": "string", "optional": True},
        {"name": "rating", "type": "float"},  # Required field for default sorting
        {"name": "stock", "type": "string", "optional": True},
        {"name": "selling_price", "type": "float", "optional": True}
    ],
    "default_sorting_field": "rating"
}


async def main():
    """Index products into Typesense"""
    settings = get_settings()
    
    # Initialize Typesense client
    client = TypesenseClient(
        host=getattr(settings, 'TYPESENSE_HOST', 'localhost'),
        port=getattr(settings, 'TYPESENSE_PORT', 8108),
        api_key=getattr(settings, 'TYPESENSE_API_KEY', 'xyz')
    )
    
    await client.connect()
    
    # Check if collection exists, delete if it does
    if await client.collection_exists('products'):
        print("Deleting existing collection...")
        await client.delete_collection('products')
    
    # Create collection
    print("Creating collection...")
    await client.create_collection(PRODUCTS_SCHEMA)
    
    # Load products from JSONL
    products_file = Path(__file__).parent.parent / 'products.jsonl'
    
    if not products_file.exists():
        print(f"Error: {products_file} not found")
        return
    
    print(f"Loading products from {products_file}...")
    products = []
    
    with open(products_file, 'r') as f:
        for line in f:
            if line.strip():
                product = json.loads(line)
                
                # Transform product for Typesense
                try:
                    rating_value = product.get('rating', 0.0)
                    if rating_value is None or rating_value == '':
                        rating_value = 0.0
                    rating_value = float(rating_value)
                except (ValueError, TypeError):
                    rating_value = 0.0
                
                try:
                    price_value = product.get('price', {})
                    if isinstance(price_value, dict):
                        selling_price = float(price_value.get('selling', 0.0))
                    else:
                        selling_price = float(price_value) if price_value else 0.0
                except (ValueError, TypeError):
                    selling_price = 0.0
                
                doc = {
                    'id': str(product.get('id', '')),
                    'title': str(product.get('title', '')),
                    'brand': str(product.get('brand', 'Unknown')),
                    'category': str(product.get('category', 'General')),
                    'sub_category': str(product.get('sub_category', '')),
                    'description': str(product.get('description', '')),
                    'rating': rating_value,  # Always a valid float
                    'stock': str(product.get('stock', 'unknown')),
                    'selling_price': selling_price
                }
                
                products.append(doc)
    
    print(f"Loaded {len(products)} products")
    
    # Index in batches
    batch_size = 100
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        print(f"Indexing batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}...")
        result = await client.index_documents('products', batch)
        
        if not result.get('success'):
            print(f"Error indexing batch: {result.get('error')}")
    
    print(f"Indexing complete! Total: {len(products)} products")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
