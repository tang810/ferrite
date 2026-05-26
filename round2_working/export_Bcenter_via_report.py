# -*- coding: utf-8 -*-
"""
export_Bcenter_via_report.py
============================
Export B field at center point using CreateReport (which works!) + ExportToFile.

The key insight from diagnose_fields2.py: CreateReport with 7 args succeeds.
We create a "Fields" / "Data Table" report at BcenterPoint_0_0_0,
export it to CSV, and parse the numeric values.
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_Bcenter.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_Bcenter_via_report.log"
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


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_Bcenter_via_report  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
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

        # ---- Step 1: Create field report at center point ----
        log(f, "")
        log(f, "=== Creating field report ===")
        report_name = "BcenterExport"

        # Remove old report(s) by this or similar names
        for old_name in [report_name, "BcenterExport1", "BcenterExport2"]:
            try:
                oModule.DeleteReport(old_name)
                log(f, "  Deleted old report: %s" % old_name)
            except Exception:
                pass

        report_created = False
        try:
            # CreateReport with 7 args (the version that works)
            # Arg format: name, type, displayType, soln, context, pointSet, expressions
            oModule.CreateReport(
                report_name,
                "Fields",
                "Data Table",
                soln,
                ["Context:=", POINT_NAME],
                [],
                [
                    "X Component:=", "Mag_B",
                    "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"],
                ],
            )
            log(f, "  CreateReport: OK")
            report_created = True
        except Exception as exc:
            log(f, "  CreateReport: %s" % str(exc)[:300])
            # Maybe the report was renamed by AEDT
            report_created = True  # It might have succeeded under a different name

        # ---- Step 2: Export report to CSV ----
        log(f, "")
        log(f, "=== Exporting report ===")
        raw_csv = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_bcenter_raw.csv"

        # Try to export - AEDT might have renamed the report
        export_ok = False
        for try_name in [report_name, "BcenterExport1", "BcenterExport2"]:
            try:
                oModule.ExportToFile(try_name, raw_csv)
                log(f, "  ExportToFile(%s): OK -> %s" % (try_name, raw_csv))
                export_ok = True
                break
            except Exception as exc:
                log(f, "  ExportToFile(%s): %s" % (try_name, str(exc)[:150]))

        if not export_ok:
            # Try exporting all reports to see what names exist
            log(f, "  Trying to find report by listing...")
            for try_name in ["BcenterExport3", "BcenterExport4"]:
                try:
                    oModule.ExportToFile(try_name, raw_csv)
                    log(f, "  ExportToFile(%s): OK" % try_name)
                    export_ok = True
                    break
                except Exception:
                    pass

        # ---- Step 3: Parse the exported CSV ----
        log(f, "")
        log(f, "=== Parsing exported data ===")
        if export_ok and os.path.exists(raw_csv):
            with open(raw_csv, "r") as fh:
                content = fh.read()
            log(f, "  Raw CSV content:")
            for line in content.strip().split("\n"):
                log(f, "    |%s|" % line)

            parsed = {}
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                # Skip header/metadata lines
                if not line or line.startswith("#") or line.startswith('"'):
                    continue
                parts = line.split(",")
                nums = []
                for p in parts:
                    try:
                        nums.append(float(p.strip()))
                    except (ValueError, TypeError):
                        pass
                if len(nums) >= 1:
                    parsed["Bcenter_T"] = nums[0]
                    log(f, "  Bcenter_T = %s" % nums[0])
                if len(nums) >= 2:
                    parsed["Bcenter_Bx_T"] = nums[1]
                    log(f, "  Bcenter_Bx_T = %s" % nums[1])
                if len(nums) >= 3:
                    parsed["Bcenter_By_T"] = nums[2]
                    log(f, "  Bcenter_By_T = %s" % nums[2])
                if len(nums) >= 4:
                    parsed["Bcenter_Bz_T"] = nums[3]
                    log(f, "  Bcenter_Bz_T = %s" % nums[3])
                if nums:
                    break  # Take first data row
            results.update(parsed)
        else:
            log(f, "  No raw CSV to parse (export_ok=%s, exists=%s)" % (
                export_ok, os.path.exists(raw_csv)))

        # ---- Step 4: If report approach failed, try CreateFieldPlot ----
        if not results.get("Bcenter_T"):
            log(f, "")
            log(f, "=== CreateFieldPlot fallback ===")
            fields = oDesign.GetModule("FieldsReporter")
            plot_name = "BcenterFieldPlot"
            try:
                fields.DeleteFieldPlot(plot_name)
            except Exception:
                pass

            try:
                fields.CreateFieldPlot(
                    plot_name,
                    "Fields",
                    "Mag_B",
                    soln,
                    ["Context:=", POINT_NAME],
                    ["X Component:=", "Mag_B", "Y Component:=", ["ComplexMag_Bx", "ComplexMag_By", "ComplexMag_Bz"]],
                    [],
                )
                log(f, "  CreateFieldPlot: OK")
            except Exception as exc:
                log(f, "  CreateFieldPlot: %s" % str(exc)[:300])

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


run()
