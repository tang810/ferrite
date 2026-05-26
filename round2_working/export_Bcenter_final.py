# -*- coding: utf-8 -*-
"""
export_Bcenter_final.py
=======================
Export B field at center point using the working API pattern from
export_Bcenter_1ceng_nominal.py (the only script that succeeded).

Key rules for AEDT 2025 R1:
  - Use EnterPoint(), NOT EnterGrid()
  - Do NOT use CalcOp("Value") -- not available
  - Do NOT use CalcOp("Complex")/CalcOp("CmplxMag") -- use CalcOp("Mag")
  - Use ClcEval() + GetTopEntryValue() directly after building stack

Target: Project100_4ceng_fixedT10_g02_ext.aedt (external field model)
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_final.log"
POINT_NAME = "BcenterPoint_0_0_0"


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def _extract_mm(val_str):
    if not val_str:
        return ""
    try:
        return float(str(val_str).replace("mm", "").strip())
    except ValueError:
        return ""


def eval_expression(fields, soln, build_stack_fn, label):
    """
    Try one field-calculator stack sequence.
    build_stack_fn() builds the expression on the cleared stack.
    """
    try:
        fields.CalcStack("clear")
        build_stack_fn()
        fields.ClcEval(soln, [])
        val = fields.GetTopEntryValue(soln, [])
        return val
    except Exception as exc:
        raise Exception("%s: %s" % (label, str(exc)[:200]))


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_final  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Project: %s" % PROJECT_PATH)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception as exc:
            log(f, "OpenProject (may already be open): %s" % str(exc)[:100])

        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields = oDesign.GetModule("FieldsReporter")
        soln = "Setup1 : LastAdaptive"

        # Read design variables
        var_values = {}
        for vn in ["a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
                log(f, "  %s = %s" % (vn, var_values[vn]))
            except Exception:
                var_values[vn] = ""
                log(f, "  %s: read failed" % vn)

        results = {}

        # ---- |B| at center point ----
        # Replicate the working pattern from export_Bcenter_1ceng_nominal.py.
        # Try 4 different stack orders.
        log(f, "")
        log(f, "=== |B| magnitude at center point ===")

        mag_attempts = [
            ("point_then_Mag_B", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.CopyNamedExprToStack("Mag_B"),
            )),
            ("Mag_B_then_point", lambda: (
                fields.CopyNamedExprToStack("Mag_B"),
                fields.EnterPoint(POINT_NAME),
            )),
            ("point_then_B_mag", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
            )),
            ("B_mag_then_point", lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
            )),
        ]

        for label, build in mag_attempts:
            try:
                val = eval_expression(fields, soln, build, label)
                log(f, "  %s = %s" % (label, val))
                results["Bcenter_T"] = val
                break
            except Exception as exc:
                log(f, "  %s: %s" % (label, str(exc)[:200]))

        # ---- B vector components at center point ----
        # Try to get Bx, By, Bz using similar patterns
        log(f, "")
        log(f, "=== B vector components at center point ===")

        # For components, try:
        #   EnterQty("B") -> CalcOp("ScalarX")  (intrinsic B -> scalar X)
        #   CopyNamedExprToStack("ComplexMag_Bx") etc.
        #   EnterQty("Bx") (intrinsic scalar)

        component_attempts = {
            "Bcenter_Bx_T": [
                ("point_B_ScalarX", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarX"),
                )),
                ("B_ScalarX_point", lambda: (
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarX"),
                    fields.EnterPoint(POINT_NAME),
                )),
                ("ComplexMag_Bx", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.CopyNamedExprToStack("ComplexMag_Bx"),
                )),
                ("Bx_qty", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("Bx"),
                    fields.CalcOp("Mag"),
                )),
            ],
            "Bcenter_By_T": [
                ("point_B_ScalarY", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarY"),
                )),
                ("B_ScalarY_point", lambda: (
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarY"),
                    fields.EnterPoint(POINT_NAME),
                )),
                ("ComplexMag_By", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.CopyNamedExprToStack("ComplexMag_By"),
                )),
                ("By_qty", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("By"),
                    fields.CalcOp("Mag"),
                )),
            ],
            "Bcenter_Bz_T": [
                ("point_B_ScalarZ", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarZ"),
                )),
                ("B_ScalarZ_point", lambda: (
                    fields.EnterQty("B"),
                    fields.CalcOp("ScalarZ"),
                    fields.EnterPoint(POINT_NAME),
                )),
                ("ComplexMag_Bz", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.CopyNamedExprToStack("ComplexMag_Bz"),
                )),
                ("Bz_qty", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("Bz"),
                    fields.CalcOp("Mag"),
                )),
            ],
        }

        for out_key, attempts in component_attempts.items():
            for label, build in attempts:
                try:
                    val = eval_expression(fields, soln, build, label)
                    log(f, "  %s -> %s = %s" % (label, out_key, val))
                    results[out_key] = val
                    break
                except Exception as exc:
                    log(f, "  %s -> %s: %s" % (label, out_key, str(exc)[:200]))

        # ---- Write CSV ----
        a_mm = _extract_mm(var_values.get("a", ""))
        g_mm = _extract_mm(var_values.get("g", ""))
        T_mm = _extract_mm(var_values.get("T", ""))

        csv_cols = [
            "experiment", "layer", "T_mm", "a_mm", "g_mm",
            "Bcenter_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
        ]
        csv_row = {
            "experiment": "fixedT10_g02_ext",
            "layer": 4,
            "T_mm": T_mm,
            "a_mm": a_mm,
            "g_mm": g_mm,
        }
        csv_row.update(results)

        lines = [",".join(csv_cols)]
        lines.append(",".join([str(csv_row.get(c, "")) for c in csv_cols]))
        with open(OUT_CSV, "w") as fh:
            fh.write("\n".join(lines))

        log(f, "")
        log(f, "Wrote: %s" % OUT_CSV)
        for c in csv_cols:
            log(f, "  %s = %s" % (c, csv_row.get(c, "N/A")))
        log(f, "Done.")


run()
