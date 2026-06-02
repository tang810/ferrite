import csv
import os
import re
import shutil
import sys


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis_ready")

OUT_MAIN = os.path.join(ANALYSIS_DIR, "all_results_clean.csv")
OUT_LAYERWISE = os.path.join(ANALYSIS_DIR, "all_results_clean_layerwise.csv")
BACKUP = os.path.join(ANALYSIS_DIR, "all_results_clean_before_layerwise.csv")


EXPORTS = [
    ("export_1ceng_asweep.csv", "asweep", 1),
    ("export_1ceng_Tcompare.csv", "Tcompare", 1),
    ("export_2ceng_asweep.csv", "asweep", 2),
    ("export_2ceng_Tcompare.csv", "Tcompare", 2),
    ("export_2ceng_agmatrix.csv", "agmatrix", 2),
    ("export_3ceng_asweep.csv", "asweep", 3),
    ("export_3ceng_Tcompare.csv", "Tcompare", 3),
    ("export_3ceng_agmatrix.csv", "agmatrix", 3),
    ("export_4ceng_asweep.csv", "asweep", 4),
    ("export_4ceng_Tcompare.csv", "Tcompare", 4),
    ("export_4ceng_agmatrix.csv", "agmatrix", 4),
]


OUT_FIELDS = [
    "experiment",
    "layer",
    "T_mm",
    "a_mm",
    "g_mm",
    "IntH2_total",
    "IntH2_L1",
    "IntH2_L2",
    "IntH2_L3",
    "IntH2_L4",
]

LEGACY_ALIASES = {
    "IntH2_L1": ["IntH2_cyl2", "IntH2_s1"],
    "IntH2_L2": ["IntH2_cyl4", "IntH2_s2"],
    "IntH2_L3": ["IntH2_s3"],
    "IntH2_L4": ["InH2_s4", "IntH2_s4"],
}


def clean_header(name):
    return name.split(":")[0].strip()


def parse_mm(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    match = re.match(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text)
    if not match:
        return ""
    return float(match.group(1))


def get_value(row, clean_to_raw, clean_name):
    raw = clean_to_raw.get(clean_name)
    if raw is None:
        return ""
    value = row.get(raw, "")
    if value is None:
        return ""
    return str(value).strip()


def normalize_row(row, experiment, layer, clean_to_raw):
    total = get_value(row, clean_to_raw, "IntH2_total")
    out = {
        "experiment": experiment,
        "layer": layer,
        "T_mm": parse_mm(get_value(row, clean_to_raw, "T")),
        "a_mm": parse_mm(get_value(row, clean_to_raw, "a")),
        "g_mm": parse_mm(get_value(row, clean_to_raw, "g")),
        "IntH2_total": total,
        "IntH2_L1": "",
        "IntH2_L2": "",
        "IntH2_L3": "",
        "IntH2_L4": "",
    }

    if layer == 1:
        if out["T_mm"] == "":
            out["T_mm"] = out["a_mm"]
        out["g_mm"] = 0.0 if out["g_mm"] == "" else out["g_mm"]
        out["IntH2_L1"] = total
    elif layer == 2:
        out["IntH2_L1"] = get_value(row, clean_to_raw, "IntH2_cyl2")
        out["IntH2_L2"] = get_value(row, clean_to_raw, "IntH2_cyl4")
    elif layer == 3:
        out["IntH2_L1"] = get_value(row, clean_to_raw, "IntH2_s1")
        out["IntH2_L2"] = get_value(row, clean_to_raw, "IntH2_s2")
        out["IntH2_L3"] = get_value(row, clean_to_raw, "IntH2_s3")
    elif layer == 4:
        out["IntH2_L1"] = get_value(row, clean_to_raw, "IntH2_s1")
        out["IntH2_L2"] = get_value(row, clean_to_raw, "IntH2_s2")
        out["IntH2_L3"] = get_value(row, clean_to_raw, "IntH2_s3")
        out["IntH2_L4"] = get_value(row, clean_to_raw, "InH2_s4")

    # Some AEDT Result exports only include the swept independent variable.
    # Reconstruct the dependent geometry columns from the experiment design.
    if experiment == "asweep":
        if out["g_mm"] == "":
            out["g_mm"] = 0.0 if layer == 1 else 0.5
        if out["T_mm"] == "" and out["a_mm"] != "":
            out["T_mm"] = layer * out["a_mm"] + (layer - 1) * out["g_mm"]

    if experiment == "Tcompare":
        if out["g_mm"] == "":
            out["g_mm"] = 0.0 if layer == 1 else 0.5
        if out["a_mm"] == "" and out["T_mm"] != "":
            out["a_mm"] = (out["T_mm"] - (layer - 1) * out["g_mm"]) / layer

    return out


def warn_legacy_aliases(clean_to_raw, filename):
    seen = []
    for canonical, aliases in LEGACY_ALIASES.items():
        for alias in aliases:
            if alias in clean_to_raw:
                seen.append("{}->{}".format(alias, canonical))
    if seen:
        print(
            "WARNING legacy-compatible IntH2 names in {}: {}. "
            "Rename AEDT expressions to IntH2_Li/IntH2_total for new exports.".format(
                filename, ", ".join(seen)
            ),
            file=sys.stderr,
        )


def validate_rows(rows):
    problems = []
    for i, row in enumerate(rows, start=2):
        total = float(row["IntH2_total"])
        layer_sum = 0.0
        has_layers = False
        for col in ["IntH2_L1", "IntH2_L2", "IntH2_L3", "IntH2_L4"]:
            if row[col] != "":
                has_layers = True
                layer_sum += float(row[col])
        if has_layers:
            rel = abs(layer_sum - total) / max(abs(total), 1e-300)
            if rel > 1e-5:
                problems.append((i, row["experiment"], row["layer"], rel))
    return problems


def main():
    rows_out = []
    missing = []

    for filename, experiment, layer in EXPORTS:
        path = os.path.join(ANALYSIS_DIR, filename)
        if not os.path.exists(path):
            missing.append(filename)
            continue

        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            clean_to_raw = {clean_header(name): name for name in reader.fieldnames}
            warn_legacy_aliases(clean_to_raw, filename)
            for row in reader:
                rows_out.append(normalize_row(row, experiment, layer, clean_to_raw))

    if missing:
        raise RuntimeError("Missing export files: {}".format(", ".join(missing)))

    problems = validate_rows(rows_out)
    if problems:
        msg = "; ".join(
            "line {} {} layer {} relerr {:.3e}".format(*p) for p in problems
        )
        raise RuntimeError("Layer sums do not match IntH2_total: " + msg)

    if os.path.exists(OUT_MAIN) and not os.path.exists(BACKUP):
        shutil.copy2(OUT_MAIN, BACKUP)

    for out_path in [OUT_LAYERWISE, OUT_MAIN]:
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows_out)

    print("Wrote {}".format(OUT_MAIN))
    print("Wrote {}".format(OUT_LAYERWISE))
    print("Rows: {}".format(len(rows_out)))
    print("Backup: {}".format(BACKUP))


if __name__ == "__main__":
    main()
