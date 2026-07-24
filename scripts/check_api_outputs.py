"""Check five non-empty, schema-valid responses from each public load-test API."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Callable

import httpx

DEFAULT_API_KEY = "pk_5c75cd41dd114ca7aaf32a040a777008"
SAMPLE_COUNT = 5


def _json(response: httpx.Response, endpoint: str, sample: int) -> dict[str, Any]:
    if response.status_code >= 400:
        raise RuntimeError(f"{endpoint} sample {sample} returned HTTP {response.status_code}: {response.text}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{endpoint} sample {sample} returned non-JSON data") from exc
    if not isinstance(payload, dict) or not payload:
        raise RuntimeError(f"{endpoint} sample {sample} returned an empty payload")
    return payload


def _validate_search(payload: dict[str, Any], endpoint: str, sample: int) -> dict[str, Any]:
    if payload.get("success") is not True:
        raise RuntimeError(f"{endpoint} sample {sample} was not successful: {payload}")
    if not str(payload.get("query", "")).strip():
        raise RuntimeError(f"{endpoint} sample {sample} has no query")
    if not isinstance(payload.get("results"), list):
        raise RuntimeError(f"{endpoint} sample {sample} has no results list")
    if not isinstance(payload.get("total_results"), int):
        raise RuntimeError(f"{endpoint} sample {sample} has no total_results")
    if not isinstance(payload.get("meta"), dict) or "latency_ms" not in payload["meta"]:
        raise RuntimeError(f"{endpoint} sample {sample} has no search metadata")
    return {
        "success": payload["success"],
        "query": payload["query"],
        "results_count": len(payload["results"]),
        "total_results": payload["total_results"],
        "meta": payload["meta"],
        "first_result": payload["results"][0] if payload["results"] else None,
    }


def _validate_autocomplete(payload: dict[str, Any], endpoint: str, sample: int) -> dict[str, Any]:
    suggestions = payload.get("suggestions")
    if not str(payload.get("query", "")).strip() or not isinstance(suggestions, list):
        raise RuntimeError(f"{endpoint} sample {sample} has an invalid payload: {payload}")
    return {
        "query": payload["query"],
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
        "total": payload.get("total"),
    }


def _validate_health(payload: dict[str, Any], endpoint: str, sample: int) -> dict[str, Any]:
    services = payload.get("services")
    if payload.get("status") not in {"healthy", "degraded"}:
        raise RuntimeError(f"{endpoint} sample {sample} has an invalid payload: {payload}")
    return {
        "status": payload["status"],
        "version": payload.get("version"),
        "services": services,
    }


def _validate_chat(payload: dict[str, Any], endpoint: str, sample: int) -> dict[str, Any]:
    answer = payload.get("answer")
    if payload.get("success") is not True or not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(f"{endpoint} sample {sample} has an empty/failed answer: {payload}")
    return {"success": payload["success"], "answer": answer}


def _check_endpoint(
    client: httpx.Client,
    name: str,
    request: Callable[[], httpx.Response],
    validator: Callable[[dict[str, Any], str, int], dict[str, Any]],
) -> None:
    print(f"\n{name}: {SAMPLE_COUNT} samples")
    for sample in range(1, SAMPLE_COUNT + 1):
        response = request()
        payload = _json(response, name, sample)
        summary = validator(payload, name, sample)
        print(json.dumps({"sample": sample, "status": response.status_code, "payload": summary}, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("MERCURY_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--api-key", default=os.getenv("SEARCH_API_KEY", DEFAULT_API_KEY))
    args = parser.parse_args()

    headers = {"X-API-Key": args.api_key, "Content-Type": "application/json"}
    queries = ["laptop", "phone", "headphones", "camera", "watch"]
    with httpx.Client(base_url=args.base_url.rstrip("/"), headers=headers, timeout=30.0) as client:
        _check_endpoint(
            client,
            "POST /api/v1/search/",
            lambda: client.post(
                "/api/v1/search/",
                json={"query": queries[0], "pagination": {"page": 1, "limit": 10}},
            ),
            _validate_search,
        )
        _check_endpoint(
            client,
            "GET /api/v1/search/autocomplete",
            lambda: client.get("/api/v1/search/autocomplete?q=lap&limit=5"),
            _validate_autocomplete,
        )
        _check_endpoint(client, "GET /health", lambda: client.get("/health"), _validate_health)
        _check_endpoint(
            client,
            "POST /api/v1/search/chat",
            lambda: client.post(
                "/api/v1/search/chat",
                json={"message": "Can you recommend a good laptop?", "session_id": "output_check"},
            ),
            _validate_chat,
        )

    print("\nAll API output checks passed.")
    print("Embedding path: Gemini Embedding 2, 384 dimensions; vectors are internal and are not returned by these APIs.")


if __name__ == "__main__":
    main()
