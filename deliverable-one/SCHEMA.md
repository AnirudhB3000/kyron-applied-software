# Dataset Schema

The deliverable uses a lean practice-level schema designed to stay dense after filtering and deduplication.

## Final Output Schema

```csv
practice_id,practice_name,phone,street,city,state,zip_code,website,location_count,source,source_url
```

This is the schema for the final deduplicated output:

- [`orthopedic_practices_deduped.csv`](D:\kyron-applied-software\deliverable-one\outputs\orthopedic_practices_deduped.csv)

## Field Rationale

- `practice_id`: Canonical identifier for the deduplicated practice record. Currently sourced from the canonical NPI chosen for the merged cluster.
- `practice_name`: Canonical practice name selected during deduplication.
- `phone`: Canonical phone selected from the surviving representative record.
- `street`: Canonical street address from the surviving representative record.
- `city`: Canonical city.
- `state`: Canonical two-letter state code.
- `zip_code`: Canonical 5-digit ZIP code.
- `website`: Reserved for later enrichment. Currently blank in the NPPES-only pipeline.
- `location_count`: Count of distinct normalized addresses merged into the deduplicated practice record.
- `source`: Provenance label. Currently `nppes`.
- `source_url`: Reserved for later provenance enrichment. Currently blank in the NPPES-only pipeline.

## Intermediate Dataset Schema

The extraction step first writes a candidate-level file with additional internal fields used for filtering and deduplication:

- [`orthopedic_candidates.csv`](D:\kyron-applied-software\deliverable-one\outputs\orthopedic_candidates.csv)

```csv
npi,confidence_tier,match_reason,practice_name,other_name,phone,street_1,street_2,city,state,zip_code,parent_organization,is_organization_subpart,taxonomy_codes,taxonomy_groups,source
```

Field notes:
- `npi`: Source NPI from the NPPES organization record.
- `confidence_tier`: Initial extraction classification such as `high` or `medium`.
- `match_reason`: Evidence used to include the row, such as taxonomy and name matches.
- `other_name`: Other organization name from NPPES when present.
- `street_1`, `street_2`: Raw practice location address lines before final canonicalization.
- `parent_organization`: Parent organization legal business name from NPPES when present.
- `is_organization_subpart`: NPPES organizational subpart indicator.
- `taxonomy_codes`: Pipe-separated non-empty taxonomy codes.
- `taxonomy_groups`: Pipe-separated non-empty taxonomy groups.

## Current Source-Specific Notes

- The current pipeline is NPPES-only.
- `website` and `source_url` are intentionally retained in the final schema for later enrichment, but they are not yet populated.
- `location_count` is derived from merged office records and secondary practice locations.

## Design Constraints

- Keep the final dataset compact and practice-level.
- Prefer dense columns over wide sparse enrichment.
- Preserve internal matching evidence in intermediate files rather than bloating the final deliverable schema.
