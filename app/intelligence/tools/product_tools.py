"""
Product Tools - Layer 3: Intelligence
Function calling tools for product operations
"""
from typing import Any, Dict, List

from app.domain.products.service import ProductService


class ProductTools:
    """Product-related tools for LLM"""
    
    def __init__(self, product_service: ProductService):
        self.products = product_service
    
    async def search_products(self, query: str, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for products"""
        filters = {}
        if category:
            filters['category'] = category
        
        results = await self.products.search_products(filters, limit)
        
        # Return simplified product info for LLM
        return [
            {
                'id': p.get('id'),
                'title': p.get('title'),
                'price': p.get('price', {}).get('selling'),
                'category': p.get('category'),
                'rating': p.get('rating')
            }
            for p in results
        ]
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Get detailed product information"""
        product = await self.products.get_product(product_id)
        if not product:
            return {"error": "Product not found"}
        
        return {
            'id': product.get('id'),
            'title': product.get('title'),
            'description': product.get('description'),
            'price': product.get('price'),
            'category': product.get('category'),
            'brand': product.get('brand'),
            'rating': product.get('rating'),
            'stock': product.get('stock')
        }
    
    async def get_trending(self, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get trending products"""
        results = await self.products.get_trending_products(category, limit)
        
        return [
            {
                'id': p.get('id'),
                'title': p.get('title'),
                'price': p.get('price', {}).get('selling'),
                'category': p.get('category')
            }
            for p in results
        ]
    
    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """Get function declarations for LLM"""
        return [
            {
                'name': 'search_products',
                'description': 'Search for products by query and optional category',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'Search query for products'
                        },
                        'category': {
                            'type': 'string',
                            'description': 'Optional category filter'
                        },
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of results',
                            'default': 5
                        }
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'get_product_details',
                'description': 'Get detailed information about a specific product',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'product_id': {
                            'type': 'string',
                            'description': 'The product ID'
                        }
                    },
                    'required': ['product_id']
                }
            },
            {
                'name': 'get_trending',
                'description': 'Get trending products, optionally filtered by category',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'category': {
                            'type': 'string',
                            'description': 'Optional category filter'
                        },
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of results',
                            'default': 5
                        }
                    }
                }
            }
        ]
