from __future__ import annotations

import csv
from pathlib import Path


DEFAULT_CSV_PATH = Path(__file__).parent / "outputs" / "orthopedic_practices_with_scheduling_info.csv"


def percentage(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def main() -> None:
    with DEFAULT_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    attempted_rows = [row for row in rows if row.get("call_attempted") == "Y"]
    completed_yes = sum(1 for row in attempted_rows if row.get("call_completed") == "Y")

    combined_entrypoints: list[str] = []
    for row in attempted_rows:
        for column in ("working_hours_entrypoint", "after_hours_entrypoint"):
            value = (row.get(column) or "").strip()
            if value:
                combined_entrypoints.append(value)

    ivr_count = sum(1 for value in combined_entrypoints if value == "IVR")
    human_count = sum(1 for value in combined_entrypoints if value == "Human")

    print("===========================================ANALYSIS RESULTS===========================================")
    print(f"Source file:                                {DEFAULT_CSV_PATH}")
    print(f"Total Attempted Calls:                      {len(attempted_rows)}")
    print(f"Completed Calls:                            {percentage(completed_yes, len(attempted_rows)):.2f}%")
    print(f"IVR Responses (working and after hours):    {percentage(ivr_count, len(combined_entrypoints)):.2f}%")
    print(f"Human Responses (working and after hours):  {percentage(human_count, len(combined_entrypoints)):.2f}%")
    print("======================================================================================================")


if __name__ == "__main__":
    main()
