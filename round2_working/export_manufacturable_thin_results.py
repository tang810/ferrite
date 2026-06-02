# -*- coding: utf-8 -*-
"""
export_manufacturable_thin_results.py
=====================================
Export center B fields and IntH2 values from solved manufacturable-thin
continuous-shell AEDT projects.

Run this inside AEDT after `run_manufacturable_thin_continuous.py` has created
and solved the shield/B0 projects.
"""

import csv
import math
import os
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PARAM_CSV = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin_params.csv")
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
OUT_CSV = os.path.join(BASE_DIR, "analysis_ready", "manufacturable_thin_center_fields_exported.csv")
LOG_PATH = os.path.join(PROJECT_DIR, "export_manufacturable_thin_results.log")

MAX_PRIORITY = 1
CASE_ID_FILTER = []
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

INT_EXPR_BY_LAYER = {
    1: {"IntH2_total": "IntH2_total", "IntH2_L1": "IntH2_total"},
    2: {"IntH2_total": "IntH2_total", "IntH2_L1": "IntH2_cyl2", "IntH2_L2": "IntH2_cyl4"},
    3: {"IntH2_total": "IntH2_total", "IntH2_L1": "IntH2_s1", "IntH2_L2": "IntH2_s2", "IntH2_L3": "IntH2_s3"},
    4: {"IntH2_total": "IntH2_total", "IntH2_L1": "IntH2_s1", "IntH2_L2": "IntH2_s2", "IntH2_L3": "IntH2_s3", "IntH2_L4": "InH2_s4"},
}


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def read_cases():
    with open(PARAM_CSV, "r") as f:
        rows = list(csv.DictReader(f))
    cases = []
    for row in rows:
        if row["model_type"] != "continuous_shell":
            continue
        if int(float(row["priority"])) > MAX_PRIORITY:
            continue
        if int(float(row["layer"])) > 4:
            continue
        cases.append(row)
    return cases


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    try:
        return float(raw)
    except Exception:
        return str(raw)


def eval_b_component(fields, key):
    op = {"T": "Mag", "Bx": "ScalarX", "By": "ScalarY", "Bz": "ScalarZ"}[key]
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp(op)
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_named_expr(fields, expr_name):
    fields.CalcStack("clear")
    fields.CopyNamedExprToStack(expr_name)
    fields.ClcEval(SOLN, [])
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def open_project(oDesktop, path, fp):
    try:
        oDesktop.OpenProject(path)
        log(fp, "OpenProject OK: %s" % path)
    except Exception as exc:
        log(fp, "OpenProject warning: %s" % str(exc)[:160])
    return oDesktop.GetActiveProject()


def export_b_fields(oDesktop, project_path, prefix, fp):
    row = {}
    oProject = open_project(oDesktop, project_path, fp)
    oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
    fields = oDesign.GetModule("FieldsReporter")

    for comp in ["T", "Bx", "By", "Bz"]:
        key = "%s_%s_T" % (prefix, comp) if comp != "T" else "%s_T" % prefix
        try:
            row[key] = eval_b_component(fields, comp)
            log(fp, "  %s = %s" % (key, row[key]))
        except Exception:
            row[key] = ""
            log(fp, "  %s FAILED" % key)
            log(fp, traceback.format_exc())
    return row


def export_int_h2(oDesktop, project_path, layer, fp):
    row = {}
    oProject = open_project(oDesktop, project_path, fp)
    oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
    fields = oDesign.GetModule("FieldsReporter")

    for out_key, expr in INT_EXPR_BY_LAYER.get(layer, {}).items():
        try:
            row[out_key] = eval_named_expr(fields, expr)
            log(fp, "  %s/%s = %s" % (out_key, expr, row[out_key]))
        except Exception:
            row[out_key] = ""
            log(fp, "  %s/%s FAILED" % (out_key, expr))
            log(fp, traceback.format_exc())
    return row


def run():
    cases = read_cases()
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))

    fieldnames = [
        "case_id", "experiment", "stage", "model_type", "layer", "T_mm", "a_mm", "g_mm",
        "N_segments", "circumferential_gap_mm", "coverage_phi",
        "B0_T", "B0_Bx_T", "B0_By_T", "B0_Bz_T",
        "Bcenter_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
        "IntH2_total", "IntH2_L1", "IntH2_L2", "IntH2_L3", "IntH2_L4",
    ]

    with open(LOG_PATH, "w") as fp:
        log(fp, "export_manufacturable_thin_results %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        rows = []
        for case in cases:
            case_id = case["case_id"]
            if CASE_ID_FILTER and case_id not in CASE_ID_FILTER:
                continue
            layer = int(float(case["layer"]))
            shield_project = os.path.join(PROJECT_DIR, "%s_shield.aedt" % case_id)
            b0_project = os.path.join(PROJECT_DIR, "%s_B0.aedt" % case_id)

            log(fp, "")
            log(fp, "=" * 70)
            log(fp, "Exporting %s" % case_id)

            out = {
                "case_id": case_id,
                "experiment": "manufacturable_thin",
                "stage": case["stage"],
                "model_type": case["model_type"],
                "layer": case["layer"],
                "T_mm": case["T_mm"],
                "a_mm": case["a_mm"],
                "g_mm": case["g_mm"],
                "N_segments": case["N_segments"],
                "circumferential_gap_mm": case["circumferential_gap_mm"],
                "coverage_phi": case["coverage_phi"],
            }

            if os.path.exists(b0_project):
                out.update(export_b_fields(oDesktop, b0_project, "B0", fp))
            else:
                log(fp, "Missing B0 project: %s" % b0_project)

            if os.path.exists(shield_project):
                out.update(export_b_fields(oDesktop, shield_project, "Bcenter", fp))
                out.update(export_int_h2(oDesktop, shield_project, layer, fp))
            else:
                log(fp, "Missing shield project: %s" % shield_project)

            rows.append(out)

        with open(OUT_CSV, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        log(fp, "Wrote %s" % OUT_CSV)


run()
