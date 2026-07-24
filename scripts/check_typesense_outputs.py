"""Print five real responses from the legacy 57k Typesense collection."""

from __future__ import annotations

import argparse
import json

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8108")
    parser.add_argument("--api-key", default="xyz")
    args = parser.parse_args()

    queries = ("laptop", "phone", "shirt", "watch", "headphones")
    headers = {"X-TYPESENSE-API-KEY": args.api_key}
    with httpx.Client(base_url=args.base_url, headers=headers, timeout=10.0) as client:
        collection = client.get("/collections/products")
        collection.raise_for_status()
        metadata = collection.json()
        print(
            json.dumps(
                {
                    "collection": metadata.get("name"),
                    "documents": metadata.get("num_documents"),
                    "embedding_field": next(
                        (
                            {
                                "type": field.get("type"),
                                "num_dim": field.get("num_dim"),
                                "optional": field.get("optional"),
                            }
                            for field in metadata.get("fields", [])
                            if field.get("name") == "embedding"
                        ),
                        None,
                    ),
                },
                indent=2,
            )
        )

        for index, query in enumerate(queries, start=1):
            response = client.get(
                "/collections/products/documents/search",
                params={
                    "q": query,
                    "query_by": "title,name,description,brand,category",
                    "per_page": 5,
                    "num_typos": 2,
                },
            )
            response.raise_for_status()
            payload = response.json()
            hits = payload.get("hits") or []
            first = (hits[0].get("document") or {}) if hits else {}
            print(
                json.dumps(
                    {
                        "sample": index,
                        "query": query,
                        "found": payload.get("found"),
                        "results": len(hits),
                        "first_product": {
                            "id": first.get("id"),
                            "title": first.get("title") or first.get("name"),
                            "brand": first.get("brand"),
                            "category": first.get("category"),
                            "has_embedding": bool(first.get("embedding")),
                        },
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    main()
