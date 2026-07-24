import random

from locust import HttpUser, between, task

SEARCH_API_KEY = "pk_5c75cd41dd114ca7aaf32a040a777008"

class MercurySearchLoadUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.headers = {
            "X-API-Key": SEARCH_API_KEY,
            "Content-Type": "application/json"
        }
        self.queries = ["laptop", "phone", "headphones", "camera", "watch", "wireless", "battery"]

    @staticmethod
    def _validate_json_response(response, endpoint):
        """Fail load-test requests that return blank or structurally invalid payloads."""
        if response.status_code >= 400:
            response.failure(f"{endpoint} returned HTTP {response.status_code}")
            return
        try:
            payload = response.json()
        except ValueError:
            response.failure(f"{endpoint} returned non-JSON data")
            return
        if not isinstance(payload, dict) or not payload:
            response.failure(f"{endpoint} returned an empty payload")
            return

        required = {
            "search": (payload.get("success") is True and isinstance(payload.get("results"), list)
                       and isinstance(payload.get("total_results"), int)
                       and isinstance(payload.get("meta"), dict)
                       and bool(str(payload.get("query", "")).strip())),
            "autocomplete": (bool(str(payload.get("query", "")).strip())
                              and isinstance(payload.get("suggestions"), list)
                              and bool(payload.get("suggestions"))),
            "health": payload.get("status") in {"healthy", "degraded"},
            "chat": (payload.get("success") is True
                      and isinstance(payload.get("answer"), str)
                      and bool(payload["answer"].strip())),
        }
        if not required[endpoint]:
            response.failure(f"{endpoint} returned an invalid payload: {payload}")

    @task(5)
    def search_products(self):
        query = random.choice(self.queries)
        with self.client.post(
            "/api/v1/search/",
            headers=self.headers,
            json={"query": query, "pagination": {"page": 1, "limit": 10}},
            name="/api/v1/search",
            catch_response=True,
        ) as response:
            self._validate_json_response(response, "search")

    @task(3)
    def autocomplete_suggestions(self):
        query = random.choice(self.queries)[:3]
        with self.client.get(
            f"/api/v1/search/autocomplete?q={query}&limit=5",
            headers=self.headers,
            name="/api/v1/search/autocomplete",
            catch_response=True,
        ) as response:
            self._validate_json_response(response, "autocomplete")

    @task(2)
    def health_check(self):
        with self.client.get(
            "/health",
            name="/health",
            catch_response=True,
        ) as response:
            self._validate_json_response(response, "health")

    @task(1)
    def public_chat(self):
        with self.client.post(
            "/api/v1/search/chat",
            headers=self.headers,
            json={"message": "Can you recommend a good laptop?", "session_id": "locust_session"},
            name="/api/v1/search/chat",
            catch_response=True,
        ) as response:
            self._validate_json_response(response, "chat")
