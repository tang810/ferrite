# -*- coding: utf-8 -*-
"""
export_Bcenter_working.py
=========================
Export B field at center point using the WORKING field calculator sequence:
  EnterQty("B") -> CalcOp("Mag") -> EnterPoint(point) -> CalcOp("Value")
  -> GetTopEntryValue(soln, [])

Confirmed working on AEDT 2025 R1 (test_calcop_eval.py Test 4).
Result: Bcenter = 2.005e-9 T for 4ceng external field model.
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_working.log"
POINT_NAME = "BcenterPoint_0_0_0"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def _extract_mm(val_str):
    if not val_str:
        return ""
    try:
        return float(str(val_str).replace("mm", "").strip())
    except ValueError:
        return ""


def _extract_value(val):
    """Handle GetTopEntryValue return format: a list like ['1.23E-09']."""
    if val is None:
        return None
    if isinstance(val, list):
        try:
            return float(val[0])
        except (ValueError, TypeError, IndexError):
            return str(val[0]) if val else ""
    try:
        return float(val)
    except (ValueError, TypeError):
        return str(val)


def eval_at_point(fields, soln, build_stack_fn, label):
    """
    Build stack, CalcOp("Value"), GetTopEntryValue.
    """
    fields.CalcStack("clear")
    build_stack_fn()
    fields.CalcOp("Value")
    val = fields.GetTopEntryValue(soln, [])
    return val


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_working  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Project: %s" % PROJECT_PATH)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception as exc:
            log(f, "OpenProject: %s" % str(exc)[:100])

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields   = oDesign.GetModule("FieldsReporter")
        soln     = "Setup1 : LastAdaptive"

        # Read design variables
        var_values = {}
        for vn in ["a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
                log(f, "  %s = %s" % (vn, var_values[vn]))
            except Exception:
                var_values[vn] = ""

        results = {}

        # ---- |B| magnitude at center ----
        # Working sequence: EnterQty("B") -> CalcOp("Mag") -> EnterPoint -> CalcOp("Value")
        log(f, "")
        log(f, "=== B magnitude at center ===")
        try:
            raw = eval_at_point(fields, soln, lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
            ), "Bmag")
            val = _extract_value(raw)
            log(f, "  Bcenter_T = %s (raw: %s)" % (val, raw))
            if val is not None:
                results["Bcenter_T"] = val
        except Exception as exc:
            log(f, "  Bcenter_T FAILED: %s" % str(exc)[:200])

        # ---- B vector components at center ----
        # Try: EnterQty("B") -> CalcOp("ScalarX") -> EnterPoint -> CalcOp("Value")
        # Or: EnterQty("Bx") -> CalcOp("Mag") -> EnterPoint -> CalcOp("Value")
        log(f, "")
        log(f, "=== B vector components at center ===")

        for comp, key, scal_op in [
            ("Bx", "Bcenter_Bx_T", "ScalarX"),
            ("By", "Bcenter_By_T", "ScalarY"),
            ("Bz", "Bcenter_Bz_T", "ScalarZ"),
        ]:
            # Approach 1: EnterQty("B") -> ScalarX/Y/Z -> EnterPoint -> Value
            try:
                raw = eval_at_point(fields, soln, lambda co=scal_op: (
                    fields.EnterQty("B"),
                    fields.CalcOp(co),
                    fields.EnterPoint(POINT_NAME),
                ), "B%s_Scalar" % comp)
                val = _extract_value(raw)
                log(f, "  %s (Scalar approach) = %s (raw: %s)" % (key, val, raw))
                if val is not None:
                    results[key] = val
                continue
            except Exception as exc:
                log(f, "  %s Scalar: %s" % (key, str(exc)[:150]))

            # Approach 2: EnterQty("Bx") -> Mag -> EnterPoint -> Value
            try:
                raw = eval_at_point(fields, soln, lambda c=comp: (
                    fields.EnterQty(c),
                    fields.CalcOp("Mag"),
                    fields.EnterPoint(POINT_NAME),
                ), "B%s_qty" % comp)
                val = _extract_value(raw)
                log(f, "  %s (Qty approach) = %s (raw: %s)" % (key, val, raw))
                if val is not None:
                    results[key] = val
                continue
            except Exception as exc:
                log(f, "  %s Qty: %s" % (key, str(exc)[:150]))

            # Approach 3: Try CopyNamedExprToStack("ComplexMag_Bx") -> EnterPoint -> Value
            try:
                raw = eval_at_point(fields, soln, lambda c=comp: (
                    fields.CopyNamedExprToStack("ComplexMag_%s" % c),
                    fields.EnterPoint(POINT_NAME),
                ), "B%s_named" % comp)
                val = _extract_value(raw)
                log(f, "  %s (Named approach) = %s (raw: %s)" % (key, val, raw))
                if val is not None:
                    results[key] = val
                continue
            except Exception as exc:
                log(f, "  %s Named: %s" % (key, str(exc)[:150]))

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
