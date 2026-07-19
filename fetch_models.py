"""Fetch OpenRouter models and save them locally.

Get the public model list from /api/v1/models and write:
- data/models_raw.json
- data/models.csv

Usage:
    python fetch_models.py
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests

MODELS_URL = "https://openrouter.ai/api/v1/models"
OUT_DIR = Path("data")


def fetch_models() -> List[Dict[str, Any]]:
    response = requests.get(MODELS_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


def flatten_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """Convert one model entry into a simple flat row."""
    architecture = model.get("architecture", {}) or {}
    pricing = model.get("pricing", {}) or {}
    top_provider = model.get("top_provider", {}) or {}

    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "author": model.get("id", "").split("/", 1)[0] if model.get("id") else None,
        "description": model.get("description"),
        "created": model.get("created"),
        "context_length": model.get("context_length"),
        "tokenizer": architecture.get("tokenizer"),
        "input_modalities": ",".join(architecture.get("input_modalities", []) or []),
        "output_modalities": ",".join(architecture.get("output_modalities", []) or []),
        "supported_parameters": ",".join(model.get("supported_parameters", []) or []),
        "prompt_price": pricing.get("prompt"),
        "completion_price": pricing.get("completion"),
        "request_price": pricing.get("request"),
        "image_price": pricing.get("image"),
        "max_completion_tokens": top_provider.get("max_completion_tokens"),
        "is_moderated": top_provider.get("is_moderated"),
    }


def save_json(data: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def save_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    models = fetch_models()
    print(f"Fetched {len(models)} models from OpenRouter")

    raw_path = OUT_DIR / "models_raw.json"
    csv_path = OUT_DIR / "models.csv"

    save_json(models, raw_path)

    rows = [flatten_model(model) for model in models]
    save_csv(rows, csv_path)

    print(f"Saved {len(rows)} rows to {csv_path}")
    if rows:
        print(pd.DataFrame(rows).head().to_string(index=False))


if __name__ == "__main__":
    main()
