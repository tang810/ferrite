"""中文说明：
本脚本基于 data/processed/main_dataset.csv 计算论文需要的派生指标，
包括 SFq、LeakageRatioq、Vf、etaS、etaS_star、rhoH 和 chiH。
正式 SF 按外场方向取对应分量计算：x 向用 Bx，z 向用 Bz；
Mag_B 只作为辅助检查，不作为正式 SF 的默认来源。
"""

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INFILE = ROOT / "data" / "processed" / "main_dataset.csv"
OUTFILE = ROOT / "data" / "processed" / "metrics_table.csv"


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


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def ferrite_volume(row):
    n = int(f(row["N_layers"]) if finite(f(row["N_layers"])) else 0)
    a = f(row["t_ferrite_mm"])
    g = f(row["g_radial_mm"])
    rin = f(row["Rin_mm"])
    length = f(row["H_mm"])
    coverage = f(row["coverage_phi"])
    if n <= 0 or not all(finite(v) for v in (a, rin, length)):
        return 0.0
    if not finite(g):
        g = 0.0
    if not finite(coverage) or coverage <= 0:
        coverage = 1.0
    total = 0.0
    for i in range(n):
        r_in = rin + i * (a + g)
        r_out = r_in + a
        total += math.pi * length * (r_out * r_out - r_in * r_in)
    return total * coverage


def directional_values(row):
    q = row["external_field_direction"]
    if q == "x":
        return f(row["B0_Bx_T"]), f(row["Bcenter_Bx_T"])
    if q == "z":
        return f(row["B0_Bz_T"]), f(row["Bcenter_Bz_T"])
    if q == "y":
        return f(row["B0_By_T"]), f(row["Bcenter_By_T"])
    return math.nan, math.nan


def main():
    parser = argparse.ArgumentParser(description="Compute metrics for ferrite paper dataset.")
    parser.add_argument("--infile", type=Path, default=INFILE)
    parser.add_argument("--out", type=Path, default=OUTFILE)
    parser.add_argument("--vref-case", default="C1_N1_t060_x")
    args = parser.parse_args()

    rows = read_csv(args.infile)
    volumes = {row["case_id"]: ferrite_volume(row) for row in rows}
    vref = volumes.get(args.vref_case, math.nan)
    if not finite(vref) or vref <= 0:
        vref = math.nan

    out_rows = []
    for row in rows:
        out = dict(row)
        vf = volumes[row["case_id"]]
        b0_q, bc_q = directional_values(row)
        sf = abs(b0_q) / abs(bc_q) if finite(b0_q) and finite(bc_q) and abs(bc_q) > 0 else math.nan
        leakage = abs(bc_q) / abs(b0_q) if finite(b0_q) and finite(bc_q) and abs(b0_q) > 0 else math.nan
        ln_sf = math.log(sf) if finite(sf) and sf > 0 else math.nan
        int_h2 = f(row.get("IntH2_total", ""))

        eta_s = ln_sf / vf if finite(ln_sf) and vf > 0 else math.nan
        eta_s_star = (vref / vf) * ln_sf if finite(vref) and finite(ln_sf) and vf > 0 else math.nan
        rho_h = int_h2 / vf if finite(int_h2) and vf > 0 else math.nan
        chi_h = int_h2 / ln_sf if finite(int_h2) and finite(ln_sf) and abs(ln_sf) > 0 else math.nan

        q = row["external_field_direction"]
        out["Vf_mm3"] = fmt(vf)
        out["SFq"] = fmt(sf)
        out[f"SF{q}"] = fmt(sf)
        out["LeakageRatioq"] = fmt(leakage)
        out[f"LeakageRatio{q}"] = fmt(leakage)
        out["etaS"] = fmt(eta_s)
        out["etaS_star"] = fmt(eta_s_star)
        out["rhoH"] = fmt(rho_h)
        out["chiH"] = fmt(chi_h)
        out["metric_status"] = "processed" if finite(sf) else "missing"
        out["used_in_paper"] = "no"
        out_rows.append(out)

    fieldnames = []
    for row in out_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
