# -*- coding: utf-8 -*-
"""
diagnose_fields2.py
==================
More targeted diagnostic. Lists ALL FieldsReporter methods cleanly,
and tries alternative approaches to get field data.
"""

import os
import time

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
LOG_PATH    = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\diagnose_fields2.log"
POINT_NAME  = "BcenterPoint_0_0_0"
POINT_FILE  = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_point.pts"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def try_call(fp, label, fn):
    try:
        result = fn()
        log(fp, "OK %s: %s" % (label, str(result)[:500]))
        return result
    except Exception as exc:
        log(fp, "FAIL %s: %s" % (label, str(exc)[:300]))
        return None


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "diagnose_fields2  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        with open(POINT_FILE, "w") as pf:
            pf.write("0 0 0\n")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
        except Exception:
            pass

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields   = oDesign.GetModule("FieldsReporter")
        oModule  = oDesign.GetModule("ReportSetup")
        soln     = "Setup1 : LastAdaptive"

        # ---- List all methods on FieldsReporter (write each separately) ----
        log(f, "")
        log(f, "=== FieldsReporter methods ===")
        for m in dir(fields):
            if not m.startswith("_"):
                log(f, "  %s" % m)

        # ---- List oDesign methods that might relate to fields ----
        log(f, "")
        log(f, "=== oDesign field-related methods ===")
        for m in dir(oDesign):
            m_lower = m.lower()
            if any(kw in m_lower for kw in ["field", "solution", "export", "soln", "calc"]):
                log(f, "  %s" % m)

        # ---- Try ExportToFile correctly ----
        log(f, "")
        log(f, "=== ExportToFile with correct args ===")

        # Try with empty varVals and different export options
        out_fld = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_test.fld"
        for opt in [
            [],
            ["ExportFieldType:=", "Mag_B"],
            ["Expression:=", "Mag_B"],
            ["Quantity:=", "B"],
            ["Field:=", "B"],
        ]:
            label = "ExportToFile(opt=%s)" % str(opt)
            try_call(f, label, lambda opt=opt: fields.ExportToFile(out_fld, POINT_FILE, soln, [], opt))

        # ---- Try oDesign methods ----
        log(f, "")
        log(f, "=== oDesign solution/field methods ===")

        try_call(f, "oDesign.GetNominalVariation",
                 lambda: oDesign.GetNominalVariation())
        try_call(f, "oDesign.GetSolutionData(%s)" % soln,
                 lambda: oDesign.GetSolutionData(soln))
        try_call(f, "oDesign.GetSolutionContext",
                 lambda: oDesign.GetSolutionContext())

        # ---- Try setting field context before calc ----
        log(f, "")
        log(f, "=== Try setting field context ===")
        try_call(f, "fields.SetSolutionContext",
                 lambda: fields.SetSolutionContext(soln, []))
        try_call(f, "fields.LoadSolution",
                 lambda: fields.LoadSolution(soln))
        try_call(f, "fields.SetFieldSolution",
                 lambda: fields.SetFieldSolution(soln))

        # After attempting to set context, try calc again
        log(f, "")
        log(f, "=== Calc after context setup ===")
        for label, build_fn in [
            ("Mag_B+point", lambda: (
                fields.CopyNamedExprToStack("Mag_B"),
                fields.EnterPoint(POINT_NAME),
            )),
            ("point+Mag_B", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.CopyNamedExprToStack("Mag_B"),
            )),
            ("point+B+Mag", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
            )),
            ("B+Mag+point", lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
            )),
        ]:
            try_call(f, label, lambda b=build_fn: (
                fields.CalcStack("clear"),
                b(),
                fields.ClcEval(soln, []),
                fields.GetTopEntryValue(soln, []),
            )[-1])

        # ---- Try CalcOp("Eval") instead of ClcEval ----
        log(f, "")
        log(f, "=== CalcOp('Eval') instead of ClcEval ===")
        try_call(f, "point+Mag_B+Eval", lambda: (
            fields.CalcStack("clear"),
            fields.EnterPoint(POINT_NAME),
            fields.CopyNamedExprToStack("Mag_B"),
            fields.CalcOp("Eval"),
        )[-1] if False else "see_error")

        # ---- Try GetFieldValue ----
        log(f, "")
        log(f, "=== GetFieldValue ===")
        for expr in ["Mag_B", "B"]:
            try_call(f, "GetFieldValue(%s)" % expr,
                     lambda e=expr: fields.GetFieldValue(POINT_NAME, e, soln))

        # ---- Try CreateReport with 7 args ----
        log(f, "")
        log(f, "=== CreateReport with 7+ args ===")
        report_name = "DiagReport2"
        try:
            oModule.DeleteReport(report_name)
        except Exception:
            pass

        # Try different CreateReport formats
        for label, args in [
            ("7args_basic", [
                report_name, "Fields", "Data Table", soln,
                ["Context:=", POINT_NAME],
                [],
                ["X Component:=", "Mag_B", "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"]],
            ]),
            ("8args", [
                report_name, "Fields", "Data Table", soln,
                ["Context:=", POINT_NAME],
                [],
                ["X Component:=", "Mag_B", "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"]],
                [],
            ]),
        ]:
            try_call(f, label, lambda a=args: oModule.CreateReport(*a))

        log(f, "")
        log(f, "Done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
