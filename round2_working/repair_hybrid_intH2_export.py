# -*- coding: utf-8 -*-
"""
Repair IntH2 exports for an already solved hybrid outer-layer project.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/repair_hybrid_intH2_export.py

This script does not call Analyze. It updates the existing CSV row in place.
"""

import csv
import math
import os
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
CASE_ID = "H_C2_N4_t015_g008_x_outer_nanocrystalline_t0200_g0400_mu50000"
PROJECT_PATH = os.path.join(
    BASE_DIR, "round2_working", "hybrid_outer_layer", CASE_ID + "_shield.aedt")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw", "hybrid_outer_layer_exports.csv")
LOG_PATH = os.path.join(
    BASE_DIR, "round2_working", "hybrid_outer_layer", "repair_hybrid_intH2_export.log")

DESIGN_NAME = "Maxwell3DDesign1"
SOLN = "Setup1 : LastAdaptive"
BASE_INTH2 = 4.16011287324e-06
FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]
OUTER_OBJECT = "HybridOuterLayer"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def extract_value(raw):
    if isinstance(raw, list):
        if not raw:
            return ""
        raw = raw[0]
    return float(raw)


def eval_h2_integral_over_objects(fields, objects):
    def object_comp_integral(obj, comp):
        op = {"x": "ScalarX", "y": "ScalarY", "z": "ScalarZ"}[comp]
        fields.CalcStack("clear")
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.CalcOp("*")
        fields.EnterVol(obj)
        fields.CalcOp("Integrate")
        fields.ClcEval(SOLN, [])
        return extract_value(fields.GetTopEntryValue(SOLN, []))

    total = 0.0
    for obj in objects:
        for comp in ["x", "y", "z"]:
            total += object_comp_integral(obj, comp)
    return total


def update_csv(int_total, int_outer):
    with open(OUT_CSV, "rb") as fp:
        reader = csv.DictReader(fp)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = False
    for row in rows:
        if row.get("case_id") != CASE_ID:
            continue
        row["IntH2_total"] = str(int_total)
        row["IntH2_outer"] = str(int_outer)
        row["IntH2_ratio"] = str(int_total / BASE_INTH2)
        try:
            sfx = float(row.get("SFx", ""))
            row["chiH"] = str(int_total / math.log(sfx)) if sfx > 1 else ""
        except Exception:
            row["chiH"] = ""
        row["status"] = "exported"
        row["notes"] = row.get("notes", "") + "; repaired IntH2 export"
        updated = True

    if not updated:
        raise RuntimeError("CSV row not found for " + CASE_ID)

    with open(OUT_CSV, "wb") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    with open(LOG_PATH, "wb") as fp:
        try:
            log(fp, "repair_hybrid_intH2_export")
            log(fp, "CASE " + CASE_ID)
            if not os.path.exists(PROJECT_PATH):
                raise RuntimeError("project missing: " + PROJECT_PATH)

            oDesktop.OpenProject(PROJECT_PATH)
            project = oDesktop.GetActiveProject()
            design = project.SetActiveDesign(DESIGN_NAME)
            fields = design.GetModule("FieldsReporter")

            int_outer = eval_h2_integral_over_objects(fields, [OUTER_OBJECT])
            log(fp, "IntH2_outer=" + str(int_outer))
            int_total = eval_h2_integral_over_objects(
                fields, FERRITE_OBJECTS + [OUTER_OBJECT])
            log(fp, "IntH2_total=" + str(int_total))

            update_csv(int_total, int_outer)
            project.Save()
            log(fp, "status=exported")
        except Exception:
            log(fp, "FAILED")
            log(fp, traceback.format_exc())
            raise


main()
