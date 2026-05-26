"""
merge_SF_into_all_results.py
=============================
Merges the computed SF summary (from compute_SF_from_B0_Bcenter.py) into the
main all_results_clean.csv, adding B0_T, Bcenter_T, Bcenter component, SF, and
ResidualRatio columns.

This makes the SF data available to the MATLAB analysis pipeline.

Also updates the SF_center_fields_clean.csv registry of center-field exports.
"""

import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inputs
ALL_RESULTS_CSV = os.path.join(BASE_DIR, "all_results_clean.csv")
SF_SUMMARY_CSV  = os.path.join(BASE_DIR, "SF_4ceng_fixedT10_g02_summary.csv")

# Outputs
ALL_RESULTS_UPDATED = os.path.join(BASE_DIR, "all_results_clean.csv")
SF_REGISTRY_CSV     = os.path.join(BASE_DIR, "SF_center_fields_clean.csv")


def read_csv(path):
    with open(path, "r", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def merge_sf_into_all_results():
    """Add SF columns to all_results_clean.csv for the 4ceng external-field case."""
    if not os.path.exists(SF_SUMMARY_CSV):
        print("SF summary not found: %s" % SF_SUMMARY_CSV)
        print("Run compute_SF_from_B0_Bcenter.py first.")
        return

    all_rows = read_csv(ALL_RESULTS_CSV)
    sf_rows  = read_csv(SF_SUMMARY_CSV)

    if not sf_rows:
        print("SF summary is empty.")
        return

    sf_row = sf_rows[0]
    experiment_match = sf_row.get("experiment", "")
    layer_match = sf_row.get("layer", "")

    # New columns to add
    sf_columns = [
        "B0_T", "B0_Bx_T", "B0_By_T", "B0_Bz_T",
        "Bcenter_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
        "SF", "ResidualRatio",
        "SF_Bx", "ResidualRatio_Bx",
        "SF_By", "ResidualRatio_By",
        "SF_Bz", "ResidualRatio_Bz",
    ]

    # Ensure all columns exist in all_rows (add if missing)
    existing_columns = list(all_rows[0].keys()) if all_rows else []
    for col in sf_columns:
        if col not in existing_columns:
            for row in all_rows:
                row[col] = ""

    # Add SF data to the matching row(s)
    updated = 0
    for row in all_rows:
        if str(row.get("experiment", "")).strip() == str(experiment_match).strip() \
           and str(row.get("layer", "")).strip() == str(layer_match).strip() \
           and str(row.get("T_mm", "")).strip() == str(sf_row.get("T_mm", "")).strip():
            for col in sf_columns:
                row[col] = sf_row.get(col, "")
            updated += 1

    # If no exact match, keep the SF data in the center-field registry only.
    # The MATLAB noise pipeline requires IntH2_total, so adding an SF-only row
    # here would break the main analysis.
    if updated == 0:
        print("No matching row found in all_results for experiment=%s layer=%s T_mm=%s" %
              (experiment_match, layer_match, sf_row.get("T_mm", "")))
        print("SF-only row was not appended to all_results_clean.csv.")

    # Write back
    write_csv(ALL_RESULTS_UPDATED, all_rows, list(all_rows[0].keys()))
    print("Updated %d row(s) in %s" % (updated, ALL_RESULTS_UPDATED))


def update_sf_registry():
    """Maintain a registry of all center-field export files."""
    if not os.path.exists(SF_SUMMARY_CSV):
        return

    sf_rows = read_csv(SF_SUMMARY_CSV)
    if not sf_rows:
        return

    sf_row = sf_rows[0]

    registry_fields = [
        "experiment", "layer", "T_mm", "a_mm", "g_mm",
        "B0_T", "Bcenter_T", "SF", "ResidualRatio",
        "B0_source", "Bcenter_source",
    ]

    # Load existing registry or create new
    if os.path.exists(SF_REGISTRY_CSV):
        registry = read_csv(SF_REGISTRY_CSV)
        registry = [
            r for r in registry
            if str(r.get("experiment", "")).strip()
            and str(r.get("SF", "")).strip().lower() not in ["", "nan"]
        ]
    else:
        registry = []

    # Build new entry
    entry = {}
    for fld in registry_fields:
        entry[fld] = sf_row.get(fld, "")
    entry["B0_source"] = "SF_4ceng_fixedT10_g02_B0.csv"
    entry["Bcenter_source"] = "SF_4ceng_fixedT10_g02_Bcenter.csv"

    # Check for duplicate
    exists = any(
        str(r.get("experiment", "")) == str(entry["experiment"]) and
        str(r.get("layer", "")) == str(entry["layer"]) and
        str(r.get("T_mm", "")) == str(entry["T_mm"])
        for r in registry
    )
    if not exists:
        registry.append(entry)

    write_csv(SF_REGISTRY_CSV, registry, registry_fields)
    print("SF registry updated: %s (%d entries)" % (SF_REGISTRY_CSV, len(registry)))


if __name__ == "__main__":
    merge_sf_into_all_results()
    update_sf_registry()
    print("Done.")
