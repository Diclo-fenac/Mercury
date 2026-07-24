"""Load test for the legacy global Typesense catalog.

This is intentionally separate from the Mercury API load test. The global
``products`` collection is not tenant-scoped, so it must not be accessed by
the API's tenant collection resolver.
"""

import os
import random

from locust import HttpUser, between, task


class GlobalTypesenseUser(HttpUser):
    """Exercise the collection containing the 57k legacy product documents."""

    host = os.getenv("TYPESENSE_LOAD_HOST", "http://localhost:8108")
    wait_time = between(0.05, 0.15)

    def on_start(self) -> None:
        self.client.headers.update(
            {"X-TYPESENSE-API-KEY": os.getenv("TYPESENSE_API_KEY", "xyz")}
        )

    @task
    def search_global_products(self) -> None:
        query = random.choice(("laptop", "phone", "shirt", "watch", "headphones"))
        with self.client.get(
            "/collections/products/documents/search",
            params={
                "q": query,
                "query_by": "title,name,description,brand,category",
                "per_page": 10,
                "num_typos": 2,
                "facet_by": "brand,category",
            },
            name="/collections/products/documents/search",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"HTTP {response.status_code}")
                return
            try:
                payload = response.json()
            except ValueError:
                response.failure("non-JSON response")
                return
            if not isinstance(payload, dict) or not isinstance(payload.get("hits"), list):
                response.failure("missing Typesense hits")
                return
            if not isinstance(payload.get("found"), int):
                response.failure("missing Typesense found count")
