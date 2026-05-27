"""中文说明：
本脚本检查 B0 reference 是否真的代表目标外场方向。
x 向 reference 要求 B0_Bx 显著大于 B0_By/B0_Bz；
z 向 reference 要求 B0_Bz 显著大于 B0_Bx/B0_By。
缺失或方向不合格的 reference 会阻止对应方向进入论文结果。
"""

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
        return "missing", "reference file missing", math.nan, math.nan, math.nan, math.nan
    bx, by, bz = abs(f(row.get("B0_Bx_T", ""))), abs(f(row.get("B0_By_T", ""))), abs(f(row.get("B0_Bz_T", "")))
    if direction == "x":
        primary, transverse = bx, max(by if finite(by) else 0, bz if finite(bz) else 0)
    else:
        primary, transverse = bz, max(bx if finite(bx) else 0, by if finite(by) else 0)
    if not finite(primary):
        return "missing", "primary component missing", bx, by, bz, math.nan
    ratio = primary / transverse if transverse > 0 else math.inf
    if transverse == 0 or primary >= dominance_ratio * transverse:
        return "passed", "primary component dominates", bx, by, bz, ratio
    return "failed_validation", "primary component does not dominate transverse components", bx, by, bz, ratio


def main():
    parser = argparse.ArgumentParser(description="Validate B0 reference directionality.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUTFILE)
    parser.add_argument("--dominance-ratio", type=float, default=10.0)
    args = parser.parse_args()

    rows = []
    for direction in ("x", "z"):
        row = read_first(args.raw_dir / f"B0_reference_{direction}.csv")
        status, notes, bx, by, bz, ratio = validate(row, direction, args.dominance_ratio)
        rows.append({
            "reference": f"B0_reference_{direction}",
            "field_dir": direction,
            "abs_B0_Bx_T": "" if not finite(bx) else f"{bx:.9g}",
            "abs_B0_By_T": "" if not finite(by) else f"{by:.9g}",
            "abs_B0_Bz_T": "" if not finite(bz) else f"{bz:.9g}",
            "primary_to_largest_transverse_ratio": "" if not finite(ratio) else f"{ratio:.9g}",
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
