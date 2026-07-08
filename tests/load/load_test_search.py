"""
Locust load test for Mercury AI Assistant - Search & Product Search Stress Test
Run: locust -f tests/load_test_search.py --host=http://localhost:8080
"""
import random

from locust import HttpUser, between, task


class SearchStressUser(HttpUser):
    # Short wait time to generate high request rate and stress-test the backend
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        self.user_id = f"stress_test_user_{random.randint(1, 10000)}"
        self.client.headers.update({"X-API-Key": "stress_test_key_123"})
        self.queries = [
            "laptop", "headphones", "phone", "shoes", "watch",
            "wireless earbuds", "gaming mouse", "tshirt", "backpack",
            "iPhone", "Samsung", "Nike", "Levi's", "Dyson", "Fitbit"
        ]
        self.categories = [
            "Electronics", "Fashion", "Home & Kitchen", None
        ]
        
    @task(8)
    def product_search(self):
        query = random.choice(self.queries)
        category = random.choice(self.categories)
        
        payload = {
            "query": query,
            "limit": 10
        }
        if category:
            payload["filters"] = {"category": [category]}
            
        self.client.post("/api/v1/products/search", json=payload)

    @task(4)
    def search_suggestions(self):
        query = random.choice(["ph", "lap", "sh", "wat", "ni", "dy"])
        self.client.get(f"/api/v1/products/search/suggestions?q={query}&limit=5")

    @task(2)
    def trending_searches(self):
        category = random.choice(["Electronics", "Fashion", None])
        url = "/api/v1/search/trending"
        if category:
            url += f"?category={category}"
        self.client.get(url)

    @task(2)
    def popular_searches(self):
        self.client.get("/api/v1/search/popular")
