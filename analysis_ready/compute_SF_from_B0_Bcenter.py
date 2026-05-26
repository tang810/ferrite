"""
compute_SF_from_B0_Bcenter.py
==============================
Standalone Python script (run outside AEDT) to compute shielding factor SF
from B0 and Bcenter CSV files.

Input:
  analysis_ready/SF_4ceng_fixedT10_g02_B0.csv      (no-shield reference)
  analysis_ready/SF_4ceng_fixedT10_g02_Bcenter.csv  (with shield)

Output:
  analysis_ready/SF_4ceng_fixedT10_g02_summary.csv

Also computes:
  SF             = abs(B0_T) / abs(Bcenter_T)
  ResidualRatio  = abs(Bcenter_T) / abs(B0_T)
  SF_Bx          = abs(B0_Bx_T) / abs(Bcenter_Bx_T)   [if Bx available]
  SF_By          = abs(B0_By_T) / abs(Bcenter_By_T)
  SF_Bz          = abs(B0_Bz_T) / abs(Bcenter_Bz_T)
"""

import csv
import os
import sys
from math import fabs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- configuration ----------
CASES = [
    {
        "label"     : "4ceng_fixedT10_g02",
        "b0_csv"    : os.path.join(BASE_DIR, "SF_4ceng_fixedT10_g02_B0.csv"),
        "bcenter_csv": os.path.join(BASE_DIR, "SF_4ceng_fixedT10_g02_Bcenter.csv"),
        "out_csv"   : os.path.join(BASE_DIR, "SF_4ceng_fixedT10_g02_summary.csv"),
    },
]
# ------------------------------------


def read_csv(path):
    """Read a CSV file, return list of dicts."""
    with open(path, "r", newline="") as fh:
        return list(csv.DictReader(fh))


def safe_float(val):
    """Try to convert to float, return None on failure."""
    if val is None or val == "" or val == "FAILED":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def compute_sf(b0_row, bc_row):
    """Compute SF and ResidualRatio from B0 and Bcenter rows."""
    b0_T     = safe_float(b0_row.get("B0_T"))
    bc_T     = safe_float(bc_row.get("Bcenter_T"))
    b0_Bx    = safe_float(b0_row.get("B0_Bx_T"))
    bc_Bx    = safe_float(bc_row.get("Bcenter_Bx_T"))
    b0_By    = safe_float(b0_row.get("B0_By_T"))
    bc_By    = safe_float(bc_row.get("Bcenter_By_T"))
    b0_Bz    = safe_float(b0_row.get("B0_Bz_T"))
    bc_Bz    = safe_float(bc_row.get("Bcenter_Bz_T"))

    result = {}

    if b0_T is not None and bc_T is not None and b0_T != 0 and bc_T != 0:
        result["SF"] = round(fabs(b0_T) / fabs(bc_T), 6)
        result["ResidualRatio"] = round(fabs(bc_T) / fabs(b0_T), 6)
    else:
        result["SF"] = ""
        result["ResidualRatio"] = ""

    for comp, b0_val, bc_val in [("Bx", b0_Bx, bc_Bx),
                                   ("By", b0_By, bc_By),
                                   ("Bz", b0_Bz, bc_Bz)]:
        key_sf = "SF_" + comp
        key_rr = "ResidualRatio_" + comp
        if b0_val is not None and bc_val is not None and b0_val != 0 and bc_val != 0:
            result[key_sf] = round(fabs(b0_val) / fabs(bc_val), 6)
            result[key_rr] = round(fabs(bc_val) / fabs(b0_val), 6)
        else:
            result[key_sf] = ""
            result[key_rr] = ""

    return result


def main():
    for case in CASES:
        label   = case["label"]
        b0_path = case["b0_csv"]
        bc_path = case["bcenter_csv"]
        out_path = case["out_csv"]

        print("=" * 60)
        print("Case: %s" % label)

        if not os.path.exists(b0_path):
            print("  SKIP: B0 file not found: %s" % b0_path)
            continue
        if not os.path.exists(bc_path):
            print("  SKIP: Bcenter file not found: %s" % bc_path)
            continue

        b0_rows = read_csv(b0_path)
        bc_rows = read_csv(bc_path)

        if not b0_rows:
            print("  SKIP: B0 file is empty")
            continue
        if not bc_rows:
            print("  SKIP: Bcenter file is empty")
            continue

        b0_row  = b0_rows[0]
        bc_row  = bc_rows[0]
        sf_data = compute_sf(b0_row, bc_row)

        # Merge all fields
        merged = {}
        # Copy metadata from Bcenter row (has shield design params)
        for k in ["experiment", "layer", "T_mm", "a_mm", "g_mm"]:
            merged[k] = bc_row.get(k, "")

        # B0 fields (prefix B0_)
        for k, v in b0_row.items():
            if k.startswith("B0_"):
                merged[k] = v

        # Bcenter fields (prefix Bcenter_)
        for k, v in bc_row.items():
            if k.startswith("Bcenter_"):
                merged[k] = v

        # SF & ResidualRatio
        merged.update(sf_data)

        # Write output
        fieldnames = list(merged.keys())
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(merged)

        print("  B0_T              = %s" % b0_row.get("B0_T", "N/A"))
        print("  Bcenter_T         = %s" % bc_row.get("Bcenter_T", "N/A"))
        print("  SF                = %s" % merged.get("SF", "N/A"))
        print("  ResidualRatio     = %s" % merged.get("ResidualRatio", "N/A"))
        print("  Wrote: %s" % out_path)


if __name__ == "__main__":
    main()
