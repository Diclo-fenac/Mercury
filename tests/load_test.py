"""
Locust load test for Mercury AI Assistant
Run: locust -f tests/load_test.py --host=http://localhost:8000
"""
import random

from locust import HttpUser, between, task


class MercuryUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.user_id = f"load_test_user_{random.randint(1, 1000)}"
        self.queries = [
            "laptop", "headphones", "phone", "shoes", "watch",
            "wireless earbuds", "gaming mouse", "tshirt", "backpack"
        ]
    
    @task(5)
    def search(self):
        query = random.choice(self.queries)
        self.client.post("/api/v1/search/", json={
            "query": query,
            "user_id": self.user_id,
            "limit": 10
        })
    
    @task(2)
    def chat(self):
        messages = [
            "Show me laptops under 50000",
            "What are the best headphones?",
            "Find running shoes",
            "Recommend a phone for gaming"
        ]
        self.client.post("/api/v1/chat/", json={
            "user_id": self.user_id,
            "message": random.choice(messages)
        })
    
    @task(1)
    def get_suggestions(self):
        self.client.get("/api/v1/products/search/suggestions?q=phone&limit=5")
    
    @task(1)
    def health_check(self):
        self.client.get("/health")