#!/usr/bin/env python3
"""
Product Data Seeding Script
Seeds real product data into Firestore and Qdrant for testing
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.db.firestore import FirestoreClient
from app.infrastructure.vector.qdrant import QdrantClient
from app.infrastructure.id_generator import IDGenerator
from app.utils.logger import get_logger

logger = get_logger("seed_products")

# Sample product data
SAMPLE_PRODUCTS = [
    {
        "name": "iPhone 15 Pro Max",
        "description": "Latest Apple iPhone with A17 Pro chip, titanium design, and advanced camera system",
        "category": "Electronics",
        "subcategory": "Smartphones",
        "brand": "Apple",
        "price": 1199.99,
        "original_price": 1199.99,
        "discount_percentage": 0,
        "rating": 4.8,
        "review_count": 2847,
        "in_stock": True,
        "stock_quantity": 150,
        "tags": ["smartphone", "apple", "iphone", "premium", "5g"],
        "features": ["A17 Pro chip", "Titanium design", "48MP camera", "5G connectivity"],
        "image_url": "https://example.com/iphone15pro.jpg"
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "description": "Premium Android smartphone with S Pen, 200MP camera, and AI features",
        "category": "Electronics",
        "subcategory": "Smartphones", 
        "brand": "Samsung",
        "price": 1099.99,
        "original_price": 1199.99,
        "discount_percentage": 8.3,
        "rating": 4.7,
        "review_count": 1923,
        "in_stock": True,
        "stock_quantity": 89,
        "tags": ["smartphone", "samsung", "galaxy", "s-pen", "android"],
        "features": ["200MP camera", "S Pen included", "AI photo editing", "120Hz display"],
        "image_url": "https://example.com/galaxys24ultra.jpg"
    },
    {
        "name": "MacBook Air M3",
        "description": "Ultra-thin laptop with M3 chip, 18-hour battery life, and Liquid Retina display",
        "category": "Electronics",
        "subcategory": "Laptops",
        "brand": "Apple",
        "price": 1099.00,
        "original_price": 1199.00,
        "discount_percentage": 8.3,
        "rating": 4.9,
        "review_count": 1456,
        "in_stock": True,
        "stock_quantity": 67,
        "tags": ["laptop", "apple", "macbook", "m3", "ultrabook"],
        "features": ["M3 chip", "18-hour battery", "Liquid Retina display", "1080p camera"],
        "image_url": "https://example.com/macbookairm3.jpg"
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "description": "Industry-leading noise canceling wireless headphones with 30-hour battery",
        "category": "Electronics",
        "subcategory": "Audio",
        "brand": "Sony",
        "price": 349.99,
        "original_price": 399.99,
        "discount_percentage": 12.5,
        "rating": 4.6,
        "review_count": 3421,
        "in_stock": True,
        "stock_quantity": 234,
        "tags": ["headphones", "sony", "wireless", "noise-canceling", "bluetooth"],
        "features": ["Active noise canceling", "30-hour battery", "Quick charge", "Multipoint connection"],
        "image_url": "https://example.com/sonywh1000xm5.jpg"
    },
    {
        "name": "Nike Air Max 270",
        "description": "Comfortable running shoes with Max Air unit and breathable mesh upper",
        "category": "Fashion",
        "subcategory": "Shoes",
        "brand": "Nike",
        "price": 129.99,
        "original_price": 150.00,
        "discount_percentage": 13.3,
        "rating": 4.4,
        "review_count": 892,
        "in_stock": True,
        "stock_quantity": 156,
        "tags": ["shoes", "nike", "running", "air-max", "sneakers"],
        "features": ["Max Air cushioning", "Breathable mesh", "Rubber outsole", "Lightweight"],
        "image_url": "https://example.com/nikeairmax270.jpg"
    },
    {
        "name": "Instant Pot Duo 7-in-1",
        "description": "Multi-use pressure cooker that replaces 7 kitchen appliances",
        "category": "Home & Kitchen",
        "subcategory": "Appliances",
        "brand": "Instant Pot",
        "price": 79.99,
        "original_price": 99.99,
        "discount_percentage": 20.0,
        "rating": 4.7,
        "review_count": 15678,
        "in_stock": True,
        "stock_quantity": 89,
        "tags": ["kitchen", "pressure-cooker", "instant-pot", "appliance", "cooking"],
        "features": ["7-in-1 functionality", "6-quart capacity", "14 programs", "Stainless steel"],
        "image_url": "https://example.com/instantpotduo.jpg"
    },
    {
        "name": "Levi's 501 Original Jeans",
        "description": "Classic straight-leg jeans with button fly and iconic styling",
        "category": "Fashion",
        "subcategory": "Clothing",
        "brand": "Levi's",
        "price": 59.99,
        "original_price": 69.99,
        "discount_percentage": 14.3,
        "rating": 4.3,
        "review_count": 2341,
        "in_stock": True,
        "stock_quantity": 278,
        "tags": ["jeans", "levis", "denim", "classic", "501"],
        "features": ["100% cotton", "Button fly", "Straight leg", "Classic fit"],
        "image_url": "https://example.com/levis501.jpg"
    },
    {
        "name": "Kindle Paperwhite",
        "description": "Waterproof e-reader with 6.8-inch display and adjustable warm light",
        "category": "Electronics",
        "subcategory": "E-readers",
        "brand": "Amazon",
        "price": 139.99,
        "original_price": 139.99,
        "discount_percentage": 0,
        "rating": 4.6,
        "review_count": 8934,
        "in_stock": True,
        "stock_quantity": 445,
        "tags": ["e-reader", "kindle", "amazon", "books", "waterproof"],
        "features": ["6.8-inch display", "Waterproof", "Adjustable warm light", "Weeks of battery"],
        "image_url": "https://example.com/kindlepaperwhite.jpg"
    },
    {
        "name": "Dyson V15 Detect Vacuum",
        "description": "Cordless vacuum with laser dust detection and powerful suction",
        "category": "Home & Kitchen",
        "subcategory": "Appliances",
        "brand": "Dyson",
        "price": 649.99,
        "original_price": 749.99,
        "discount_percentage": 13.3,
        "rating": 4.5,
        "review_count": 1567,
        "in_stock": True,
        "stock_quantity": 34,
        "tags": ["vacuum", "dyson", "cordless", "laser", "cleaning"],
        "features": ["Laser dust detection", "60-minute runtime", "5-stage filtration", "LCD screen"],
        "image_url": "https://example.com/dysonv15.jpg"
    },
    {
        "name": "Fitbit Charge 6",
        "description": "Advanced fitness tracker with GPS, heart rate monitoring, and 7-day battery",
        "category": "Electronics",
        "subcategory": "Wearables",
        "brand": "Fitbit",
        "price": 159.99,
        "original_price": 199.99,
        "discount_percentage": 20.0,
        "rating": 4.2,
        "review_count": 743,
        "in_stock": True,
        "stock_quantity": 123,
        "tags": ["fitness", "tracker", "fitbit", "gps", "health"],
        "features": ["Built-in GPS", "Heart rate monitoring", "7-day battery", "Sleep tracking"],
        "image_url": "https://example.com/fitbitcharge6.jpg"
    }
]

class ProductSeeder:
    """Seeds product data into Firestore and Qdrant"""
    
    def __init__(self):
        self.firestore = None
        self.qdrant = None
        self.id_gen = IDGenerator()
    
    async def initialize_services(self):
        """Initialize database services"""
        try:
            # Initialize Firestore
            self.firestore = FirestoreClient(
                project_id=os.getenv('FIREBASE_PROJECT_ID'),
                credentials_path=os.getenv('FIREBASE_CREDENTIALS_PATH', 'config/firebase-config.json')
            )
            await self.firestore.connect()
            logger.info("✅ Firestore connected")
            
            # Initialize Qdrant
            self.qdrant = QdrantClient(
                host=os.getenv('QDRANT_HOST', 'localhost'),
                port=int(os.getenv('QDRANT_PORT', 6333)),
                api_key=os.getenv('QDRANT_API_KEY')
            )
            await self.qdrant.connect()
            logger.info("✅ Qdrant connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    async def seed_products(self, overwrite: bool = False):
        """Seed products into both Firestore and Qdrant"""
        try:
            logger.info("🌱 Starting product seeding...")
            
            # Check if products already exist
            if not overwrite:
                existing = await self.firestore.query_collection('products', limit=1)
                if existing:
                    logger.info("Products already exist. Use --overwrite to replace them.")
                    return
            
            seeded_count = 0
            
            for product_data in SAMPLE_PRODUCTS:
                try:
                    # Generate product ID
                    product_id = self.id_gen.product_id()
                    
                    # Add metadata
                    product_data.update({
                        'id': product_id,
                        'created_at': self.id_gen.timestamp(),
                        'updated_at': self.id_gen.timestamp(),
                        'is_active': True,
                        'view_count': 0,
                        'purchase_count': 0
                    })
                    
                    # Save to Firestore
                    success = await self.firestore.set_document('products', product_id, product_data)
                    if not success:
                        logger.error(f"Failed to save product {product_data['name']} to Firestore")
                        continue
                    
                    # Create vector for Qdrant
                    text_content = f"{product_data['name']} {product_data['description']} {product_data['brand']} {' '.join(product_data['tags'])}"
                    
                    # Generate simple vector (in real implementation, use embedding model)
                    vector = self._generate_simple_vector(text_content)
                    
                    # Save to Qdrant
                    qdrant_success = await self.qdrant.upsert_points(
                        collection_name='products',
                        points=[{
                            'id': product_id,
                            'vector': vector,
                            'payload': {
                                'name': product_data['name'],
                                'category': product_data['category'],
                                'brand': product_data['brand'],
                                'price': product_data['price'],
                                'rating': product_data['rating']
                            }
                        }]
                    )
                    
                    if qdrant_success:
                        seeded_count += 1
                        logger.info(f"✅ Seeded: {product_data['name']}")
                    else:
                        logger.error(f"Failed to save product {product_data['name']} to Qdrant")
                
                except Exception as e:
                    logger.error(f"Failed to seed product {product_data.get('name', 'unknown')}: {e}")
                    continue
            
            logger.info(f"🎉 Successfully seeded {seeded_count}/{len(SAMPLE_PRODUCTS)} products")
            
        except Exception as e:
            logger.error(f"❌ Product seeding failed: {e}")
            raise
    
    def _generate_simple_vector(self, text: str, dim: int = 384) -> list:
        """Generate a simple vector from text (placeholder for real embedding)"""
        # Simple hash-based vector generation for testing
        import hashlib
        
        # Create hash of text
        text_hash = hashlib.md5(text.lower().encode()).hexdigest()
        
        # Convert to vector
        vector = []
        for i in range(0, min(len(text_hash), dim * 2), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # Normalize to [-0.5, 0.5]
            vector.append(value)
        
        # Pad or truncate to desired dimension
        while len(vector) < dim:
            vector.append(0.0)
        
        return vector[:dim]
    
    async def verify_seeding(self):
        """Verify that products were seeded correctly"""
        try:
            logger.info("🔍 Verifying seeded data...")
            
            # Check Firestore
            products = await self.firestore.query_collection('products', limit=20)
            logger.info(f"Firestore: Found {len(products)} products")
            
            # Check Qdrant (optional)
            qdrant_count = 0
            if self.qdrant:
                try:
                    collection_info = await self.qdrant.get_collection_info('products')
                    if collection_info:
                        qdrant_count = collection_info.get('points_count', 0)
                        logger.info(f"Qdrant: Collection has {qdrant_count} points")
                    else:
                        logger.warning("Qdrant: Collection 'products' not found")
                except Exception as e:
                    logger.warning(f"Qdrant verification failed: {e}")
            
            # Sample some products
            if products:
                sample = products[:3]
                logger.info("Sample products:")
                for product in sample:
                    logger.info(f"  - {product.get('name', 'Unknown')} (${product.get('price', 0)})")
            
            return len(products) > 0
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.firestore:
            await self.firestore.close()
        if self.qdrant:
            await self.qdrant.close()

async def main():
    """Main seeding function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed product data')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing data')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing data')
    args = parser.parse_args()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    seeder = ProductSeeder()
    
    try:
        await seeder.initialize_services()
        
        if args.verify_only:
            success = await seeder.verify_seeding()
            if success:
                logger.info("✅ Data verification passed")
            else:
                logger.error("❌ Data verification failed")
                sys.exit(1)
        else:
            await seeder.seed_products(overwrite=args.overwrite)
            await seeder.verify_seeding()
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        sys.exit(1)
    finally:
        await seeder.cleanup()

if __name__ == "__main__":
    asyncio.run(main())