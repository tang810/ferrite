"""
export_Bcenter_simple.py
========================
Simple, robust B-field export at the center point for IronPython 2.7.
Writes SF_4ceng_fixedT10_g02_Bcenter.csv.
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_simple.log"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_simple %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        oDesktop.OpenProject(PROJECT_PATH)
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields  = oDesign.GetModule("FieldsReporter")

        # Read design variables
        var_values = {}
        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
            except Exception:
                var_values[vn] = ""
        log(f, "a=%s g=%s T=%s" % (var_values.get("a"), var_values.get("g"), var_values.get("T")))

        soln = "Setup1 : LastAdaptive"
        point = "BcenterPoint_0_0_0"

        # Dictionary to store results
        results = {}
        errors = {}

        # Approach: Use field calculator intrinsic operations.
        # In Maxwell 3D, the intrinsic B field is accessed via the "Quantity" menu
        # in the field calculator. The named expression approach uses user-defined
        # expressions which don't exist by default.
        #
        # Instead, we build the field calculation from intrinsic quantities:
        #   Input -> Quantity -> B
        #   Vector -> Scal? -> ScalarX/Y/Z  or  Complex -> CmplxMag
        #   Output -> Value
        #   EnterGrid -> point_name
        #   Eval

        # Try using FieldsReporter.GetFieldValueAtPoint or similar simpler API
        # Actually, let's use the ExportToFile with a point-based path

        # ---- Method 1: Try to get field values via GetFieldValue ----
        log(f, "")
        log(f, "=== Trying GetFieldValue approach ===")
        for expr_name in ["Mag_B", "B", "B_x", "B_y", "B_z"]:
            try:
                val = fields.GetFieldValue(point, expr_name, soln)
                log(f, "  GetFieldValue(%s) = %s" % (expr_name, val))
            except Exception:
                log(f, "  GetFieldValue(%s): failed" % expr_name)

        # ---- Method 2: Build field calc manually ----
        log(f, "")
        log(f, "=== Field calculator approach ===")

        def eval_field_expr(expr_name_or_sequence):
            """Evaluate a field expression at the center point.
            The sequence can be either a named expression or a list of calc ops."""
            try:
                fields.CalcStack("clear")
                if isinstance(expr_name_or_sequence, list):
                    for op in expr_name_or_sequence:
                        if isinstance(op, tuple):
                            fields.CalcOp(op[0], op[1])
                        else:
                            fields.CalcOp(op)
                else:
                    fields.CopyNamedExprToStack(expr_name_or_sequence)

                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                return fields.GetTopEntryValue(soln, [])
            except Exception as e:
                raise Exception("eval_field_expr failed: %s" % str(e))

        # Build B magnitude from components using intrinsic B vector
        # Sequence: Input(Quantity=B), Complex, CmplxMag, Value @ point
        calc_sequences = {
            "Bcenter_T": [
                "EnterVector",  # Select B vector
                ("Complex", []),
                ("CmplxMag", []),
            ],
            # Alternative: try named expressions for field calculator
            "Bcenter_Bx_T": "ComplexMag_Bx",
            "Bcenter_By_T": "ComplexMag_By",
            "Bcenter_Bz_T": "ComplexMag_Bz",
            "Bcenter_T_v2": "ComplexMag_B",
        }

        # Actually, let me try the simplest possible approach first:
        # Use the field reporter's built-in expression evaluation
        log(f, "")
        log(f, "=== Direct expression evaluation ===")

        # Try intrinsic field quantities via the field calculator
        for try_name in ["Mag_B", "ComplexMag_B", "B"]:
            try:
                fields.CalcStack("clear")
                fields.CopyNamedExprToStack(try_name)
                fields.EnterGrid(point)
                fields.CalcOp("Value")
                fields.ClcEval(soln, [])
                val = fields.GetTopEntryValue(soln, [])
                log(f, "  %s at point: %s" % (try_name, val))
                if try_name == "ComplexMag_B":
                    results["Bcenter_T"] = val
                if try_name == "Mag_B":
                    results["Bcenter_T"] = val
            except Exception as e:
                log(f, "  %s: %s" % (try_name, str(e)[:200]))

        # Try the field export file approach
        log(f, "")
        log(f, "=== ExportToFile approach ===")

        # Export B field on a grid that includes just the center point
        point_list_file = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_point.pts"
        with open(point_list_file, "w") as pf:
            pf.write("0 0 0\n")

        try:
            fields.ExportToFile(
                r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_field.fld",
                point_list_file,
                soln,
                ["Mag_B"],
            )
            log(f, "  ExportToFile: OK")
        except Exception as e:
            log(f, "  ExportToFile: %s" % str(e)[:200])

        # ---- Write CSV with whatever results we have ----
        log(f, "")
        log(f, "=== Writing CSV ===")
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
            "Bcenter_T": results.get("Bcenter_T", ""),
            "Bcenter_Bx_T": results.get("Bcenter_Bx_T", ""),
            "Bcenter_By_T": results.get("Bcenter_By_T", ""),
            "Bcenter_Bz_T": results.get("Bcenter_Bz_T", ""),
        }

        # Write CSV manually (IronPython 2.7 compatible)
        lines = [",".join(csv_cols)]
        lines.append(",".join([str(csv_row.get(c, "")) for c in csv_cols]))
        with open(OUT_CSV, "w") as fh:
            fh.write("\n".join(lines))
        log(f, "Wrote: %s" % OUT_CSV)
        log(f, "Done.")


def _extract_mm(val_str):
    if not val_str:
        return ""
    try:
        return float(str(val_str).replace("mm", "").strip())
    except ValueError:
        return ""


run()
