
"""
fetch_quantization.py
 
Loops over every model in data/models.csv and hits OpenRouter's
per-model endpoints route to pull quantization level (and per-provider
pricing) for each serving provider of that model.
 
  GET https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints
 
This is a separate, more granular call than the main /api/v1/models
list -- quantization lives at the endpoint level, not the top-level
model summary, because the same model can be served by multiple
providers at different quantization levels and prices.
 
Usage:
    python fetch_quantization.py
 
Notes:
    - Run fetch_models.py first; this script reads data/models.csv.
    - This makes one HTTP request per model, so with 300+ models this
      will take a few minutes. Be polite -- there's a small delay
      between requests below. Adjust if you hit rate limits.
"""
 
import os
import json
import time
import requests
import pandas as pd
 
OUT_DIR = "data"
ENDPOINT_TEMPLATE = "https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints"
REQUEST_DELAY_SECONDS = 0.25
 
 
def load_model_ids():
    df = pd.read_csv(os.path.join(OUT_DIR, "models.csv"))
    return df["id"].dropna().tolist()
 
 
def fetch_endpoints_for_model(model_id):
    author, slug = model_id.split("/", 1)
    url = ENDPOINT_TEMPLATE.format(author=author, slug=slug)
    try:
        resp = requests.get(url, timeout=30, headers={"Accept": "application/json"})
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  WARNING: failed to fetch endpoints for {model_id}: {e}")
        return None
 
 
def main():
    model_ids = load_model_ids()
    print(f"Fetching endpoint/quantization data for {len(model_ids)} models...")
 
    all_endpoint_rows = []
    raw_responses = {}
 
    for i, model_id in enumerate(model_ids, 1):
        print(f"[{i}/{len(model_ids)}] {model_id}")
        data = fetch_endpoints_for_model(model_id)
        if data is None:
            continue
 
        raw_responses[model_id] = data
 
        endpoints = data.get("data", {}).get("endpoints", []) or []
        for ep in endpoints:
            all_endpoint_rows.append({
                "model_id": model_id,
                "provider_name": ep.get("provider_name"),
                "quantization": ep.get("quantization"),
                "prompt_price": (ep.get("pricing") or {}).get("prompt"),
                "completion_price": (ep.get("pricing") or {}).get("completion"),
                "context_length": ep.get("context_length"),
                "status": ep.get("status"),
            })
 
        time.sleep(REQUEST_DELAY_SECONDS)
 
    with open(os.path.join(OUT_DIR, "endpoints_raw.json"), "w") as f:
        json.dump(raw_responses, f, indent=2)
 
    endpoints_df = pd.DataFrame(all_endpoint_rows)
    endpoints_df.to_csv(os.path.join(OUT_DIR, "endpoints.csv"), index=False)
 
    print(f"Saved {len(endpoints_df)} endpoint rows to {OUT_DIR}/endpoints.csv")
 
 
if __name__ == "__main__":
    main()