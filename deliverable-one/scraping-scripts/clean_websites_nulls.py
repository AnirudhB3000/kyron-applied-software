import csv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DELIVERABLE_DIR = SCRIPT_DIR.parent
INPUT_PATH = DELIVERABLE_DIR / "outputs" / "orthopedic_practices_with_websites.csv"
OUTPUT_PATH = DELIVERABLE_DIR / "outputs" / "final_orthopedic_practices.csv"


def clean_websites() -> None:
    with INPUT_PATH.open("r", encoding="utf-8", newline="") as src, OUTPUT_PATH.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if not (row.get("website") or "").strip():
                row["website"] = "null"
            writer.writerow(row)


if __name__ == "__main__":
    clean_websites()
