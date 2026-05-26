import csv
import math
from pathlib import Path


BASE_DIR = Path(r"D:\tangyumengnew\aaaaaaaaximukeji")
IN_CSV = BASE_DIR / "analysis_ready" / "formal_sf_fixedT10_g02_N1_N4_center_fields_template.csv"
OUT_CSV = BASE_DIR / "analysis_ready" / "formal_sf_fixedT10_g02_N1_N4_evaluated.csv"


def as_float(value):
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return math.nan
    return float(text)


def magnitude(x, y, z):
    values = [x, y, z]
    if all(math.isfinite(v) for v in values):
        return math.sqrt(x * x + y * y + z * z)
    return math.nan


def ratio(numerator, denominator):
    if math.isfinite(numerator) and math.isfinite(denominator) and abs(denominator) > 0:
        return abs(numerator) / abs(denominator)
    return math.nan


def fmt(value):
    if not math.isfinite(value):
        return ""
    return "{:.9g}".format(value)


def main():
    with IN_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError("No rows found: {}".format(IN_CSV))

    evaluated = []
    single_volume = math.nan
    single_sf = math.nan
    single_int_h2 = math.nan

    for row in rows:
        layer = int(as_float(row["layer"]))
        volume = as_float(row["material_volume_mm3"])

        b0_t = as_float(row.get("B0_T", ""))
        b0_bx = as_float(row.get("B0_Bx_T", ""))
        b0_by = as_float(row.get("B0_By_T", ""))
        b0_bz = as_float(row.get("B0_Bz_T", ""))
        bc_t = as_float(row.get("Bcenter_T", ""))
        bc_bx = as_float(row.get("Bcenter_Bx_T", ""))
        bc_by = as_float(row.get("Bcenter_By_T", ""))
        bc_bz = as_float(row.get("Bcenter_Bz_T", ""))

        if not math.isfinite(b0_t):
            b0_t = magnitude(b0_bx, b0_by, b0_bz)
        if not math.isfinite(bc_t):
            bc_t = magnitude(bc_bx, bc_by, bc_bz)

        sf = ratio(b0_t, bc_t)
        residual = ratio(bc_t, b0_t)
        int_h2 = as_float(row.get("IntH2_total", ""))

        if layer == 1:
            single_volume = volume
            single_sf = sf
            single_int_h2 = int_h2

        out = dict(row)
        out["B0_T_used"] = fmt(b0_t)
        out["Bcenter_T_used"] = fmt(bc_t)
        out["SF"] = fmt(sf)
        out["ResidualRatio"] = fmt(residual)
        out["SF_Bx"] = fmt(ratio(b0_bx, bc_bx))
        out["SF_By"] = fmt(ratio(b0_by, bc_by))
        out["SF_Bz"] = fmt(ratio(b0_bz, bc_bz))
        out["_volume_value"] = volume
        out["_sf_value"] = sf
        out["_int_h2_value"] = int_h2
        evaluated.append(out)

    for out in evaluated:
        volume = out.pop("_volume_value")
        sf = out.pop("_sf_value")
        int_h2 = out.pop("_int_h2_value")

        volume_saving = math.nan
        if math.isfinite(single_volume) and single_volume > 0 and math.isfinite(volume):
            volume_saving = (single_volume - volume) / single_volume * 100.0

        sf_vs_single = math.nan
        if math.isfinite(single_sf) and single_sf > 0 and math.isfinite(sf):
            sf_vs_single = sf / single_sf

        int_h2_vs_single = math.nan
        if math.isfinite(single_int_h2) and single_int_h2 > 0 and math.isfinite(int_h2):
            int_h2_vs_single = int_h2 / single_int_h2

        out["VolumeSaving_vs_N1_percent"] = fmt(volume_saving)
        out["SF_vs_N1"] = fmt(sf_vs_single)
        out["IntH2_vs_N1"] = fmt(int_h2_vs_single)
        out["passes_same_space_material_efficiency_check"] = (
            "yes"
            if math.isfinite(volume_saving)
            and volume_saving > 0
            and math.isfinite(sf_vs_single)
            and sf_vs_single >= 1.0
            else ""
        )

    fieldnames = list(evaluated[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(evaluated)

    print("Wrote {}".format(OUT_CSV))


if __name__ == "__main__":
    main()
