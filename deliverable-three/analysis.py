from __future__ import annotations

import csv
from pathlib import Path


DEFAULT_CSV_PATH = Path(__file__).parent / "outputs" / "orthopedic_practices_with_failure_modes.csv"


def percentage(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def main() -> None:
    with DEFAULT_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    confidence_rows = [row for row in rows if (row.get("confidence") or "").strip()]
    failure_mode_rows = [row for row in rows if (row.get("failure_modes") or "").strip()]

    confidence_h = sum(1 for row in confidence_rows if row.get("confidence") == "H")
    confidence_m = sum(1 for row in confidence_rows if row.get("confidence") == "M")
    confidence_l = sum(1 for row in confidence_rows if row.get("confidence") == "L")

    failure_mode_1 = sum(1 for row in failure_mode_rows if row.get("failure_modes") == "1")
    failure_mode_2 = sum(1 for row in failure_mode_rows if row.get("failure_modes") == "2")
    failure_mode_3 = sum(1 for row in failure_mode_rows if row.get("failure_modes") == "3")

    print("===========================================ANALYSIS RESULTS===========================================")
    print(f"Source file:                                {DEFAULT_CSV_PATH}")
    print(f"Rows with confidence populated:             {len(confidence_rows)}")
    print(f"High Confidence (H):                        {percentage(confidence_h, len(confidence_rows)):.2f}%")
    print(f"Medium Confidence (M):                      {percentage(confidence_m, len(confidence_rows)):.2f}%")
    print(f"Low Confidence (L):                         {percentage(confidence_l, len(confidence_rows)):.2f}%")
    print(f"Rows with failure_modes populated:          {len(failure_mode_rows)}")
    print(f"Failure Mode 1:                             {percentage(failure_mode_1, len(failure_mode_rows)):.2f}%")
    print(f"Failure Mode 2:                             {percentage(failure_mode_2, len(failure_mode_rows)):.2f}%")
    print(f"Failure Mode 3:                             {percentage(failure_mode_3, len(failure_mode_rows)):.2f}%")
    print("======================================================================================================")


if __name__ == "__main__":
    main()
