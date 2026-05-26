"""
export_Bcenter_v2.py
====================
Export B field at center point using field calculator intrinsic B quantities.
IronPython 2.7 compatible.

The key insight: Named expressions like "Mag_B" don't exist by default.
We must build the field calculation from intrinsic quantities using
the field calculator's Enter* / CalcOp API.
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_v2.log"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def eval_at_point(fields, soln, point, calc_ops):
    """
    Evaluate a field quantity at a point using field calculator operations.

    calc_ops: list of (operation, params) tuples to build the expression.
    Example for |B| at point:
        [("EnterVector", ["Bx", "By", "Bz"]), ("Mag", []), ("Value", [])]
    """
    fields.CalcStack("clear")
    for op_name, op_params in calc_ops:
        if op_params:
            fields.CalcOp(op_name, op_params)
        else:
            fields.CalcOp(op_name)
    fields.EnterGrid(point)
    fields.CalcOp("Value")
    fields.ClcEval(soln, [])
    return fields.GetTopEntryValue(soln, [])


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_v2 %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        oDesktop.OpenProject(PROJECT_PATH)
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields  = oDesign.GetModule("FieldsReporter")

        soln  = "Setup1 : LastAdaptive"
        point = "BcenterPoint_0_0_0"

        # Read design variables
        var_values = {}
        for vn in ["a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
            except Exception:
                var_values[vn] = ""

        results = {}

        # ---- Try each approach to get B field at center ----

        # Approach A: Named expressions that AEDT creates internally
        log(f, "--- Named expression attempts ---")
        for name in ["Mag_B", "MagB", "B_Mag", "ComplexMag_B", "B"]:
            try:
                fields.CalcStack("clear")
                fields.CopyNamedExprToStack(name)
                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                val = fields.GetTopEntryValue(soln, [])
                log(f, "  %s = %s" % (name, val))
            except Exception as e:
                log(f, "  %s: %s" % (name, str(e)[:100]))

        # Approach B: Use EnterVector for B field, then Mag
        log(f, "")
        log(f, "--- Intrinsic B vector -> Mag ---")
        try:
            # The intrinsic B vector is accessed via Input -> Quantity -> B
            # In the field calculator API, this is "EnterVector" with B components
            for vec_spec in [["Bx", "By", "Bz"], ["BX", "BY", "BZ"]]:
                try:
                    fields.CalcStack("clear")
                    fields.EnterVector(vec_spec)
                    fields.CalcOp("Mag")
                    fields.EnterGrid(point)
                    fields.CalcOp("Value")
                    fields.ClcEval(soln, [])
                    val = fields.GetTopEntryValue(soln, [])
                    log(f, "  EnterVector(%s)->Mag = %s" % (vec_spec, val))
                    results["Bcenter_T"] = val
                    break
                except Exception as e2:
                    log(f, "  EnterVector(%s)->Mag: %s" % (vec_spec, str(e2)[:100]))
        except Exception as e:
            log(f, "  Intrinsic vector approach: %s" % str(e)[:200])

        # Approach C: Get B components individually via EnterScalar
        log(f, "")
        log(f, "--- Intrinsic B scalar components ---")
        for comp, key in [("Bx", "Bcenter_Bx_T"), ("By", "Bcenter_By_T"), ("Bz", "Bcenter_Bz_T")]:
            try:
                fields.CalcStack("clear")
                fields.EnterScalar(comp)
                fields.CalcOp("Complex")
                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                val = fields.GetTopEntryValue(soln, [])
                log(f, "  %s = %s" % (comp, val))
                results[key] = val
            except Exception as e:
                log(f, "  %s: %s" % (comp, str(e)[:100]))

        # Approach D: Use EnterScalarFunc for the B field
        log(f, "")
        log(f, "--- EnterScalarFunc ---")
        for func_name in ["B", "H", "<Bx,By,Bz>"]:
            try:
                fields.CalcStack("clear")
                fields.EnterScalarFunc(func_name)
                fields.CalcOp("Complex")
                fields.CalcOp("CmplxMag")
                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                val = fields.GetTopEntryValue(soln, [])
                log(f, "  EnterScalarFunc(%s)->CmplxMag = %s" % (func_name, val))
                if "Bcenter_T" not in results or not results["Bcenter_T"]:
                    results["Bcenter_T"] = val
            except Exception as e:
                log(f, "  EnterScalarFunc(%s): %s" % (func_name, str(e)[:100]))

        # Approach E: Try the Quantity approach
        log(f, "")
        log(f, "--- Input Quantity approach ---")
        for qty_name in ["B", "Mag_B", "B_Vector"]:
            try:
                fields.CalcStack("clear")
                fields.EnterQty(qty_name)
                fields.CalcOp("Complex")
                fields.CalcOp("CmplxMag")
                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                val = fields.GetTopEntryValue(soln, [])
                log(f, "  EnterQty(%s)->Complex->CmplxMag = %s" % (qty_name, val))
                results["Bcenter_T"] = val
            except Exception as e:
                log(f, "  EnterQty(%s): %s" % (qty_name, str(e)[:100]))

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


def _extract_mm(val_str):
    if not val_str:
        return ""
    try:
        return float(str(val_str).replace("mm", "").strip())
    except ValueError:
        return ""


run()
