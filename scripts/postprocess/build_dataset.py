"""中文说明：
本脚本合并实验矩阵、B0 reference、中心场导出和 IntH2 分层导出，
生成 data/processed/main_dataset.csv。它只做数据合并和缺失字段标记，
不会计算论文结论，也不会把缺失数据填成 0。
"""

import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "data" / "experiment_matrix_main.csv"
RAW_DIR = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "main_dataset.csv"


FIELDNAMES_EXTRA = [
    "B0_Bx_T",
    "B0_By_T",
    "B0_Bz_T",
    "B0_Mag_T",
    "Bcenter_Bx_T",
    "Bcenter_By_T",
    "Bcenter_Bz_T",
    "Bcenter_Mag_T",
    "IntH2_total",
    "IntH2_L1",
    "IntH2_L2",
    "IntH2_L3",
    "IntH2_L4",
    "IntH2_L5",
    "IntH2_L6",
    "data_status",
    "missing_fields",
]


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def index_by_case(rows):
    return {(row.get("case_id") or "").strip(): row for row in rows if (row.get("case_id") or "").strip()}


def first_nonempty(*values):
    for value in values:
        if str(value).strip() != "":
            return value
    return ""


def load_reference(raw_dir):
    refs = {}
    for field_dir in ("x", "z"):
        rows = read_csv(raw_dir / f"B0_reference_{field_dir}.csv")
        if rows:
            refs[field_dir] = rows[0]
    for row in read_csv(raw_dir / "center_field_raw.csv"):
        model_type = row.get("model_type", "")
        field_dir = row.get("field_dir", row.get("external_field_direction", ""))
        if model_type == "no_shield" and field_dir:
            refs[field_dir] = row
    return refs


def required_for_row(row):
    if row["model_type"] == "no_shield":
        return ["B0_Bx_T", "B0_By_T", "B0_Bz_T", "B0_Mag_T"]
    required = ["Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T", "Bcenter_Mag_T"]
    if row["model_type"] == "continuous_shell":
        n = int(float(row["N_layers"]))
        required.append("IntH2_total")
        required.extend([f"IntH2_L{i}" for i in range(1, n + 1)])
    elif row["model_type"] == "segmented_shell_3d":
        required.append("IntH2_total")
    return required


def main():
    parser = argparse.ArgumentParser(description="Build merged dataset from raw AEDT exports.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    matrix = read_csv(args.matrix)
    center = index_by_case(read_csv(args.raw_dir / "center_field_raw.csv"))
    int_h2 = index_by_case(read_csv(args.raw_dir / "intH2_layerwise_raw.csv"))
    refs = load_reference(args.raw_dir)

    out_rows = []
    for row in matrix:
        out = dict(row)
        case_id = row["case_id"]
        field_dir = row["external_field_direction"]
        center_row = center.get(case_id, {})
        h2_row = int_h2.get(case_id, {})
        ref = refs.get(field_dir, {})

        for key in ("B0_Bx_T", "B0_By_T", "B0_Bz_T", "B0_Mag_T"):
            out[key] = first_nonempty(row.get(key, ""), center_row.get(key, ""), ref.get(key, ""))
        for key in ("Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T", "Bcenter_Mag_T"):
            out[key] = first_nonempty(row.get(key, ""), center_row.get(key, ""))
        for key in ("IntH2_total", "IntH2_L1", "IntH2_L2", "IntH2_L3", "IntH2_L4", "IntH2_L5", "IntH2_L6"):
            out[key] = first_nonempty(row.get(key, ""), h2_row.get(key, ""))

        # ---- Auto-compute Bcenter_Mag_T from vector components when missing ----
        mag_computed = False
        if str(out.get("Bcenter_Mag_T", "")).strip() == "":
            bx = out.get("Bcenter_Bx_T", "")
            by = out.get("Bcenter_By_T", "")
            bz = out.get("Bcenter_Bz_T", "")
            try:
                bx_v = float(bx)
                by_v = float(by)
                bz_v = float(bz)
                mag = math.sqrt(bx_v * bx_v + by_v * by_v + bz_v * bz_v)
                out["Bcenter_Mag_T"] = mag
                mag_computed = True
            except (ValueError, TypeError):
                pass

        missing = [key for key in required_for_row(row) if str(out.get(key, "")).strip() == ""]
        out["missing_fields"] = ";".join(missing)
        if row["status"] == "failed":
            out["data_status"] = "failed"
        elif row["status"] in ("planned", "missing") and missing:
            out["data_status"] = row["status"]
        elif missing:
            out["data_status"] = "missing"
        else:
            out["data_status"] = "exported"

        if mag_computed:
            existing_note = str(out.get("notes", "")).strip()
            tag = "Bcenter_Mag_T computed_from_components"
            if existing_note:
                out["notes"] = existing_note + "; " + tag
            else:
                out["notes"] = tag
        out_rows.append(out)

    fieldnames = list(matrix[0].keys()) + [name for name in FIELDNAMES_EXTRA if name not in matrix[0]]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{k: r.get(k, "") for k in fieldnames} for r in out_rows])
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
