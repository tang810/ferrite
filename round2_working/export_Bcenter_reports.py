# -*- coding: utf-8 -*-
"""
export_Bcenter_reports.py
=========================
Export B field at center point using the Reports/ExportToFile approach.

Strategy:
  1. Create named expressions for Mag_B if they don't exist
  2. Use CreateReport with proper field expressions
  3. Export report to CSV and parse
  4. Fall back: ExportToFile with point list
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_reports.log"
POINT_NAME = "BcenterPoint_0_0_0"
POINT_FILE = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_point.pts"


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


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_reports  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        # Write point file
        with open(POINT_FILE, "w") as pf:
            pf.write("0 0 0\n")

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
        oModule  = oDesign.GetModule("ReportSetup")
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

        # ---- Step 1: Add named expressions for B field ----
        log(f, "")
        log(f, "=== Adding named expressions ===")

        # In AEDT, we can add named expressions to the field calculator.
        # "Mag_B" = magnitude of B vector
        # "ComplexMag_Bx" = magnitude of Bx component, etc.

        named_exprs = [
            ("Mag_B", "Mag(B)"),
            ("ComplexMag_Bx", "Mag(Bx)"),
            ("ComplexMag_By", "Mag(By)"),
            ("ComplexMag_Bz", "Mag(Bz)"),
        ]

        for name, expr in named_exprs:
            try:
                # Try AddNamedExpression first
                fields.AddNamedExpression(name, expr)
                log(f, "  AddNamedExpression(%s, %s): OK" % (name, expr))
            except Exception as e1:
                try:
                    # Alternative method name
                    fields.AddNamedExpr(name, expr)
                    log(f, "  AddNamedExpr(%s, %s): OK" % (name, expr))
                except Exception as e2:
                    log(f, "  AddNamedExpression(%s): FAILED (%s / %s)" % (name, str(e1)[:60], str(e2)[:60]))

        # ---- Step 2: Try creating a field data table report ----
        log(f, "")
        log(f, "=== Field Data Table Report ===")

        report_name = "BcenterDataTable"
        try:
            oModule.DeleteReport(report_name)
            log(f, "  Deleted old report")
        except Exception:
            pass

        # For a "Data Table" report at a point in Maxwell 3D:
        # The report type is "Fields", display type "Data Table"
        # simValueCtxt: ["Context:=", point_name]
        # expressions: list of trace expressions
        try:
            oModule.CreateReport(
                report_name,
                "Fields",
                "Data Table",
                soln,
                ["Context:=", POINT_NAME],
                [
                    "X Component:=", "Mag_B",
                    "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"],
                ],
            )
            log(f, "  CreateReport: OK")
            report_ok = True
        except Exception as exc:
            log(f, "  CreateReport: %s" % str(exc)[:300])
            report_ok = False

        if report_ok:
            tmp_csv = OUT_CSV.replace(".csv", "_raw.csv")
            try:
                oModule.ExportToFile(report_name, tmp_csv)
                log(f, "  ExportToFile: OK -> %s" % tmp_csv)
                # Parse the raw CSV
                if os.path.exists(tmp_csv):
                    with open(tmp_csv, "r") as fh:
                        content = fh.read()
                        log(f, "  Raw CSV content:")
                        for line in content.strip().split("\n")[:20]:
                            log(f, "    %s" % line)
                    # Try to extract numeric values
                    parsed = _parse_report_csv(tmp_csv)
                    results.update(parsed)
            except Exception as exc:
                log(f, "  ExportToFile: %s" % str(exc)[:200])

        # ---- Step 3: Try ExportToFile with point list ----
        log(f, "")
        log(f, "=== ExportToFile with point list ===")

        # Try different expression sets
        for idx, expr_set in enumerate([
            ["Mag_B"],
            ["ComplexMag_B"],
            ["B"],
            ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"],
        ]):
            out_fld = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_center_field_%d.fld" % idx
            try:
                fields.ExportToFile(out_fld, POINT_FILE, soln, expr_set)
                log(f, "  ExportToFile(%s): OK -> %s" % (expr_set, out_fld))
                if os.path.exists(out_fld):
                    with open(out_fld, "r") as fh:
                        content = fh.read()
                        log(f, "    Content:\n%s" % content[:500])
            except Exception as exc:
                log(f, "  ExportToFile(%s): %s" % (expr_set, str(exc)[:200]))

        # ---- Step 4: Try the field calculator with fldType parameter ----
        log(f, "")
        log(f, "=== Field calc with fldType parameter ===")

        for fld_type in [None, "Fields", "Mag_B", "Field"]:
            log(f, "--- fldType=%s ---" % fld_type)
            for label, build_fn in [
                ("Mag_B+point", lambda: (
                    fields.CopyNamedExprToStack("Mag_B"),
                    fields.EnterPoint(POINT_NAME),
                )),
                ("point+B+Mag", lambda: (
                    fields.EnterPoint(POINT_NAME),
                    fields.EnterQty("B"),
                    fields.CalcOp("Mag"),
                )),
            ]:
                try:
                    fields.CalcStack("clear")
                    build_fn()
                    if fld_type is not None:
                        fields.ClcEval(soln, [], fld_type)
                    else:
                        fields.ClcEval(soln, [])
                    val = fields.GetTopEntryValue(soln, [])
                    log(f, "  %s = %s" % (label, val))
                    if val is not None and "Bcenter_T" not in results:
                        results["Bcenter_T"] = val
                except Exception as exc:
                    log(f, "  %s: %s" % (label, str(exc)[:200]))

        # ---- Write final CSV ----
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


def _parse_report_csv(path):
    """Parse AEDT report CSV, extracting field values."""
    values = {}
    if not os.path.exists(path):
        return values
    with open(path, "r") as fh:
        content = fh.read()
    lines = content.strip().split("\n")
    # Look for data rows (comma-separated numbers)
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith('"'):
            continue
        parts = line.split(",")
        numeric_parts = []
        for p in parts:
            try:
                numeric_parts.append(float(p.strip()))
            except ValueError:
                numeric_parts.append(None)
        # First numeric value is typically Mag_B
        non_null = [x for x in numeric_parts if x is not None]
        if len(non_null) >= 1:
            values["Bcenter_T"] = non_null[0]
        if len(non_null) >= 2:
            values["Bcenter_Bx_T"] = non_null[1]
        if len(non_null) >= 3:
            values["Bcenter_By_T"] = non_null[2]
        if len(non_null) >= 4:
            values["Bcenter_Bz_T"] = non_null[3]
        if non_null:
            break
    return values


run()
