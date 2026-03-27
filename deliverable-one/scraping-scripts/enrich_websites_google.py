import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError


SCRIPT_DIR = Path(__file__).resolve().parent
DELIVERABLE_DIR = SCRIPT_DIR.parent
REPO_ROOT = DELIVERABLE_DIR.parent
ENV_PATH = REPO_ROOT / ".env"
INPUT_PATH = DELIVERABLE_DIR / "outputs" / "orthopedic_practices_deduped.csv"
OUTPUT_PATH = DELIVERABLE_DIR / "outputs" / "orthopedic_practices_with_websites.csv"
SUMMARY_PATH = DELIVERABLE_DIR / "outputs" / "website_enrichment_summary.json"
QUERY_CACHE_PATH = DELIVERABLE_DIR / "outputs" / "website_query_cache.json"
DETAILS_CACHE_PATH = DELIVERABLE_DIR / "outputs" / "website_details_cache.json"

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
API_KEY_NAMES = ("GOOGLE_MAPS_API_KEY", "GOOGLE_PLACES_API_KEY")
SLEEP_SECONDS = 0.1
MAX_RETRIES = 4
BACKOFF_SECONDS = 1.0
BATCH_SIZE = 50
BATCH_COOLDOWN_SECONDS = 10.0
MAX_ROWS = 1500


def normalize_text(value: str) -> str:
    return (value or "").strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits[:10] if len(digits) >= 10 else ""


def normalize_name(value: str) -> str:
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\b(inc|llc|pllc|pc|pa|corp|corporation|ltd|lp|llp)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize_name(value: str) -> set[str]:
    return {token for token in normalize_name(value).split() if token}


def load_env_file(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_api_key() -> str:
    env_values = load_env_file(ENV_PATH)
    for key_name in API_KEY_NAMES:
        value = env_values.get(key_name, "")
        if value:
            return value
    raise RuntimeError(
        f"Missing Google Maps API key in {ENV_PATH}. Expected one of: {', '.join(API_KEY_NAMES)}"
    )


def http_get_json(url: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    request_url = f"{url}?{query}"
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request_url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(BACKOFF_SECONDS * (2**attempt))
    raise RuntimeError(f"Request failed after retries: {request_url}") from last_error


def load_json_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_cache(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def text_search(api_key: str, query: str, query_cache: dict) -> list[dict]:
    if query in query_cache:
        return query_cache[query]
    payload = http_get_json(TEXT_SEARCH_URL, {"query": query, "key": api_key})
    results = payload.get("results", [])
    query_cache[query] = results
    return results


def place_details(api_key: str, place_id: str, details_cache: dict) -> dict:
    if place_id in details_cache:
        return details_cache[place_id]
    payload = http_get_json(
        DETAILS_URL,
        {
            "place_id": place_id,
            "fields": "name,website,formatted_phone_number,international_phone_number,url,formatted_address",
            "key": api_key,
        },
    )
    result = payload.get("result", {})
    details_cache[place_id] = result
    return result


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = left & right
    union = left | right
    return len(overlap) / len(union)


def name_match_score(practice_name: str, candidate_name: str) -> float:
    practice_norm = normalize_name(practice_name)
    candidate_norm = normalize_name(candidate_name)
    if not practice_norm or not candidate_norm:
        return 0.0
    if practice_norm == candidate_norm:
        return 1.0
    if practice_norm in candidate_norm or candidate_norm in practice_norm:
        return 0.9
    return jaccard_similarity(tokenize_name(practice_name), tokenize_name(candidate_name))


def candidate_score(row: dict, candidate: dict, details: dict) -> tuple[float, str]:
    score = 0.0
    reasons = []

    name_score = name_match_score(row["practice_name"], details.get("name", "") or candidate.get("name", ""))
    score += name_score * 5
    reasons.append(f"name={name_score:.2f}")

    address_blob = " ".join(
        [
            normalize_text(candidate.get("formatted_address", "")),
            normalize_text(details.get("formatted_address", "")),
        ]
    ).lower()
    if row["city"].lower() in address_blob:
        score += 1.0
        reasons.append("city")
    if row["state"].lower() in address_blob:
        score += 0.5
        reasons.append("state")

    row_phone = normalize_phone(row.get("phone", ""))
    details_phone = normalize_phone(
        details.get("formatted_phone_number", "") or details.get("international_phone_number", "")
    )
    if row_phone and details_phone and row_phone == details_phone:
        score += 3.0
        reasons.append("phone")

    if normalize_text(details.get("website", "")):
        score += 1.0
        reasons.append("website")

    return score, "+".join(reasons)


def accept_candidate(row: dict, details: dict, score: float) -> bool:
    if not normalize_text(details.get("website", "")):
        return False

    name_score = name_match_score(row["practice_name"], details.get("name", ""))
    row_phone = normalize_phone(row.get("phone", ""))
    details_phone = normalize_phone(
        details.get("formatted_phone_number", "") or details.get("international_phone_number", "")
    )
    phone_match = bool(row_phone and details_phone and row_phone == details_phone)

    if name_score >= 0.9 and (phone_match or score >= 6.0):
        return True
    if name_score >= 0.75 and phone_match:
        return True
    return False


def best_website_match(api_key: str, row: dict, query_cache: dict, details_cache: dict) -> tuple[str, str]:
    query = " ".join(
        part for part in [row["practice_name"], row["city"], row["state"]] if normalize_text(part)
    )
    try:
        candidates = text_search(api_key, query, query_cache)
    except RuntimeError:
        return "", "query_error"
    best_score = -1.0
    best_website = ""
    best_reason = ""

    for candidate in candidates[:5]:
        place_id = normalize_text(candidate.get("place_id", ""))
        if not place_id:
            continue
        try:
            details = place_details(api_key, place_id, details_cache)
        except RuntimeError:
            continue
        score, reason = candidate_score(row, candidate, details)
        if accept_candidate(row, details, score) and score > best_score:
            best_score = score
            best_website = normalize_text(details.get("website", ""))
            best_reason = reason
        time.sleep(SLEEP_SECONDS)

    return best_website, best_reason


def enrich_websites() -> None:
    api_key = load_api_key()
    summary = Counter()
    query_cache = load_json_cache(QUERY_CACHE_PATH)
    details_cache = load_json_cache(DETAILS_CACHE_PATH)

    with INPUT_PATH.open("r", encoding="utf-8", newline="") as src, OUTPUT_PATH.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(reader, start=1):
            if index > MAX_ROWS:
                break
            if index % 250 == 0:
                print(f"processed {index:,} rows")
            if index % BATCH_SIZE == 0:
                print(f"cooldown after {index:,} rows")
                save_json_cache(QUERY_CACHE_PATH, query_cache)
                save_json_cache(DETAILS_CACHE_PATH, details_cache)
                time.sleep(BATCH_COOLDOWN_SECONDS)

            website, match_reason = best_website_match(api_key, row, query_cache, details_cache)
            row["website"] = website
            writer.writerow(row)

            summary["rows_processed"] += 1
            if website:
                summary["websites_found"] += 1
            else:
                summary["websites_missing"] += 1
            if match_reason:
                summary[f"reason::{match_reason}"] += 1

    save_json_cache(QUERY_CACHE_PATH, query_cache)
    save_json_cache(DETAILS_CACHE_PATH, details_cache)

    with SUMMARY_PATH.open("w", encoding="utf-8") as dst:
        json.dump(dict(summary), dst, indent=2, sort_keys=True)

    print(json.dumps(dict(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    enrich_websites()
