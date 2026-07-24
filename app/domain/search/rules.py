from typing import Any, Dict, List, Optional


class SearchRuleEngine:
    """
    Applies tenant-scoped merchandising rules (redirects, synonyms, pins, boosts/buries)
    to a search query or result set.
    """
    
    @staticmethod
    def apply_query_rules(query: str, redirects: List[Dict[str, Any]], synonyms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for redirects and expand synonyms.
        """
        # 1. Check Exact Match Redirects
        for redirect in redirects:
            if redirect.get("query_pattern", "").lower() == query.lower() and redirect.get("is_active", True):
                return {"action": "redirect", "url": redirect.get("redirect_url")}
                
        # 2. Expand Synonyms
        expanded_query = query
        for syn in synonyms:
            if syn.get("term", "").lower() in query.lower() and syn.get("is_active", True):
                # Simple expansion
                expanded_query += " " + " ".join(syn.get("synonyms", []))
                
        return {"action": "search", "expanded_query": expanded_query.strip()}

    @staticmethod
    def apply_result_rules(
        results: List[Dict[str, Any]], 
        pins: List[Dict[str, Any]], 
        boosts: List[Dict[str, Any]],
        hard_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply pins and boosts. 
        Pins and boosts cannot override hard_filters.
        """
        # We don't apply rules if there are no results
        if not results:
            return results
            
        # Hard filters check logic (pseudo-logic for test validation)
        # If a pinned product doesn't match the hard filters, it shouldn't be pinned.
        # But we assume `results` are already filtered by the engine, so we only reorder what is returned,
        # OR we inject pins. If we inject pins, we MUST check hard filters.
        
        # 1. Apply Boosts
        for result in results:
            score_multiplier = 1.0
            for boost in boosts:
                if not boost.get("is_active", True):
                    continue
                
                attr_name = boost.get("attribute_name")
                attr_value = boost.get("attribute_value")
                
                if attr_name and result.get(attr_name) == attr_value:
                    score_multiplier *= boost.get("boost_factor", 1.0)
            
            # Assuming the result has a _score field from the search engine
            current_score = result.get("_score", 1.0)
            result["_score"] = current_score * score_multiplier

        # Re-sort after boost
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # 2. Apply Pins
        pinned_items = []
        regular_items = list(results)
        
        for pin in sorted(pins, key=lambda x: x.get("position", 1)):
            if not pin.get("is_active", True):
                continue
                
            product_id = pin.get("product_id")
            
            # Find the item in the results
            item_to_pin = next((item for item in regular_items if str(item.get("id")) == str(product_id)), None)
            
            if item_to_pin:
                regular_items.remove(item_to_pin)
                pinned_items.append(item_to_pin)
                
        # Pins go at the top
        return pinned_items + regular_items
