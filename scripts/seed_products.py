#!/usr/bin/env python3
"""
Product Data Seeding Script
Seeds real product data into Postgres for testing
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.db.postgres import PostgresClient
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
    """Seeds product data into PostgreSQL"""
    
    def __init__(self):
        self.db = None
        self.id_gen = IDGenerator()
        self.vector_dim = 768
    
    async def initialize_services(self):
        """Initialize database services"""
        try:
            from app.settings import get_settings
            settings = get_settings()
            # Initialize PostgreSQL
            self.db = PostgresClient(
                database_url=settings.DATABASE_URL
            )
            await self.db.connect()
            logger.info("✅ PostgreSQL connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    async def seed_products(self, overwrite: bool = False):
        """Seed products into PostgreSQL"""
        try:
            logger.info("🌱 Starting product seeding...")
            
            # Check if products already exist using async session
            org_id = "00000000-0000-0000-0000-000000000001"
            org_uuid = UUID(org_id)
            
            async with self.db.async_session() as session:
                from sqlalchemy import select

                from app.domain.tenants.models import Catalog, CatalogItem, Organization
                
                # Ensure default organization exists
                org = await session.get(Organization, org_uuid)
                if not org:
                    org = Organization(id=org_uuid, name="Demo Store", slug="demo-store", owner_email="demo@mystore.com")
                    session.add(org)
                    await session.flush()
                
                # Ensure default catalog exists
                cat_stmt = select(Catalog).where(Catalog.organization_id == org_uuid)
                cat_res = await session.execute(cat_stmt)
                catalog = cat_res.scalar_one_or_none()
                if not catalog:
                    catalog = Catalog(organization_id=org_uuid, name="Default Catalog", slug="default-catalog")
                    session.add(catalog)
                    await session.flush()

                # Check existing items
                if not overwrite:
                    item_stmt = select(CatalogItem).where(CatalogItem.organization_id == org_uuid).limit(1)
                    existing = (await session.execute(item_stmt)).scalar()
                    if existing:
                        logger.info("Products already exist in default catalog. Use --overwrite to replace them.")
                        return

                seeded_count = 0
                for product_data in SAMPLE_PRODUCTS:
                    prod_id = self.id_gen.product_id()
                    doc = {
                        'id': prod_id,
                        'name': product_data['name'],
                        'title': product_data['name'],
                        'brand': product_data['brand'],
                        'category': product_data['category'],
                        'sub_category': product_data.get('subcategory') or product_data.get('sub_category', ''),
                        'description': product_data['description'],
                        'rating': product_data.get('rating', 0.0),
                        'stock': product_data.get('in_stock', True),
                        'online_available': True,
                        'selling_price': product_data['price']
                    }
                    item = CatalogItem(
                        organization_id=org_uuid,
                        catalog_id=catalog.id,
                        external_id=prod_id,
                        resource_type="product",
                        title=product_data['name'],
                        brand=product_data['brand'],
                        category=product_data['category'],
                        description=product_data['description'],
                        document=doc,
                        status="active"
                    )
                    session.add(item)
                    seeded_count += 1
                    logger.info(f"✅ Seeded: {product_data['name']}")

                await session.commit()
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
            
            async with self.db.async_session() as session:
                from sqlalchemy import select

                from app.domain.tenants.models import CatalogItem
                res = await session.execute(select(CatalogItem).limit(20))
                items = res.scalars().all()
                logger.info(f"PostgreSQL: Found {len(items)} catalog items")
                return len(items) > 0
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.db:
            await self.db.close()

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