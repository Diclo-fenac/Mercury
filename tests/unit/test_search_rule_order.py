import pytest

from app.domain.search.rules import SearchRuleEngine


def test_apply_query_rules_redirect():
    redirects = [{"query_pattern": "shoes", "redirect_url": "/category/shoes", "is_active": True}]
    synonyms = []
    
    result = SearchRuleEngine.apply_query_rules("Shoes", redirects, synonyms)
    assert result["action"] == "redirect"
    assert result["url"] == "/category/shoes"

def test_apply_query_rules_synonym():
    redirects = []
    synonyms = [{"term": "sneakers", "synonyms": ["trainers", "kicks"], "is_active": True}]
    
    result = SearchRuleEngine.apply_query_rules("buy sneakers", redirects, synonyms)
    assert result["action"] == "search"
    assert "trainers kicks" in result["expanded_query"]

def test_apply_result_rules_boosts_and_pins():
    results = [
        {"id": "1", "brand": "Nike", "_score": 1.0},
        {"id": "2", "brand": "Adidas", "_score": 1.0},
        {"id": "3", "brand": "Nike", "_score": 1.0},
    ]
    
    pins = [{"product_id": "2", "position": 1, "is_active": True}]
    boosts = [{"attribute_name": "brand", "attribute_value": "Nike", "boost_factor": 2.0, "is_active": True}]
    
    final_results = SearchRuleEngine.apply_result_rules(results, pins, boosts)
    
    # Pin should be first
    assert final_results[0]["id"] == "2"
    
    # Boosted Nike should be next
    assert final_results[1]["brand"] == "Nike"
    assert final_results[1]["_score"] == 2.0
    assert final_results[2]["brand"] == "Nike"
    assert final_results[2]["_score"] == 2.0
