"""
export_Bcenter_field.py
=======================
Export B-field at origin (center point) from a solved Maxwell 3D project.
Used for SF (shielding factor) calculation.

Run after Setup1 has been analyzed.

Output columns:
  experiment, layer, T_mm, a_mm, g_mm,
  Bcenter_T, Bcenter_Bx_T, Bcenter_By_T, Bcenter_Bz_T
"""

import csv
import os
import time
import traceback

# ---------- user settings ----------
PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_external.aedt"
OUT_CSV      = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH     = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_field.log"
# --------------------------------

CENTRE_POINT  = "BcenterPoint_0_0_0"
SOLUTION_NAME = "Setup1 : LastAdaptive"
EXPERIMENT    = "fixedT10_g02_external"
LAYER         = 4

# The field calculator expressions we want
EXPRESSIONS = [
    ("Bcenter_T"   , "Mag_B"),
    ("Bcenter_Bx_T", "ComplexMag_Bx"),
    ("Bcenter_By_T", "ComplexMag_By"),
    ("Bcenter_Bz_T", "ComplexMag_Bz"),
]


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_field  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Project: %s" % PROJECT_PATH)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception:
            log(f, "OpenProject skipped (maybe already open)")

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields   = oDesign.GetModule("FieldsReporter")

        # Read design variables
        var_values = {}
        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            try:
                var_values[vn] = oDesign.GetVariableValue(vn)
                log(f, "  %s = %s" % (vn, var_values[vn]))
            except Exception:
                log(f, "  %s: read failed" % vn)

        # Set up field calculator
        fields.EnterFieldClc()
        fields.CopyNamedExprToStack("Mag_B")
        fields.CalcOp("Complex")
        fields.EnterScalar(0)
        fields.EnterGrid(CENTRE_POINT)
        fields.CalcOp("Value")
        try:
            result = fields.GetTopEntryValue(SOLUTION_NAME, [])
            log(f, "  Mag_B at centre = %s" % str(result))
        except Exception:
            result = "FAILED"
            log(f, "  Mag_B at centre: FAILED")
            log(f, traceback.format_exc())

        # Actually, the field calculator API above is complex and may not work.
        # Let's use the FieldsReporter export method instead.

        # Alternative: export fields at point via the standard export
        values = {}
        errors  = {}

        for out_name, expr_name in EXPRESSIONS:
            try:
                fields.CalcStack("clear")
                fields.CopyNamedExprToStack(expr_name)
                fields.EnterGrid(CENTRE_POINT)
                fields.CalcOp("Value")
                val = fields.GetTopEntryValue(SOLUTION_NAME, [])
                # Try to convert to float
                try:
                    values[out_name] = float(val)
                except (TypeError, ValueError):
                    values[out_name] = str(val)
                log(f, "  %s = %s" % (out_name, values[out_name]))
            except Exception:
                errors[out_name] = traceback.format_exc()
                log(f, "  %s: FAILED" % out_name)
                log(f, errors[out_name])

        # Write CSV
        a_mm = None
        g_mm = None
        T_mm = None
        try:
            a_mm = float(str(var_values.get("a", "")).replace("mm", ""))
        except Exception:
            pass
        try:
            g_mm = float(str(var_values.get("g", "")).replace("mm", ""))
        except Exception:
            pass
        try:
            T_mm = float(str(var_values.get("T", "")).replace("mm", ""))
        except Exception:
            pass

        os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
        with open(OUT_CSV, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "experiment", "layer", "T_mm", "a_mm", "g_mm",
                    "Bcenter_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
                ],
            )
            writer.writeheader()
            row = {
                "experiment": EXPERIMENT,
                "layer": LAYER,
                "T_mm": T_mm,
                "a_mm": a_mm,
                "g_mm": g_mm,
            }
            row.update(values)
            writer.writerow(row)

        log(f, "Wrote %s" % OUT_CSV)
        log(f, "Done.")


run()
