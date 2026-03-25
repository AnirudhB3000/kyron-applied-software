import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

NPIDATA_PATH = DATA_DIR / "npidata_pfile_20050523-20260308.csv"
PL_PATH = DATA_DIR / "pl_pfile_20050523-20260308.csv"

CANDIDATES_PATH = OUTPUT_DIR / "orthopedic_candidates.csv"
FINAL_PATH = OUTPUT_DIR / "orthopedic_practices_base.csv"
QA_SUMMARY_PATH = OUTPUT_DIR / "orthopedic_qa_summary.json"

HIGH_NAME_TERMS = ("orthopedic", "orthopaedic", "ortho")
MEDIUM_NAME_TERMS = ("sports medicine", "spine", "joint", "musculoskeletal")


def normalize_text(value: str) -> str:
    return (value or "").strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits[:10] if len(digits) >= 10 else ""


def normalize_zip(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits[:5]


def collect_taxonomy_codes(row: dict) -> list[str]:
    codes = []
    for i in range(1, 16):
        value = normalize_text(row.get(f"Healthcare Provider Taxonomy Code_{i}", ""))
        if value:
            codes.append(value)
    return codes


def collect_taxonomy_groups(row: dict) -> list[str]:
    groups = []
    for i in range(1, 16):
        value = normalize_text(row.get(f"Healthcare Provider Taxonomy Group_{i}", ""))
        if value:
            groups.append(value)
    return groups


def classify_candidate(row: dict) -> tuple[str, str] | None:
    if normalize_text(row.get("Entity Type Code", "")) != "2":
        return None

    legal_name = normalize_text(row.get("Provider Organization Name (Legal Business Name)", ""))
    other_name = normalize_text(row.get("Provider Other Organization Name", ""))
    name_text = f"{legal_name} {other_name}".lower()
    tax_codes = collect_taxonomy_codes(row)

    reasons = []
    if any(code.startswith("207X") for code in tax_codes):
        reasons.append("taxonomy_207X")
    if any(term in name_text for term in HIGH_NAME_TERMS):
        reasons.append("name_ortho")
    if reasons:
        return "high", "+".join(sorted(set(reasons)))

    if any(code.startswith("2086S") for code in tax_codes):
        reasons.append("taxonomy_2086S")
    if any(term in name_text for term in MEDIUM_NAME_TERMS):
        reasons.append("name_broader_msk")
    if reasons:
        return "medium", "+".join(sorted(set(reasons)))

    return None


def iter_candidate_rows():
    with NPIDATA_PATH.open("r", encoding="utf-8", newline="") as src:
        reader = csv.DictReader(src)
        for index, row in enumerate(reader, start=1):
            if index % 250000 == 0:
                print(f"scanned {index:,} npidata rows")

            result = classify_candidate(row)
            if not result:
                continue

            tier, reason = result
            practice_phone = normalize_phone(
                row.get("Provider Business Practice Location Address Telephone Number", "")
            )
            mailing_phone = normalize_phone(
                row.get("Provider Business Mailing Address Telephone Number", "")
            )
            taxonomy_codes = sorted(set(collect_taxonomy_codes(row)))
            taxonomy_groups = sorted(set(collect_taxonomy_groups(row)))

            yield {
                "npi": normalize_text(row.get("NPI", "")),
                "confidence_tier": tier,
                "match_reason": reason,
                "practice_name": normalize_text(
                    row.get("Provider Organization Name (Legal Business Name)", "")
                ),
                "other_name": normalize_text(row.get("Provider Other Organization Name", "")),
                "phone": practice_phone or mailing_phone,
                "street_1": normalize_text(
                    row.get("Provider First Line Business Practice Location Address", "")
                ),
                "street_2": normalize_text(
                    row.get("Provider Second Line Business Practice Location Address", "")
                ),
                "city": normalize_text(
                    row.get("Provider Business Practice Location Address City Name", "")
                ),
                "state": normalize_text(
                    row.get("Provider Business Practice Location Address State Name", "")
                ).upper(),
                "zip_code": normalize_zip(
                    row.get("Provider Business Practice Location Address Postal Code", "")
                ),
                "parent_organization": normalize_text(row.get("Parent Organization LBN", "")),
                "is_organization_subpart": normalize_text(row.get("Is Organization Subpart", "")),
                "taxonomy_codes": "|".join(taxonomy_codes),
                "taxonomy_groups": "|".join(taxonomy_groups),
                "source": "nppes_npidata",
            }


def extract_candidates() -> tuple[set[str], dict]:
    fieldnames = [
        "npi",
        "confidence_tier",
        "match_reason",
        "practice_name",
        "other_name",
        "phone",
        "street_1",
        "street_2",
        "city",
        "state",
        "zip_code",
        "parent_organization",
        "is_organization_subpart",
        "taxonomy_codes",
        "taxonomy_groups",
        "source",
    ]

    candidate_npis = set()
    tier_counts = Counter()
    reason_counts = Counter()
    missing_phone = 0
    missing_address = 0
    duplicate_npi_rows = 0

    with CANDIDATES_PATH.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for candidate in iter_candidate_rows():
            npi = candidate["npi"]
            if npi in candidate_npis:
                duplicate_npi_rows += 1
                continue

            writer.writerow(candidate)
            candidate_npis.add(npi)
            tier_counts[candidate["confidence_tier"]] += 1
            reason_counts[candidate["match_reason"]] += 1

            if not candidate["phone"]:
                missing_phone += 1
            if not (candidate["street_1"] or candidate["city"] or candidate["state"]):
                missing_address += 1

    summary = {
        "candidate_count": len(candidate_npis),
        "tier_counts": dict(tier_counts),
        "reason_counts": dict(reason_counts.most_common(25)),
        "missing_phone_count": missing_phone,
        "missing_address_count": missing_address,
        "duplicate_npi_rows_skipped": duplicate_npi_rows,
    }
    return candidate_npis, summary


def build_location_counts(candidate_npis: set[str]) -> dict[str, int]:
    secondary_counts = defaultdict(int)

    with PL_PATH.open("r", encoding="utf-8", newline="") as src:
        reader = csv.DictReader(src)
        for index, row in enumerate(reader, start=1):
            if index % 250000 == 0:
                print(f"scanned {index:,} pl rows")

            npi = normalize_text(row.get("NPI", ""))
            if npi in candidate_npis:
                secondary_counts[npi] += 1

    return dict(secondary_counts)


def export_final(location_counts: dict[str, int]) -> dict:
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

    final_count = 0
    missing_phone = 0
    missing_address = 0

    with CANDIDATES_PATH.open("r", encoding="utf-8", newline="") as src, FINAL_PATH.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            street = " ".join(part for part in [row["street_1"], row["street_2"]] if part).strip()
            has_primary_address = bool(row["street_1"] or row["city"] or row["state"])
            location_count = location_counts.get(row["npi"], 0) + (1 if has_primary_address else 0)

            writer.writerow(
                {
                    "practice_id": row["npi"],
                    "practice_name": row["practice_name"],
                    "phone": row["phone"],
                    "street": street,
                    "city": row["city"],
                    "state": row["state"],
                    "zip_code": row["zip_code"],
                    "website": "",
                    "location_count": location_count,
                    "source": "nppes",
                    "source_url": "",
                }
            )

            final_count += 1
            if not row["phone"]:
                missing_phone += 1
            if not (street or row["city"] or row["state"]):
                missing_address += 1

    return {
        "final_count": final_count,
        "final_missing_phone_count": missing_phone,
        "final_missing_address_count": missing_address,
    }


def write_qa_summary(summary: dict) -> None:
    with QA_SUMMARY_PATH.open("w", encoding="utf-8") as dst:
        json.dump(summary, dst, indent=2, sort_keys=True)


def main() -> None:
    candidate_npis, extract_summary = extract_candidates()
    location_counts = build_location_counts(candidate_npis)
    final_summary = export_final(location_counts)

    combined_summary = {
        **extract_summary,
        **final_summary,
        "location_count_records": len(location_counts),
    }
    write_qa_summary(combined_summary)

    print(json.dumps(combined_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
