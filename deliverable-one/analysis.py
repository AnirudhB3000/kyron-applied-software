from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


DEFAULT_CSV_PATH = Path(__file__).parent / "outputs" / "final_orthopedic_practices.csv"
STATE_NORMALIZATION = {
    "TEXAS": "TX",
}


def percentage(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def main() -> None:
    with DEFAULT_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    total_entries = len(rows)
    state_counts = Counter()
    for row in rows:
        raw_state = (row.get("state") or "").strip()
        if not raw_state:
            continue
        normalized_state = STATE_NORMALIZATION.get(raw_state, raw_state)
        state_counts[normalized_state] += 1

    print("===========================================ANALYSIS RESULTS===========================================")
    print(f"Source file:                                {DEFAULT_CSV_PATH}")
    print(f"Total Entries:                              {total_entries}")
    print("State Frequency (%):")

    for state, count in sorted(state_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {state}:                                  {percentage(count, total_entries):.2f}%")

    print("======================================================================================================")


if __name__ == "__main__":
    main()
