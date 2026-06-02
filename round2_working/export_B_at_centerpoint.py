"""
export_B_at_centerpoint.py
===========================
Robust B-field export at the center point (BcenterPoint_0_0_0) using the
AEDT Reports API, which is more reliable than the raw field calculator.

Use this after Setup1 has been analyzed in the external-field model.

Output columns depend on MODE:
  MODE = "Bcenter": experiment, layer, T_mm, a_mm, g_mm,
                    Bcenter_T, Bcenter_Bx_T, Bcenter_By_T, Bcenter_Bz_T
  MODE = "B0":      experiment, layer, T_mm, a_mm, g_mm,
                    B0_T, B0_Bx_T, B0_By_T, B0_Bz_T
"""

import csv
import os
import time
import traceback

# ---------- user settings ----------
# Set PROJECT_PATH and MODE for the case you want to export.
# Run once with MODE="Bcenter" on the shield model, then
#      once with MODE="B0"      on the B0 reference model.

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
MODE         = "Bcenter"   # "Bcenter" or "B0"

OUT_CSV  = r"D:\ferrite\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_%s.csv"
LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\export_B_at_centerpoint.log"

EXPERIMENT = "fixedT10_g02_external"
LAYER      = 4
# --------------------------------


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def run():
    out_csv = OUT_CSV % MODE
    if not os.path.isdir(os.path.dirname(out_csv)):
        os.makedirs(os.path.dirname(out_csv))

    with open(LOG_PATH, "w") as f:
        log(f, "export_B_at_centerpoint  MODE=%s  %s" % (MODE, time.strftime("%Y-%m-%d %H:%M:%S")))
        log(f, "Project: %s" % PROJECT_PATH)
        log(f, "Output:  %s" % out_csv)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception:
            log(f, "OpenProject skipped (may already be open)")

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        oModule  = oDesign.GetModule("ReportSetup")
        fields   = oDesign.GetModule("FieldsReporter")

        # ---- read design variables ----
        var_values = {}
        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
                log(f, "  %s = %s" % (vn, var_values[vn]))
            except Exception:
                var_values[vn] = ""
                log(f, "  %s: read failed" % vn)

        # ---- try Report-based export first ----
        soln = "Setup1 : LastAdaptive"
        report_name = "Bcenter_export_%s" % MODE

        # Remove old report if exists
        try:
            oModule.DeleteReport(report_name)
        except Exception:
            pass

        # Create a data-table report for B at the center point
        try:
            oModule.CreateReport(
                report_name,
                "Fields",
                "Data Table",
                soln,
                [
                    "Context:=", "BcenterPoint_0_0_0",
                ],
                [
                    "X Component:=", "Mag_B",
                    "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"],
                ],
            )
            log(f, "  CreateReport: OK")
            report_ok = True
        except Exception:
            log(f, "  CreateReport: FAILED, trying field-calculator fallback")
            log(f, traceback.format_exc())
            report_ok = False

        values = {}
        if report_ok:
            # Export report to CSV, then parse
            tmp_csv = out_csv.replace(".csv", "_raw.csv")
            try:
                oModule.ExportToFile(report_name, tmp_csv)
                log(f, "  ExportToFile: OK -> %s" % tmp_csv)
                # Parse the raw CSV to get scalar values
                values = _parse_report_csv(tmp_csv, MODE)
                log(f, "  Parsed values: %s" % str(values))
            except Exception:
                log(f, "  ExportToFile: FAILED")
                log(f, traceback.format_exc())
                report_ok = False

        if not report_ok or not values:
            # ---- field-calculator fallback ----
            log(f, "  Using field-calculator fallback...")
            expr_map = {
                "Bcenter": [
                    ("Bcenter_T"   , "Mag_B"),
                    ("Bcenter_Bx_T", "ComplexMag_Bx"),
                    ("Bcenter_By_T", "ComplexMag_By"),
                    ("Bcenter_Bz_T", "ComplexMag_Bz"),
                ],
                "B0": [
                    ("B0_T"   , "Mag_B"),
                    ("B0_Bx_T", "ComplexMag_Bx"),
                    ("B0_By_T", "ComplexMag_By"),
                    ("B0_Bz_T", "ComplexMag_Bz"),
                ],
            }

            for out_name, expr_name in expr_map[MODE]:
                try:
                    fields.CalcStack("clear")
                    fields.CopyNamedExprToStack(expr_name)
                    fields.EnterGrid("BcenterPoint_0_0_0")
                    fields.CalcOp("Value")
                    fields.ClcEval(soln, [])
                    val = fields.GetTopEntryValue(soln, [])
                    try:
                        values[out_name] = float(val)
                    except (TypeError, ValueError):
                        values[out_name] = str(val) if val is not None else ""
                    log(f, "    %s = %s" % (out_name, values[out_name]))
                except Exception:
                    log(f, "    %s: FAILED" % out_name)
                    values[out_name] = ""

        # ---- write output CSV ----
        a_mm = _extract_mm(var_values.get("a", ""))
        g_mm = _extract_mm(var_values.get("g", ""))
        T_mm = _extract_mm(var_values.get("T", ""))

        # Dynamically determine fieldnames based on MODE
        prefix = "Bcenter" if MODE == "Bcenter" else "B0"
        fieldnames = [
            "experiment", "layer", "T_mm", "a_mm", "g_mm",
            "%s_T" % prefix,
            "%s_Bx_T" % prefix,
            "%s_By_T" % prefix,
            "%s_Bz_T" % prefix,
        ]

        with open(out_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
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

        log(f, "Wrote: %s" % out_csv)
        log(f, "Done.")


def _extract_mm(val_str):
    """Extract numeric mm value from a string like '2.35mm'."""
    if not val_str:
        return ""
    try:
        return float(str(val_str).replace("mm", "").strip())
    except ValueError:
        return ""


def _parse_report_csv(path, mode):
    """Parse a raw AEDT report CSV to extract field values at the center point."""
    values = {}
    prefix = "Bcenter" if mode == "Bcenter" else "B0"

    if not os.path.exists(path):
        return values

    with open(path, "r") as fh:
        content = fh.read()

    # AEDT report CSVs have a specific format. Try to extract the numeric values.
    lines = content.strip().split("\n")
    # The last few lines typically contain the data
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith('"'):
            continue
        parts = line.split(",")
        if len(parts) >= 4:
            try:
                mag_b  = float(parts[0]) if parts[0].strip() else None
                mag_bx = float(parts[1]) if len(parts) > 1 and parts[1].strip() else None
                mag_by = float(parts[2]) if len(parts) > 2 and parts[2].strip() else None
                mag_bz = float(parts[3]) if len(parts) > 3 and parts[3].strip() else None

                if mag_b is not None:
                    values["%s_T" % prefix]    = mag_b
                if mag_bx is not None:
                    values["%s_Bx_T" % prefix] = mag_bx
                if mag_by is not None:
                    values["%s_By_T" % prefix] = mag_by
                if mag_bz is not None:
                    values["%s_Bz_T" % prefix] = mag_bz
                break  # Take first data row
            except (ValueError, IndexError):
                continue

    return values


run()
