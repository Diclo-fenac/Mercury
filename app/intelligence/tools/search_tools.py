"""
Search Tools for LLM Function Calling
Layer 3: Intelligence - Tools
"""
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

logger = get_logger("search_tools")


class SearchTools:
    """Tools for product search operations"""
    
    def __init__(self, search_service=None):
        self.search_service = search_service
    
    async def search_products(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for products"""
        try:
            if not self.search_service:
                return {"success": False, "error": "Search service not available"}
            
            result = await self.search_service.search_products(
                query=query,
                limit=limit,
                filters={"category": category} if category else {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"search_products_error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get search suggestions"""
        try:
            if not self.search_service:
                return {"success": False, "error": "Search service not available"}
            
            suggestions = await self.search_service.get_suggestions(query, limit)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"get_suggestions_error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_trending(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get trending products"""
        try:
            if not self.search_service:
                return {"success": False, "error": "Search service not available"}
            
            result = await self.search_service.get_trending_products(
                category=category,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"get_trending_error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM"""
        return [
            {
                "name": "search_products",
                "description": "Search for products by query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 10
                        },
                        "category": {
                            "type": "string",
                            "description": "Product category filter"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_suggestions",
                "description": "Get search suggestions for autocomplete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Partial search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of suggestions",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_trending",
                "description": "Get trending products",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Product category filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of products",
                            "default": 10
                        }
                    }
                }
            }
        ]
