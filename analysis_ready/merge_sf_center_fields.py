import csv
import math
from pathlib import Path


BASE_DIR = Path(r"D:\tangyumengnew\aaaaaaaaximukeji")
IN_CSV = BASE_DIR / "analysis_ready" / "SF_required_center_fields_template.csv"
OUT_CSV = BASE_DIR / "analysis_ready" / "SF_center_fields_clean.csv"


REQUIRED = [
    "case",
    "layer",
    "source_model",
    "external_field_direction",
    "B0_T",
    "Bcenter_T",
    "Bcenter_Bx_T",
    "Bcenter_By_T",
    "Bcenter_Bz_T",
]


def parse_float(value):
    value = str(value).strip()
    if value == "":
        return math.nan
    return float(value)


def main():
    with IN_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError(f"No rows found in {IN_CSV}")

    missing = [name for name in REQUIRED if name not in rows[0]]
    if missing:
        raise RuntimeError("Missing required columns: " + ", ".join(missing))

    out_rows = []
    for row in rows:
        B0 = parse_float(row["B0_T"])
        Bc = parse_float(row["Bcenter_T"])
        Bx = parse_float(row["Bcenter_Bx_T"])
        By = parse_float(row["Bcenter_By_T"])
        Bz = parse_float(row["Bcenter_Bz_T"])

        if math.isnan(Bc) and all(math.isfinite(v) for v in [Bx, By, Bz]):
            Bc = math.sqrt(Bx*Bx + By*By + Bz*Bz)

        SF = math.nan
        residual = math.nan
        if math.isfinite(B0) and math.isfinite(Bc) and abs(B0) > 0:
            residual = abs(Bc) / abs(B0)
        if math.isfinite(B0) and math.isfinite(Bc) and abs(Bc) > 0:
            SF = abs(B0) / abs(Bc)

        out = dict(row)
        out["Bcenter_T"] = Bc
        out["SF"] = SF
        out["ResidualRatio"] = residual
        out_rows.append(out)

    fieldnames = list(out_rows[0].keys())
    for extra in ["SF", "ResidualRatio"]:
        if extra not in fieldnames:
            fieldnames.append(extra)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
