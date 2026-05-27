"""中文说明：
本脚本检查 IntH2_total 是否等于各层 IntH2_Li 之和。
验证条件为 abs(IntH2_total - sum(IntH2_Li)) / IntH2_total < 1e-3。
未通过验证的 case 标记为 failed_validation，不能进入论文图表。
"""

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INFILE = ROOT / "data" / "processed" / "metrics_table.csv"
OUTFILE = ROOT / "data" / "validation" / "layerwise_intH2_validation.csv"


def f(value):
    try:
        text = str(value).strip()
        return float(text) if text else math.nan
    except ValueError:
        return math.nan


def finite(value):
    return math.isfinite(value)


def fmt(value):
    return "" if not finite(value) else f"{value:.9g}"


def main():
    parser = argparse.ArgumentParser(description="Validate IntH2_total against layerwise sum.")
    parser.add_argument("--infile", type=Path, default=INFILE)
    parser.add_argument("--out", type=Path, default=OUTFILE)
    parser.add_argument("--rtol", type=float, default=1e-3)
    args = parser.parse_args()

    with args.infile.open("r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    out_rows = []
    for row in rows:
        total = f(row.get("IntH2_total", ""))
        layer_values = [f(row.get(f"IntH2_L{i}", "")) for i in range(1, 7)]
        layer_values = [v for v in layer_values if finite(v)]
        layer_sum = sum(layer_values) if layer_values else math.nan
        rel = abs(total - layer_sum) / abs(total) if finite(total) and finite(layer_sum) and abs(total) > 0 else math.nan
        if not finite(total) and not layer_values:
            status = "missing"
        elif finite(rel) and rel < args.rtol:
            status = "passed"
        else:
            status = "failed_validation"
        out_rows.append({
            "case_id": row["case_id"],
            "IntH2_total": fmt(total),
            "sum_IntH2_Li": fmt(layer_sum),
            "relative_error": fmt(rel),
            "validation_status": status,
            "used_in_paper": "no" if status != "passed" else row.get("used_in_paper", "no"),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
