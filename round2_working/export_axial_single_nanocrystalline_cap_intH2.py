# -*- coding: utf-8 -*-
"""
Export IntH2 for the solved single-side nanocrystalline cap axial case.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/export_axial_single_nanocrystalline_cap_intH2.py

This script does not solve Setup1. It opens the existing solved project and
integrates H^2 over the four ferrite layers and the nanocrystalline cap.
"""

import csv
import os
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PROJECT_PATH = os.path.join(
    BASE_DIR, "round2_working", "axial_capped_end",
    "ZCAP_C2_N4_single_nanocrystalline_cap_mu50000_shield.aedt")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw",
                       "axial_single_nanocrystalline_cap_intH2.csv")
LOG_PATH = os.path.join(
    BASE_DIR, "round2_working", "axial_capped_end",
    "export_axial_single_nanocrystalline_cap_intH2.log")

DESIGN_NAME = "Maxwell3DDesign1"
SOLN = "Setup1 : LastAdaptive"
CASE_ID = "ZCAP_C2_N4_single_nanocrystalline_cap_mu50000"

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]
CAP_OBJECTS = ["AxialCap_Top"]

FIELDNAMES = [
    "case_id", "source_project", "solution",
    "IntH2_ferrite_only", "IntH2_caps", "IntH2_total_with_caps",
    "status", "notes",
]


def ensure_dirs():
    for path in [os.path.dirname(OUT_CSV), os.path.dirname(LOG_PATH)]:
        if not os.path.isdir(path):
            os.makedirs(path)


def log(fp, msg):
    try:
        text = unicode(msg)
    except Exception:
        try:
            text = str(msg)
        except Exception:
            text = "<unprintable>"
    try:
        fp.write(text.encode("utf-8", "replace") + "\n")
    except Exception:
        fp.write(str(text).replace("\x00", "?") + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        value = fn()
        s = str(value) if value is not None else ""
        log(fp, label + ": OK" + (" -> " + s if s else ""))
        return True if value is None else value
    except Exception:
        log(fp, label + ": FAILED")
        log(fp, traceback.format_exc())
        return None


def append_csv_row(path, fieldnames, row):
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    fp = open(path, "ab" if exists else "wb")
    try:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        out = {}
        for name in fieldnames:
            out[name] = row.get(name, "")
        writer.writerow(out)
    finally:
        fp.close()


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        if not raw:
            return ""
        raw = raw[0]
    try:
        return float(raw)
    except Exception:
        return str(raw)


def eval_h2_integral_over_objects(fields, objects):
    if not objects:
        return 0.0

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
            total += float(object_comp_integral(obj, comp))
    return total


def run():
    ensure_dirs()
    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "export_axial_single_nanocrystalline_cap_intH2 " +
            time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "PROJECT_PATH=" + PROJECT_PATH)
        log(fp, "FERRITE_OBJECTS=" + str(FERRITE_OBJECTS))
        log(fp, "CAP_OBJECTS=" + str(CAP_OBJECTS))

        if not os.path.exists(PROJECT_PATH):
            log(fp, "PROJECT MISSING")
            append_csv_row(OUT_CSV, FIELDNAMES, {
                "case_id": CASE_ID,
                "source_project": PROJECT_PATH,
                "solution": SOLN,
                "status": "project_missing",
                "notes": "Run axial single nanocrystalline cap solve first",
            })
            return

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        safe(fp, "OpenProject", lambda: oDesktop.OpenProject(PROJECT_PATH))
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign(DESIGN_NAME)
        fields = oDesign.GetModule("FieldsReporter")

        int_ferrite = safe(fp, "IntH2 ferrite only",
                           lambda: eval_h2_integral_over_objects(fields, FERRITE_OBJECTS))
        int_caps = safe(fp, "IntH2 caps",
                        lambda: eval_h2_integral_over_objects(fields, CAP_OBJECTS))

        int_total = ""
        try:
            int_total = float(int_ferrite) + float(int_caps)
        except Exception:
            pass

        status = "exported" if int_ferrite not in ["", None] and int_caps not in ["", None] else "failed"
        append_csv_row(OUT_CSV, FIELDNAMES, {
            "case_id": CASE_ID,
            "source_project": PROJECT_PATH,
            "solution": SOLN,
            "IntH2_ferrite_only": int_ferrite,
            "IntH2_caps": int_caps,
            "IntH2_total_with_caps": int_total,
            "status": status,
            "notes": "H^2 integral over ferrite layers plus single nanocrystalline cap",
        })

        try:
            oDesktop.CloseProject(oProject.GetName())
        except Exception:
            pass
        log(fp, "RESULT IntH2_ferrite_only=" + str(int_ferrite) +
            " IntH2_caps=" + str(int_caps) +
            " IntH2_total_with_caps=" + str(int_total) +
            " status=" + status)
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
