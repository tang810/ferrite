# -*- coding: utf-8 -*-
import csv
import os
import time

import ScriptEnv

BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
OUT_DIR = os.path.join(BASE_DIR, "round2_working")
OUT_CSV = os.path.join(OUT_DIR, "verify_sf_center_fields_report.csv")
LOG_PATH = os.path.join(OUT_DIR, "verify_sf_center_fields_report_out.log")
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

CASES = [
    ("shield", os.path.join(OUT_DIR, "Project100_4ceng_fixedT10_g02_ext.aedt")),
    ("B0", os.path.join(OUT_DIR, "Project100_4ceng_fixedT10_g02_B0.aedt")),
]


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def read_report_csv(path):
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        rows = list(csv.reader(f))

    numeric = []
    for row in rows:
        vals = []
        for item in row:
            try:
                vals.append(float(str(item).strip()))
            except Exception:
                pass
        if len(vals) >= 2:
            numeric = vals

    return {
        "raw_numeric": numeric,
        "raw_preview": rows[:8],
    }


def export_case(f, label, project_path):
    log(f, "")
    log(f, "=== %s ===" % label)
    log(f, "Project: %s" % project_path)

    try:
        oDesktop.OpenProject(project_path)
        log(f, "OpenProject: OK")
    except Exception as exc:
        log(f, "OpenProject: %s" % str(exc)[:200])

    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
    oModule = oDesign.GetModule("ReportSetup")

    try:
        log(f, "NominalVariation: %s" % oDesign.GetNominalVariation())
    except Exception as exc:
        log(f, "NominalVariation: %s" % str(exc)[:200])

    report_name = "Verify_Center_B_%s" % label
    try:
        oModule.DeleteReport(report_name)
    except Exception:
        pass

    expressions = [
        "X Component:=", "Mag_B",
        "Y Component:=", ["Mag_B", "ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"],
    ]

    try:
        oModule.CreateReport(
            report_name,
            "Fields",
            "Data Table",
            SOLN,
            ["Context:=", POINT_NAME],
            [],
            expressions,
        )
        log(f, "CreateReport: OK")
    except Exception as exc:
        log(f, "CreateReport: FAILED: %s" % str(exc)[:500])
        return {"case": label, "status": "CreateReport failed"}

    raw_csv = os.path.join(OUT_DIR, "verify_%s_raw.csv" % label)
    try:
        oModule.ExportToFile(report_name, raw_csv)
        log(f, "ExportToFile: OK -> %s" % raw_csv)
    except Exception as exc:
        log(f, "ExportToFile: FAILED: %s" % str(exc)[:500])
        return {"case": label, "status": "ExportToFile failed"}

    parsed = read_report_csv(raw_csv)
    log(f, "Raw preview:")
    for row in parsed.get("raw_preview", []):
        log(f, "  %s" % row)
    log(f, "Numeric: %s" % parsed.get("raw_numeric", []))

    nums = parsed.get("raw_numeric", [])
    row = {"case": label, "status": "OK"}
    for idx, name in enumerate(["Mag_B", "Mag_B_dup", "ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"]):
        row[name] = nums[idx] if idx < len(nums) else ""
    return row


with open(LOG_PATH, "w") as f:
    log(f, "verify_sf_center_fields_report %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    oDesktop.RestoreWindow()

    rows = []
    for label, path in CASES:
        rows.append(export_case(f, label, path))

    with open(OUT_CSV, "w") as out:
        fieldnames = ["case", "status", "Mag_B", "Mag_B_dup", "ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"]
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log(f, "")
    log(f, "Wrote: %s" % OUT_CSV)
