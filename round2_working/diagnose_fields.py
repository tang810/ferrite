# -*- coding: utf-8 -*-
"""
Diagnose field calculator API for the external field model.
Checks available solutions, tries different APIs, reports everything.
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
LOG_PATH    = r"D:\ferrite\aaaaaaaaximukeji\round2_working\diagnose_fields.log"
POINT_NAME  = "BcenterPoint_0_0_0"
POINT_FILE  = r"D:\ferrite\aaaaaaaaximukeji\round2_working\_center_point.pts"


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        result = fn()
        log(fp, "  %s: OK -> %s" % (label, result))
        return result
    except Exception as exc:
        log(fp, "  %s: %s" % (label, str(exc)[:200]))
        return None


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "diagnose_fields  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        # Write point file for ExportToFile
        with open(POINT_FILE, "w") as pf:
            pf.write("0 0 0\n")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception as exc:
            log(f, "OpenProject (may already be open): %s" % str(exc)[:100])

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields   = oDesign.GetModule("FieldsReporter")
        oModule  = oDesign.GetModule("ReportSetup")

        # ---- Check solution status ----
        log(f, "")
        log(f, "=== Solution info ===")
        solns = ["Setup1 : LastAdaptive", "Setup1 : Adaptive_1", "Setup1"]
        for s in solns:
            safe(f, "solution='%s'" % s, lambda s=s: str(s))

        # ---- Check what field quantities are available ----
        log(f, "")
        log(f, "=== FieldsReporter methods (dir) ===")
        safe(f, "dir(fields)", lambda: [x for x in dir(fields) if not x.startswith("_")])

        # ---- Try GetFieldValue if available ----
        log(f, "")
        log(f, "=== GetFieldValue attempts ===")
        for s in solns:
            for expr in ["Mag_B", "B", "ComplexMag_B"]:
                safe(f, "GetFieldValue(point,%s,%s)" % (expr, s),
                     lambda e=expr, s=s: fields.GetFieldValue(POINT_NAME, e, s))

        # ---- Try ExportToFile with different expressions ----
        log(f, "")
        log(f, "=== ExportToFile attempts ===")
        for idx, expr_list in enumerate([
            ["Mag_B"],
            ["B"],
            ["B_Mag"],
            ["ComplexMag_B"],
            ["Bx", "By", "Bz"],
        ]):
            out_file = r"D:\ferrite\aaaaaaaaximukeji\round2_working\_test_%d.fld" % idx
            safe(f, "ExportToFile(%s)" % expr_list,
                 lambda el=expr_list, of=out_file: fields.ExportToFile(of, POINT_FILE, "Setup1 : LastAdaptive", el))

        # ---- Try field calc with different solution formats ----
        log(f, "")
        log(f, "=== Field calc attempts with different soln formats ===")

        for s in solns:
            log(f, "--- soln='%s' ---" % s)
            # Try simple stack: EnterPoint + CopyNamedExprToStack("Mag_B")
            safe(f, "  point+Mag_B", lambda s=s: (
                fields.CalcStack("clear"),
                fields.EnterPoint(POINT_NAME),
                fields.CopyNamedExprToStack("Mag_B"),
                fields.ClcEval(s, []),
                fields.GetTopEntryValue(s, []),
            )[-1])

            # Try EnterQty("B") + CalcOp("Mag") + EnterPoint
            safe(f, "  point+B+Mag", lambda s=s: (
                fields.CalcStack("clear"),
                fields.EnterPoint(POINT_NAME),
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.ClcEval(s, []),
                fields.GetTopEntryValue(s, []),
            )[-1])

            # Reverse order
            safe(f, "  B+Mag+point", lambda s=s: (
                fields.CalcStack("clear"),
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
                fields.ClcEval(s, []),
                fields.GetTopEntryValue(s, []),
            )[-1])

        # ---- Try creating a field report ----
        log(f, "")
        log(f, "=== Field report attempts ===")
        for s in solns:
            report_name = "DiagReport_%s" % s.replace(" ", "_").replace(":", "")
            try:
                oModule.DeleteReport(report_name)
            except Exception:
                pass
            safe(f, "CreateReport(%s)" % s, lambda s=s, rn=report_name: oModule.CreateReport(
                rn, "Fields", "Data Table", s,
                ["Context:=", POINT_NAME],
                ["X Component:=", "Mag_B", "Y Component:=", ["Bx", "By", "Bz"]],
                [],
            ))

        # ---- Try GetTopEntryValue after ClcEval without building stack ----
        # Maybe data already exists from a previous computation
        log(f, "")
        log(f, "=== Direct GetTopEntryValue (no stack build) ===")
        for s in solns:
            safe(f, "direct GetTopEntryValue(%s)" % s,
                 lambda s=s: fields.GetTopEntryValue(s, []))

        log(f, "")
        log(f, "Done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
