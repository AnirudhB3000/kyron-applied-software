import csv
import json
import re
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"

CANDIDATES_PATH = OUTPUTS_DIR / "orthopedic_candidates.csv"
DEDUPED_PATH = OUTPUTS_DIR / "orthopedic_practices_deduped.csv"
SUMMARY_PATH = OUTPUTS_DIR / "orthopedic_dedupe_summary.json"

NAME_FALSE_POSITIVE_TERMS = ("prosthetics", "orthotics")
GENERIC_EXCLUSION_TERMS = (
    "orthodont",
    "prosthetic",
    "orthotic",
    "university",
    "college of medicine",
    "medical group",
    "physicians network",
    "hospital",
    "ambulatory",
    "health services",
    "school of medicine",
)
INSTITUTIONAL_TERMS = (
    "medical group",
    "physicians network",
    "hospital",
    "medical center",
    "health system",
    "health services",
    "college",
    "university",
    "clinic",
    "ambulatory",
    "school of medicine",
    "physician services",
)
GENERIC_PROVIDER_TERMS = (
    "physicians",
    "physician",
    "specialists group",
    "physician associates",
    "physician billing",
    "health corporation",
    "medical services",
    "central physicians",
    "specialty network",
    "health medical group",
)
SPECIALTY_GENERIC_TERMS = (
    "surgical",
    "surgery",
    "spine",
    "sports medicine",
    "faculty practice",
    "neurosurgery",
    "rehabilitation",
    "pain management",
    "vascular",
    "vein",
    "phlebology",
)
INSTITUTIONAL_ENTITY_TERMS = (
    "medical partners",
    "medical specialties",
    "initiatives",
    "professional services",
    "regents",
    "joint venture",
    "prep",
    "network development",
    "faculty",
    "healthcare",
    "medical assoc",
    "practice, inc",
    "practice pc",
    "practice p.c",
)
LEGAL_SUFFIXES = (
    "llc",
    "inc",
    "pc",
    "p",
    "c",
    "pllc",
    "pa",
    "a",
    "corp",
    "corporation",
    "ltd",
    "llp",
    "lp",
)
STREET_REPLACEMENTS = {
    "suite": "ste",
    "road": "rd",
    "street": "st",
    "avenue": "ave",
    "boulevard": "blvd",
    "drive": "dr",
    "lane": "ln",
    "court": "ct",
    "place": "pl",
    "highway": "hwy",
}


def normalize_text(value: str) -> str:
    return (value or "").strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits[:10] if len(digits) >= 10 else ""


def normalize_zip(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits[:5]


def normalize_name(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\bp\s+a\b", "pa", text)
    text = re.sub(r"\bp\s+c\b", "pc", text)
    tokens = [token for token in text.split() if token not in LEGAL_SUFFIXES]
    return " ".join(tokens)


def normalize_street(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = []
    for token in text.split():
        tokens.append(STREET_REPLACEMENTS.get(token, token))
    return " ".join(tokens)


def enrich_row(row: dict) -> dict:
    combined_street = " ".join(
        part for part in [row.get("street_1", ""), row.get("street_2", "")] if normalize_text(part)
    ).strip()
    enriched = dict(row)
    enriched["norm_name"] = normalize_name(row.get("practice_name", ""))
    enriched["norm_phone"] = normalize_phone(row.get("phone", ""))
    enriched["norm_street"] = normalize_street(combined_street)
    enriched["norm_city"] = normalize_text(row.get("city", "")).lower()
    enriched["norm_state"] = normalize_text(row.get("state", "")).upper()
    enriched["norm_zip"] = normalize_zip(row.get("zip_code", ""))
    enriched["norm_parent_org"] = normalize_name(row.get("parent_organization", ""))
    enriched["combined_street"] = combined_street
    return enriched


def is_false_positive(row: dict) -> bool:
    name_text = normalize_text(row.get("practice_name", "")).lower()
    return (
        any(term in name_text for term in NAME_FALSE_POSITIVE_TERMS) and not has_very_strong_ortho_signal(row)
    ) or (any(term in name_text for term in GENERIC_EXCLUSION_TERMS) and not has_very_strong_ortho_signal(row)) or (
        any(term in name_text for term in INSTITUTIONAL_TERMS) and not is_ortho_branded_keep(row)
    ) or (
        any(term in name_text for term in GENERIC_PROVIDER_TERMS) and not is_ortho_branded_keep(row)
    ) or (
        any(term in name_text for term in SPECIALTY_GENERIC_TERMS) and not is_ortho_branded_keep(row)
    ) or (
        any(term in name_text for term in INSTITUTIONAL_ENTITY_TERMS) and not is_ortho_branded_keep(row)
    )


def has_very_strong_ortho_signal(row: dict) -> bool:
    match_reason = normalize_text(row.get("match_reason", ""))
    name_text = normalize_text(row.get("practice_name", "")).lower()
    return "taxonomy_207X" in match_reason or any(
        term in name_text for term in ("orthopedic", "orthopaedic", "orthopaedics")
    )


def is_ortho_branded(row: dict) -> bool:
    name_text = normalize_text(row.get("practice_name", "")).lower()
    if any(term in name_text for term in ("orthopedic", "orthopaedic", "orthopaedics", "ortho")):
        return True
    if "taxonomy_207X" in normalize_text(row.get("match_reason", "")) and any(
        term in name_text for term in ("bone and joint", "sports medicine")
    ):
        return True
    return False


def is_ortho_branded_keep(row: dict) -> bool:
    name_text = normalize_text(row.get("practice_name", "")).lower()
    if any(
        term in name_text
        for term in (
            "orthopedic",
            "orthopaedic",
            "orthopaedics",
            "orthopedic institute",
            "orthopaedic institute",
            "bone and joint",
        )
    ):
        return True
    if "taxonomy_207X" in normalize_text(row.get("match_reason", "")) and any(
        term in name_text for term in ("sports medicine", "spine", "neurospine")
    ):
        return True
    return False


def rows_match(row_a: dict, row_b: dict) -> bool:
    same_name = (
        row_a["norm_name"] == row_b["norm_name"]
        and row_a["norm_city"] == row_b["norm_city"]
        and row_a["norm_state"] == row_b["norm_state"]
    )
    if not same_name:
        return False

    same_phone = row_a["norm_phone"] and row_a["norm_phone"] == row_b["norm_phone"]
    same_street = row_a["norm_street"] and row_a["norm_street"] == row_b["norm_street"]
    same_parent_zip = (
        row_a["norm_parent_org"]
        and row_a["norm_parent_org"] == row_b["norm_parent_org"]
        and row_a["norm_zip"]
        and row_a["norm_zip"] == row_b["norm_zip"]
    )
    return same_phone or same_street or same_parent_zip


def cluster_rows(rows: list[dict]) -> list[list[dict]]:
    buckets = defaultdict(list)
    for row in rows:
        key = (row["norm_name"], row["norm_city"], row["norm_state"])
        buckets[key].append(row)

    clusters = []
    for bucket_rows in buckets.values():
        bucket_clusters = []
        for row in bucket_rows:
            matched_cluster = None
            for cluster in bucket_clusters:
                if any(rows_match(row, existing) for existing in cluster):
                    matched_cluster = cluster
                    break
            if matched_cluster is None:
                bucket_clusters.append([row])
            else:
                matched_cluster.append(row)
        clusters.extend(bucket_clusters)
    return clusters


def practice_clusters_match(cluster_a: list[dict], cluster_b: list[dict]) -> bool:
    row_a = cluster_a[0]
    row_b = cluster_b[0]
    if row_a["norm_name"] != row_b["norm_name"] or row_a["norm_state"] != row_b["norm_state"]:
        return False

    if all(is_ortho_branded(row) for row in (row_a, row_b)):
        return True

    if all("taxonomy_207X" in normalize_text(row.get("match_reason", "")) for row in (row_a, row_b)):
        return True

    phones_a = {row["norm_phone"] for row in cluster_a if row["norm_phone"]}
    phones_b = {row["norm_phone"] for row in cluster_b if row["norm_phone"]}
    parents_a = {row["norm_parent_org"] for row in cluster_a if row["norm_parent_org"]}
    parents_b = {row["norm_parent_org"] for row in cluster_b if row["norm_parent_org"]}

    return bool(phones_a & phones_b) or bool(parents_a & parents_b)


def roll_up_practice_clusters(clusters: list[list[dict]]) -> list[list[dict]]:
    practice_clusters = []
    for cluster in clusters:
        matched_cluster = None
        for existing in practice_clusters:
            if practice_clusters_match(cluster, existing):
                matched_cluster = existing
                break
        if matched_cluster is None:
            practice_clusters.append(list(cluster))
        else:
            matched_cluster.extend(cluster)
    return practice_clusters


def final_merge_exact_variants(clusters: list[list[dict]]) -> list[list[dict]]:
    merged = []
    for cluster in clusters:
        canonical = choose_canonical_row(cluster)
        matched_cluster = None
        for existing in merged:
            existing_canonical = choose_canonical_row(existing)
            same_name = canonical["norm_name"] == existing_canonical["norm_name"]
            same_city = canonical["norm_city"] == existing_canonical["norm_city"]
            same_state = canonical["norm_state"] == existing_canonical["norm_state"]
            same_street = canonical["norm_street"] and canonical["norm_street"] == existing_canonical["norm_street"]
            same_phone = canonical["norm_phone"] and canonical["norm_phone"] == existing_canonical["norm_phone"]
            if same_name and same_city and same_state and (same_street or same_phone):
                matched_cluster = existing
                break
        if matched_cluster is None:
            merged.append(list(cluster))
        else:
            matched_cluster.extend(cluster)
    return merged


def row_score(row: dict) -> tuple:
    match_reason = normalize_text(row.get("match_reason", ""))
    address_score = int(bool(row.get("combined_street"))) + int(bool(row.get("city"))) + int(bool(row.get("zip_code")))
    return (
        int(row.get("confidence_tier") == "high"),
        int("taxonomy_207X" in match_reason),
        int(bool(row.get("phone"))),
        address_score,
        len(normalize_text(row.get("practice_name", ""))),
        int(normalize_text(row.get("is_organization_subpart", "")).upper() != "Y"),
    )


def choose_canonical_row(rows: list[dict]) -> dict:
    return max(rows, key=row_score)


def count_unique_locations(rows: list[dict]) -> int:
    locations = set()
    for row in rows:
        key = (
            row.get("norm_street", ""),
            row.get("norm_city", ""),
            row.get("norm_state", ""),
            row.get("norm_zip", ""),
        )
        if any(key):
            locations.add(key)
    return len(locations)


def load_rows() -> tuple[list[dict], dict]:
    input_row_count = 0
    false_positive_rows_dropped = 0
    cleaned_rows = []

    with CANDIDATES_PATH.open("r", encoding="utf-8", newline="") as src:
        reader = csv.DictReader(src)
        for row in reader:
            input_row_count += 1
            enriched = enrich_row(row)
            if is_false_positive(enriched):
                false_positive_rows_dropped += 1
                continue
            cleaned_rows.append(enriched)

    summary = {
        "input_row_count": input_row_count,
        "rows_after_false_positive_filter": len(cleaned_rows),
        "false_positive_rows_dropped": false_positive_rows_dropped,
    }
    return cleaned_rows, summary


def write_outputs(practice_clusters: list[list[dict]], summary: dict) -> None:
    fieldnames = [
        "practice_id",
        "practice_name",
        "phone",
        "street",
        "city",
        "state",
        "zip_code",
        "website",
        "location_count",
        "source",
        "source_url",
    ]

    multi_location_practice_count = 0
    rows_merged = 0

    with DEDUPED_PATH.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for cluster in practice_clusters:
            canonical = choose_canonical_row(cluster)
            location_count = count_unique_locations(cluster)
            if location_count > 1:
                multi_location_practice_count += 1
            rows_merged += len(cluster) - 1

            writer.writerow(
                {
                    "practice_id": canonical["npi"],
                    "practice_name": canonical["practice_name"],
                    "phone": canonical["phone"],
                    "street": canonical["combined_street"],
                    "city": canonical["city"],
                    "state": canonical["state"],
                    "zip_code": canonical["zip_code"],
                    "website": "",
                    "location_count": location_count or 1,
                    "source": "nppes",
                    "source_url": f"https://npiregistry.cms.hhs.gov/provider-view/{canonical['npi']}",
                }
            )

    summary.update(
        {
            "office_level_cluster_count": len(practice_clusters),
            "final_deduped_count": len(practice_clusters),
            "rows_merged": rows_merged,
            "multi_location_practice_count": multi_location_practice_count,
        }
    )

    with SUMMARY_PATH.open("w", encoding="utf-8") as dst:
        json.dump(summary, dst, indent=2, sort_keys=True)


def main() -> None:
    rows, summary = load_rows()
    office_clusters = cluster_rows(rows)
    practice_clusters = roll_up_practice_clusters(office_clusters)
    practice_clusters = final_merge_exact_variants(practice_clusters)
    write_outputs(practice_clusters, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
