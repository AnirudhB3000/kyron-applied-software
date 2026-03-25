# Outputs

This directory stores generated outputs from the extraction, deduplication, and website-enrichment pipeline.

## Notes

- Gitignored files in this directory are intermediary or generated artifacts.
- The main deliverable files are the cleaned practice datasets written by the pipeline scripts.
- Website enrichment was intentionally limited to 1,500 rows out of roughly 16,000 possible practice rows in order to make Step 2 practical.

## Common Files

- `orthopedic_candidates.csv`: intermediate extraction output
- `orthopedic_practices_base.csv`: base extracted practice output before deduplication
- `orthopedic_practices_deduped.csv`: cleaned deduplicated dataset without website enrichment
- `orthopedic_practices_with_websites.csv`: website-enriched dataset
- `orthopedic_practices_with_websites_cleaned.csv`: website-enriched dataset with empty website values normalized to `null`
- `*_summary.json`: QA and enrichment summaries
- `*_cache.json`: Google Places query and details caches
