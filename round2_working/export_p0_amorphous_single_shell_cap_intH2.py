# -*- coding: utf-8 -*-
"""
Export IntH2 for the solved P0 amorphous single-shell + single-cap case.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/export_p0_amorphous_single_shell_cap_intH2.py

This script does not solve Setup1. It opens the solved P0 project and
integrates H^2 over the amorphous cylindrical shell and the +Z cap.
"""

import csv
import os
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PROJECT_PATH = os.path.join(
    BASE_DIR, "round2_working", "p0_amorphous_single_shell_cap",
    "P0_amorphous_single_shell_plusZ_cap_mu10000.aedt")
OUT_CSV = os.path.join(
    BASE_DIR, "data", "raw", "p0_amorphous_single_shell_cap_intH2.csv")
LOG_PATH = os.path.join(
    BASE_DIR, "round2_working", "p0_amorphous_single_shell_cap",
    "export_p0_amorphous_single_shell_cap_intH2.log")

DESIGN_NAME = "Maxwell3DDesign1"
SOLN = "Setup1 : LastAdaptive"
CASE_ID = "P0_amorphous_single_shell_plusZ_cap_mu10000"

SHELL_OBJECTS = ["P0_Amorphous_Shell"]
CAP_OBJECTS = ["P0_Amorphous_Cap_PlusZ"]

FIELDNAMES = [
    "case_id", "source_project", "solution",
    "IntH2_shell", "IntH2_cap", "IntH2_total",
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


def write_csv_row(path, fieldnames, row):
    fp = open(path, "wb")
    try:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
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
        log(fp, "export_p0_amorphous_single_shell_cap_intH2 " +
            time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "PROJECT_PATH=" + PROJECT_PATH)
        log(fp, "SHELL_OBJECTS=" + str(SHELL_OBJECTS))
        log(fp, "CAP_OBJECTS=" + str(CAP_OBJECTS))

        if not os.path.exists(PROJECT_PATH):
            log(fp, "PROJECT MISSING")
            write_csv_row(OUT_CSV, FIELDNAMES, {
                "case_id": CASE_ID,
                "source_project": PROJECT_PATH,
                "solution": SOLN,
                "status": "project_missing",
                "notes": "Run P0 amorphous shell + cap solve first",
            })
            return

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        safe(fp, "OpenProject", lambda: oDesktop.OpenProject(PROJECT_PATH))
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign(DESIGN_NAME)
        fields = oDesign.GetModule("FieldsReporter")

        int_shell = safe(fp, "IntH2 amorphous shell",
                         lambda: eval_h2_integral_over_objects(fields, SHELL_OBJECTS))
        int_cap = safe(fp, "IntH2 amorphous cap",
                       lambda: eval_h2_integral_over_objects(fields, CAP_OBJECTS))

        int_total = ""
        try:
            int_total = float(int_shell) + float(int_cap)
        except Exception:
            pass

        status = "exported" if int_shell not in ["", None] and int_cap not in ["", None] else "failed"
        write_csv_row(OUT_CSV, FIELDNAMES, {
            "case_id": CASE_ID,
            "source_project": PROJECT_PATH,
            "solution": SOLN,
            "IntH2_shell": int_shell,
            "IntH2_cap": int_cap,
            "IntH2_total": int_total,
            "status": status,
            "notes": "H^2 integral over P0 amorphous shell plus single +Z amorphous cap",
        })

        try:
            oDesktop.CloseProject(oProject.GetName())
        except Exception:
            pass
        log(fp, "RESULT IntH2_shell=" + str(int_shell) +
            " IntH2_cap=" + str(int_cap) +
            " IntH2_total=" + str(int_total) +
            " status=" + status)
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
