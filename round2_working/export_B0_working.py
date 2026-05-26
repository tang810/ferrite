# -*- coding: utf-8 -*-
"""
export_B0_working.py
====================
Export B0 field (no-shield reference) at center point.
Uses the same working field calculator sequence as export_Bcenter_working.py:
  EnterQty("B") -> CalcOp("Mag") -> EnterPoint(point) -> CalcOp("Value")
  -> GetTopEntryValue(soln, [])
"""

import os
import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_B0.aedt"
OUT_CSV  = r"D:\tangyumengnew\aaaaaaaaximukeji\analysis_ready\SF_4ceng_fixedT10_g02_B0.csv"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_B0_working.log"
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


def eval_at_point(fields, soln, build_stack_fn):
    fields.CalcStack("clear")
    build_stack_fn()
    fields.CalcOp("Value")
    return fields.GetTopEntryValue(soln, [])


def run():
    if not os.path.isdir(os.path.dirname(OUT_CSV)):
        os.makedirs(os.path.dirname(OUT_CSV))
    if not os.path.isdir(os.path.dirname(LOG_PATH)):
        os.makedirs(os.path.dirname(LOG_PATH))

    with open(LOG_PATH, "w") as f:
        log(f, "export_B0_working  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
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

        var_values = {}
        for vn in ["a", "g", "T"]:
            try:
                var_values[vn] = str(oDesign.GetVariableValue(vn))
                log(f, "  %s = %s" % (vn, var_values[vn]))
            except Exception:
                var_values[vn] = ""

        results = {}

        # ---- |B0| magnitude at center ----
        log(f, "")
        log(f, "=== B0 magnitude at center ===")
        try:
            raw = eval_at_point(fields, soln, lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
            ))
            val = _extract_value(raw)
            log(f, "  B0_T = %s (raw: %s)" % (val, raw))
            if val is not None:
                results["B0_T"] = val
        except Exception as exc:
            log(f, "  B0_T FAILED: %s" % str(exc)[:200])

        # ---- B0 vector components ----
        log(f, "")
        log(f, "=== B0 vector components at center ===")
        for comp, key, scal_op in [
            ("Bx", "B0_Bx_T", "ScalarX"),
            ("By", "B0_By_T", "ScalarY"),
            ("Bz", "B0_Bz_T", "ScalarZ"),
        ]:
            try:
                raw = eval_at_point(fields, soln, lambda co=scal_op: (
                    fields.EnterQty("B"),
                    fields.CalcOp(co),
                    fields.EnterPoint(POINT_NAME),
                ))
                val = _extract_value(raw)
                log(f, "  %s = %s (raw: %s)" % (key, val, raw))
                if val is not None:
                    results[key] = val
            except Exception as exc:
                log(f, "  %s: %s" % (key, str(exc)[:150]))

        # ---- Write CSV ----
        a_mm = _extract_mm(var_values.get("a", ""))
        g_mm = _extract_mm(var_values.get("g", ""))
        T_mm = _extract_mm(var_values.get("T", ""))

        csv_cols = [
            "experiment", "layer", "T_mm", "a_mm", "g_mm",
            "B0_T", "B0_Bx_T", "B0_By_T", "B0_Bz_T",
        ]
        csv_row = {
            "experiment": "fixedT10_g02_B0",
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
