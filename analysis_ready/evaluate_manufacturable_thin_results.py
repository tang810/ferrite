"""Evaluate manufacturable thin-shell center-field exports.

Chinese note:
本脚本只用于排查 B0/SF 数据链路。正式 transverse shielding factor
必须使用 x 分量：
SFx = abs(B0_Bx_T) / abs(Bcenter_Bx_T)
LeakageRatiox = abs(Bcenter_Bx_T) / abs(B0_Bx_T)
Mag_B/B0_Mag_T 只能作为辅助检查量，不能作为正式 SF 依据。
"""

import csv
import math
from pathlib import Path


BASE_DIR = Path(r"D:\tangyumengnew\aaaaaaaaximukeji")
EXPORTED_CSV = BASE_DIR / "analysis_ready" / "manufacturable_thin_center_fields_exported.csv"
TEMPLATE_CSV = BASE_DIR / "analysis_ready" / "manufacturable_thin_center_fields_template.csv"
IN_CSV = EXPORTED_CSV if EXPORTED_CSV.exists() else TEMPLATE_CSV
OUT_CSV = BASE_DIR / "analysis_ready" / "manufacturable_thin_evaluated.csv"

RIN_MM = 100.0
H_MM = 200.0


def as_float(value):
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return math.nan
    return float(text)


def finite(value):
    return math.isfinite(value)


def magnitude(x, y, z):
    if all(finite(v) for v in (x, y, z)):
        return math.sqrt(x * x + y * y + z * z)
    return math.nan


def ratio(numerator, denominator):
    if finite(numerator) and finite(denominator) and abs(denominator) > 0:
        return abs(numerator) / abs(denominator)
    return math.nan


def fmt(value):
    if not finite(value):
        return ""
    return "{:.9g}".format(value)


def direction_status(b0_bx, b0_by, b0_bz, dominance_ratio=10.0):
    if not finite(b0_bx):
        return "failed", "B0_Bx_T missing"
    transverse = max(abs(b0_by) if finite(b0_by) else 0.0, abs(b0_bz) if finite(b0_bz) else 0.0)
    if transverse == 0.0 or abs(b0_bx) >= dominance_ratio * transverse:
        return "passed", "B0_Bx_T dominates transverse components"
    return "failed", "B0_Bx_T does not dominate B0_By_T/B0_Bz_T; external-field direction or B0 model is suspect"


def ferrite_volume(layer_count, a_mm, g_mm, coverage_phi):
    if layer_count <= 0 or not finite(a_mm) or a_mm <= 0:
        return 0.0
    g = 0.0 if not finite(g_mm) else g_mm
    coverage = 1.0 if not finite(coverage_phi) or coverage_phi <= 0 else coverage_phi
    total = 0.0
    for i in range(layer_count):
        r_inner = RIN_MM + i * (a_mm + g)
        r_outer = r_inner + a_mm
        total += math.pi * H_MM * (r_outer * r_outer - r_inner * r_inner)
    return total * coverage


def main():
    with IN_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    evaluated = []
    common_b0 = {"T": math.nan, "Bx": math.nan, "By": math.nan, "Bz": math.nan}
    for row in rows:
        layer = int(as_float(row["layer"]))
        a = as_float(row["a_mm"])
        g = as_float(row["g_mm"])
        coverage = as_float(row["coverage_phi"])

        b0_t = as_float(row.get("B0_T", row.get("B0_Mag_T", "")))
        b0_bx = as_float(row.get("B0_Bx_T", ""))
        b0_by = as_float(row.get("B0_By_T", ""))
        b0_bz = as_float(row.get("B0_Bz_T", ""))
        bc_t = as_float(row.get("Bcenter_T", row.get("Bcenter_Mag_T", "")))
        bc_bx = as_float(row.get("Bcenter_Bx_T", ""))
        bc_by = as_float(row.get("Bcenter_By_T", ""))
        bc_bz = as_float(row.get("Bcenter_Bz_T", ""))

        if finite(b0_t):
            common_b0["T"] = b0_t
        elif finite(common_b0["T"]):
            b0_t = common_b0["T"]

        if finite(b0_bx):
            common_b0["Bx"] = b0_bx
        elif finite(common_b0["Bx"]):
            b0_bx = common_b0["Bx"]

        if finite(b0_by):
            common_b0["By"] = b0_by
        elif finite(common_b0["By"]):
            b0_by = common_b0["By"]

        if finite(b0_bz):
            common_b0["Bz"] = b0_bz
        elif finite(common_b0["Bz"]):
            b0_bz = common_b0["Bz"]

        if not finite(b0_t):
            b0_t = magnitude(b0_bx, b0_by, b0_bz)
        if not finite(bc_t):
            bc_t = magnitude(bc_bx, bc_by, bc_bz)

        sf_x = ratio(b0_bx, bc_bx)
        leakage_x = ratio(bc_bx, b0_bx)
        b0_status, b0_notes = direction_status(b0_bx, b0_by, b0_bz)
        if not finite(sf_x):
            sf_status = "failed"
            sf_notes = "SFx cannot be computed from B0_Bx_T and Bcenter_Bx_T"
        elif sf_x < 1.0:
            sf_status = "failed"
            sf_notes = "SFx < 1; verify B0/shield field direction, center point, vacuum B0 model, Mag_B misuse, and re-solve state"
        else:
            sf_status = "processed"
            sf_notes = "SFx computed from x components"
        volume = ferrite_volume(layer, a, g, coverage)
        total_ferrite_t = layer * a if layer > 0 and finite(a) else 0.0
        eta_s = math.log(sf_x) / volume if finite(sf_x) and sf_x > 0 and volume > 0 else math.nan
        eta_se = 20.0 * math.log10(sf_x) / volume if finite(sf_x) and sf_x > 0 and volume > 0 else math.nan

        out = dict(row)
        out["B0_T_used"] = fmt(b0_t)
        out["Bcenter_T_used"] = fmt(bc_t)
        out["B0_direction_validation"] = b0_status
        out["B0_direction_notes"] = b0_notes
        out["SFx"] = fmt(sf_x)
        out["LeakageRatiox"] = fmt(leakage_x)
        out["SF_status"] = sf_status if b0_status == "passed" else "failed"
        out["SF_notes"] = sf_notes if b0_status == "passed" else b0_notes
        out["SF_Mag_aux"] = fmt(ratio(b0_t, bc_t))
        out["LeakageRatio_Mag_aux"] = fmt(ratio(bc_t, b0_t))
        out["MaterialVolume_mm3"] = fmt(volume)
        out["TotalFerriteThickness_mm"] = fmt(total_ferrite_t)
        out["eta_lnS_per_mm3"] = fmt(eta_s)
        out["eta_dB_per_mm3"] = fmt(eta_se)
        evaluated.append(out)

    fieldnames = list(evaluated[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(evaluated)

    print("Wrote {}".format(OUT_CSV))


if __name__ == "__main__":
    main()
