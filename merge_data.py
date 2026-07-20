"""
merge_data.py
 
Merges the three OpenRouter data pulls into one analysis-ready
dataframe:
  - data/models.csv               (from fetch_models.py)
  - data/coding_collection_ids.json (from fetch_coding_collection.py)
  - data/endpoints.csv            (from fetch_quantization.py)
 
Produces data/merged.csv with, per model:
  - core pricing/context fields
  - is_coding: bool, in the coding collection
  - is_flagship: bool, from a manually maintained list of major-lab
    frontier model prefixes (edit FLAGSHIP_AUTHORS / FLAGSHIP_KEYWORDS
    below -- this is a judgment call, not something OpenRouter labels
    for you)
  - group: one of "coding_specialist", "flagship_generalist", "other"
  - is_open_weight: bool (best-effort; see note below)
  - min_quantization / cheapest_endpoint fields, for handling models
    served by multiple providers at different prices
 
Usage:
    python merge_data.py
"""
 
import os
import json
import pandas as pd
 
DATA_DIR = "data"
 
# --- Judgment calls that need human review before trusting results ---
# Fill these in / adjust after looking at data/models.csv. This is the
# "flagship generalist" bucket from the three-way group split -- OpenRouter
# doesn't label this for us, so it has to be defined explicitly and
# revisited if the model lineup changes.
FLAGSHIP_AUTHORS = {
    "openai",
    "anthropic",
    "google",
}
FLAGSHIP_NAME_KEYWORDS = [
    # e.g. "gpt-5", "claude-opus", "gemini-3-pro" -- fill in the specific
    # flagship model name fragments you want counted, so mini/nano/haiku
    # tiers of the same family don't get miscounted as flagship.
]
 
# Best-effort open-weight signal. OpenRouter doesn't cleanly expose this
# as a single boolean on /api/v1/models as of this writing -- this is a
# placeholder heuristic (e.g. based on known open-weight authors) that
# should be replaced with whatever field/collection turns out to be most
# reliable once you've inspected data/models_raw.json directly.
OPEN_WEIGHT_AUTHORS = {
    "meta-llama",
    "mistralai",
    "qwen",
    "deepseek",
    "google",  # gemma variants only -- refine by model name, not just author
}
 
 
def load_models():
    return pd.read_csv(os.path.join(DATA_DIR, "models.csv"))
 
 
def load_coding_ids():
    path = os.path.join(DATA_DIR, "coding_collection_ids.json")
    if not os.path.exists(path):
        print("WARNING: coding_collection_ids.json not found -- run fetch_coding_collection.py first")
        return set()
    with open(path) as f:
        return set(json.load(f))
 
 
def load_endpoints():
    path = os.path.join(DATA_DIR, "endpoints.csv")
    if not os.path.exists(path):
        print("WARNING: endpoints.csv not found -- run fetch_quantization.py first")
        return pd.DataFrame(columns=["model_id", "provider_name", "quantization",
                                      "prompt_price", "completion_price",
                                      "context_length", "status"])
    return pd.read_csv(path)
 
 
def label_flagship(row):
    if row["author"] in FLAGSHIP_AUTHORS:
        if not FLAGSHIP_NAME_KEYWORDS:
            return True
        name = str(row.get("name", "")).lower()
        return any(kw.lower() in name for kw in FLAGSHIP_NAME_KEYWORDS)
    return False
 
 
def label_open_weight(row):
    # Placeholder heuristic -- revisit after inspecting raw model data.
    return row["author"] in OPEN_WEIGHT_AUTHORS
 
 
def assign_group(row):
    if row["is_coding"] and not row["is_flagship"]:
        return "coding_specialist"
    if row["is_flagship"]:
        return "flagship_generalist"
    return "other"
 
 
def summarize_endpoints(endpoints_df):
    """Per model: cheapest completion price seen, and the quantization
    at that cheapest endpoint, so multi-provider models collapse to one
    row without silently discarding the quantization signal."""
    if endpoints_df.empty:
        return pd.DataFrame(columns=["id", "min_completion_price", "quantization_at_min_price", "n_endpoints"])
 
    endpoints_df = endpoints_df.dropna(subset=["completion_price"])
    idx = endpoints_df.groupby("model_id")["completion_price"].idxmin()
    cheapest = endpoints_df.loc[idx, ["model_id", "completion_price", "quantization"]]
    cheapest = cheapest.rename(columns={
        "model_id": "id",
        "completion_price": "min_completion_price",
        "quantization": "quantization_at_min_price",
    })
    counts = endpoints_df.groupby("model_id").size().rename("n_endpoints").reset_index()
    counts = counts.rename(columns={"model_id": "id"})
    return cheapest.merge(counts, on="id", how="left")
 
 
def main():
    models = load_models()
    coding_ids = load_coding_ids()
    endpoints = load_endpoints()
 
    models["is_coding"] = models["id"].isin(coding_ids)
    models["is_flagship"] = models.apply(label_flagship, axis=1)
    models["is_open_weight"] = models.apply(label_open_weight, axis=1)
    models["group"] = models.apply(assign_group, axis=1)
 
    endpoint_summary = summarize_endpoints(endpoints)
    merged = models.merge(endpoint_summary, on="id", how="left")
 
    out_path = os.path.join(DATA_DIR, "merged.csv")
    merged.to_csv(out_path, index=False)
 
    print(f"Saved merged dataset ({len(merged)} rows) to {out_path}")
    print(merged["group"].value_counts())
    print(f"is_coding=True count: {merged['is_coding'].sum()}")
    print(f"is_open_weight=True count: {merged['is_open_weight'].sum()}")
    print("\nReminder: FLAGSHIP_AUTHORS / FLAGSHIP_NAME_KEYWORDS and "
          "OPEN_WEIGHT_AUTHORS above are manual judgment calls -- review "
          "and adjust them before trusting the group counts.")
 
 
if __name__ == "__main__":
    main()