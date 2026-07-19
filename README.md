# ASSIP

A small Python-based repository for collecting and analyzing model metadata from API sources.

## Files

- `fetch_models.py` — pull the main `/api/v1/models` catalog
- `fetch_coding_collection.py` — pull the coding collection listing
- `fetch_quantization.py` — loop through per-model endpoint details for quantization
- `merge_data.py` — merge the three sources and handle multi-endpoint models
- `analysis.py` — group data, run Kruskal-Wallis tests, compute effect sizes, VIF, and prepare holdout splits
- `requirements.txt` — list project dependencies
- `README.md` — project overview and usage notes

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run each script as needed to collect data and analyze results.

## Notes

This repository currently contains starter files for the data collection and analysis workflow.
