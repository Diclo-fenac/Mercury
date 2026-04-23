"""
Pricing Service - Layer 5: Domain
Pure business logic for pricing rules using actual database schema
"""
from typing import Any, Dict


class PricingService:
    """Pricing business logic using actual price schema"""
    
    def __init__(self):
        pass
    
    def calculate_discount_percentage(self, actual_price: float, selling_price: float) -> float:
        """Calculate discount percentage using actual schema fields"""
        if actual_price <= 0 or selling_price <= 0:
            return 0.0
        
        if selling_price >= actual_price:
            return 0.0
        
        return round(((actual_price - selling_price) / actual_price) * 100, 2)
    
    def calculate_savings(self, actual_price: float, selling_price: float) -> float:
        """Calculate savings amount"""
        return max(0, actual_price - selling_price)
    
    def apply_bulk_discount(self, price_info: Dict[str, Any], quantity: int) -> Dict[str, Any]:
        """Apply bulk discount to price info using actual schema"""
        selling_price = price_info.get("selling", 0)
        actual_price = price_info.get("actual", 0)
        
        # Calculate bulk discount on selling price
        if quantity >= 100:
            new_selling = selling_price * 0.85
        elif quantity >= 50:
            new_selling = selling_price * 0.90
        elif quantity >= 10:
            new_selling = selling_price * 0.95
        else:
            new_selling = selling_price
        
        # Recalculate discount percentage
        new_discount = self.calculate_discount_percentage(actual_price, new_selling)
        
        return {
            "actual": actual_price,
            "selling": round(new_selling, 2),
            "discount_percent": new_discount
        }
    
    def is_price_valid(self, price_info: Dict[str, Any]) -> bool:
        """Validate price info using actual schema"""
        actual = price_info.get("actual", 0)
        selling = price_info.get("selling", 0)
        
        return actual > 0 and selling > 0 and selling <= actual
    
    def format_price_display(self, price_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format price for display using actual schema"""
        actual = price_info.get("actual", 0)
        selling = price_info.get("selling", 0)
        discount_percent = price_info.get("discount_percent", 0)
        
        return {
            "original_price": f"₹{actual:,.2f}",
            "selling_price": f"₹{selling:,.2f}",
            "discount_text": f"{discount_percent}% OFF" if discount_percent > 0 else "",
            "savings": f"Save ₹{actual - selling:,.2f}" if actual > selling else "",
            "has_discount": discount_percent > 0
        }
