import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
OUTFILE = ROOT / "data" / "validation" / "B0_reference_validation.csv"


def f(value):
    try:
        text = str(value).strip()
        return float(text) if text else math.nan
    except ValueError:
        return math.nan


def finite(value):
    return math.isfinite(value)


def read_first(path):
    if not path.exists():
        return None
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    return rows[0] if rows else None


def validate(row, direction, dominance_ratio):
    if row is None:
        return "missing", "reference file missing"
    bx, by, bz = abs(f(row.get("B0_Bx_T", ""))), abs(f(row.get("B0_By_T", ""))), abs(f(row.get("B0_Bz_T", "")))
    if direction == "x":
        primary, transverse = bx, max(by if finite(by) else 0, bz if finite(bz) else 0)
    else:
        primary, transverse = bz, max(bx if finite(bx) else 0, by if finite(by) else 0)
    if not finite(primary):
        return "missing", "primary component missing"
    if transverse == 0 or primary >= dominance_ratio * transverse:
        return "passed", "primary component dominates"
    return "failed_validation", "primary component does not dominate transverse leakage"


def main():
    parser = argparse.ArgumentParser(description="Validate B0 reference directionality.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUTFILE)
    parser.add_argument("--dominance-ratio", type=float, default=10.0)
    args = parser.parse_args()

    rows = []
    for direction in ("x", "z"):
        row = read_first(args.raw_dir / f"B0_reference_{direction}.csv")
        status, notes = validate(row, direction, args.dominance_ratio)
        rows.append({
            "reference": f"B0_reference_{direction}",
            "field_dir": direction,
            "validation_status": status,
            "notes": notes,
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
