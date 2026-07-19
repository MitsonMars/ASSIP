"""
fetch_coding_collection.py
 
Pulls model IDs belonging to OpenRouter's "coding" collection so we have
 a group-membership label independent of the main /api/v1/models pull.
 
NOTE: OpenRouter does not (as of this writing) publish a documented JSON
API for collections the way it does for /api/v1/models. This script
scrapes the public collection page instead. If OpenRouter changes their
page structure, the CSS selectors below will need updating -- check the
live page first with view-source or your browser dev tools before
assuming this still works.
 
Usage:
    python fetch_coding_collection.py
"""
 
import os
import re
import json
import requests
from bs4 import BeautifulSoup
 
COLLECTION_URL = "https://openrouter.ai/collections/programming"
OUT_DIR = "data"
 
 
def fetch_collection_page():
    resp = requests.get(COLLECTION_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text
 
 
def extract_model_ids(html):
    """
    Best-effort extraction of model IDs (e.g. 'qwen/qwen3-coder') that
    appear as links on the collection page. Model links on OpenRouter
    follow the pattern /author/slug.
 
    TODO before relying on this: manually inspect a sample of extracted
    IDs against the live page to confirm nothing is missed / no noise
    (e.g. nav links) is included.
    """
    soup = BeautifulSoup(html, "html.parser")
    ids = set()
    pattern = re.compile(r"^/([\w.\-]+)/([\w.\-:]+)$")
 
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = pattern.match(href)
        if m:
            author, slug = m.groups()
            # filter out obvious non-model nav links
            if author in ("collections", "docs", "models", "chat", "rankings"):
                continue
            ids.add(f"{author}/{slug}")
 
    return sorted(ids)
 
 
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
 
    html = fetch_collection_page()
    model_ids = extract_model_ids(html)
 
    print(f"Extracted {len(model_ids)} candidate model IDs from the coding collection page")
    print("Spot-check a handful of these against the live page before trusting this list.")
 
    with open(os.path.join(OUT_DIR, "coding_collection_ids.json"), "w") as f:
        json.dump(model_ids, f, indent=2)
 
    print(f"Saved to {OUT_DIR}/coding_collection_ids.json")
 
 
if __name__ == "__main__":
    main()
