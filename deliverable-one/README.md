# Deliverable One

This deliverable builds a cleaned dataset of orthopedic practices in the United States from the NPPES bulk files.

## Directory Layout

- `data/`: source NPPES files and reference documents
- `outputs/`: generated candidate, deduped, and QA outputs
- `scraping-scripts/`: executable pipeline scripts for extraction, deduplication, website enrichment, and final cleanup
- `scraping-scripts/extract_nppes_orthopedic.py`: extraction and candidate-generation script
- `scraping-scripts/dedupe_orthopedic_practices.py`: precision filtering and practice-level deduplication script
- `scraping-scripts/enrich_websites_google.py`: Google Places website-enrichment script
- `scraping-scripts/clean_websites_nulls.py`: final cleanup script that normalizes empty website values to `null`
- `SCHEMA.md`: output schema reference

## Pipeline

1. Extract orthopedic candidates from the large NPPES provider file.
2. Join secondary practice locations.
3. Write an intermediate candidate dataset.
4. Deduplicate candidate rows into practice-level output.
5. Write a QA summary for each major step.

## Inputs

Expected source files under `data/`:

- `npidata_pfile_20050523-20260308.csv`
- `pl_pfile_20050523-20260308.csv`
- `othername_pfile_20050523-20260308.csv`
- `endpoint_pfile_20050523-20260308.csv`

The current pipeline uses `npidata` and `pl_pfile` directly.

## Outputs

Extraction step:
- `outputs/orthopedic_candidates.csv`
- `outputs/orthopedic_practices_base.csv`
- `outputs/orthopedic_qa_summary.json`

Deduplication step:
- `outputs/orthopedic_practices_deduped.csv`
- `outputs/orthopedic_dedupe_summary.json`

Website enrichment step:
- `outputs/orthopedic_practices_with_websites.csv`
- `outputs/orthopedic_practices_with_websites_cleaned.csv`
- `outputs/website_enrichment_summary.json`
- `outputs/website_query_cache.json`
- `outputs/website_details_cache.json`

## Run Order

Run the pipeline from the repository root, `D:\kyron-applied-software`, or from inside `deliverable-one/`.

If you run from the repository root, use:

```powershell
python .\deliverable-one\scraping-scripts\extract_nppes_orthopedic.py
python .\deliverable-one\scraping-scripts\dedupe_orthopedic_practices.py
python .\deliverable-one\scraping-scripts\enrich_websites_google.py
python .\deliverable-one\scraping-scripts\clean_websites_nulls.py
```

If you run from inside `deliverable-one/`, use:

```powershell
python .\scraping-scripts\extract_nppes_orthopedic.py
python .\scraping-scripts\dedupe_orthopedic_practices.py
python .\scraping-scripts\enrich_websites_google.py
python .\scraping-scripts\clean_websites_nulls.py
```

## Environment

- `extract_nppes_orthopedic.py`, `dedupe_orthopedic_practices.py`, and `clean_websites_nulls.py` use only local files under `deliverable-one/data` and `deliverable-one/outputs`.
- `enrich_websites_google.py` expects a Google Maps or Google Places API key in the repository-level `.env` file at `D:\kyron-applied-software\.env`.
- Supported environment variable names are `GOOGLE_MAPS_API_KEY` and `GOOGLE_PLACES_API_KEY`.

## Notes

- The extraction script is designed for large-file streaming rather than full in-memory loading.
- The dedupe script intentionally favors precision over maximal recall.
- `outputs/orthopedic_practices_deduped.csv` is the cleaned deduplicated dataset without website enrichment.
- `outputs/orthopedic_practices_with_websites.csv` is the website-enriched variant.
- `outputs/orthopedic_practices_with_websites_cleaned.csv` is the website-enriched variant with empty website values normalized to `null`.
- `source_url` is populated in the deduplicated output.
- `website` is blank in `outputs/orthopedic_practices_deduped.csv` and populated only in `outputs/orthopedic_practices_with_websites.csv`.
