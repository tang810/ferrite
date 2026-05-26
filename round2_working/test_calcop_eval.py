# -*- coding: utf-8 -*-
"""
Test CalcOp("Eval") as an alternative to ClcEval.
Also test GetTopEntryValue with and without soln args after Eval.
"""

import os
import time

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
LOG_PATH    = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\test_calcop_eval.log"
POINT_NAME  = "BcenterPoint_0_0_0"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def try_it(fp, label, fn):
    try:
        result = fn()
        log(fp, "OK %s: %s" % (label, str(result)[:500]))
        return result
    except Exception as exc:
        log(fp, "FAIL %s: %s" % (label, str(exc)[:300]))
        return None


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "test_calcop_eval  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

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
        soln     = "Setup1 : LastAdaptive"

        # ---- Test 1: CalcOp("Eval") with Mag_B named expression ----
        log(f, "")
        log(f, "=== Test 1: CalcOp('Eval') with Mag_B ===")

        for order_label, build_fn in [
            ("point_then_Mag_B", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.CopyNamedExprToStack("Mag_B"),
            )),
            ("Mag_B_then_point", lambda: (
                fields.CopyNamedExprToStack("Mag_B"),
                fields.EnterPoint(POINT_NAME),
            )),
            ("point_then_B_Mag", lambda: (
                fields.EnterPoint(POINT_NAME),
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
            )),
            ("B_Mag_then_point", lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.EnterPoint(POINT_NAME),
            )),
        ]:
            log(f, "")
            log(f, "--- %s ---" % order_label)

            # Try Eval + GetTopEntryValue with different args
            try:
                fields.CalcStack("clear")
                build_fn()
                fields.CalcOp("Eval")
                # Now try GetTopEntryValue with various args
                for gtev_label, gtev_fn in [
                    ("GetTopEntryValue(soln, [])", lambda: fields.GetTopEntryValue(soln, [])),
                    ("GetTopEntryValue(soln)", lambda: fields.GetTopEntryValue(soln)),
                    ("GetTopEntryValue()", lambda: fields.GetTopEntryValue()),
                ]:
                    try_it(f, gtev_label, gtev_fn)
            except Exception as exc:
                log(f, "  Build+Eval failed: %s" % str(exc)[:200])

        # ---- Test 2: Try CalcOp with numeric output ----
        log(f, "")
        log(f, "=== Test 2: CalcOp('Value') then Eval ===")
        for order_label, build_fn in [
            ("B_Mag_Value_point", lambda: (
                fields.EnterQty("B"),
                fields.CalcOp("Mag"),
                fields.CalcOp("Value"),
                fields.EnterPoint(POINT_NAME),
            )),
        ]:
            log(f, "--- %s ---" % order_label)
            try:
                fields.CalcStack("clear")
                build_fn()
                fields.CalcOp("Eval")
                for gtev_label, gtev_fn in [
                    ("GetTopEntryValue(soln, [])", lambda: fields.GetTopEntryValue(soln, [])),
                    ("GetTopEntryValue(soln)", lambda: fields.GetTopEntryValue(soln)),
                    ("GetTopEntryValue()", lambda: fields.GetTopEntryValue()),
                ]:
                    try_it(f, gtev_label, gtev_fn)
            except Exception as exc:
                log(f, "  Build+Eval failed: %s" % str(exc)[:200])

        # ---- Test 3: Direct GetTopEntryValue after Eval (no soln) ----
        log(f, "")
        log(f, "=== Test 3: GetTopEntryValue without soln ===")
        for i in range(4):
            try:
                fields.CalcStack("clear")
                fields.CopyNamedExprToStack("Mag_B")
                fields.EnterPoint(POINT_NAME)
                fields.CalcOp("Eval")
                # Try different args
                log(f, "  Trying GetTopEntryValue with arg %d..." % i)
                if i == 0:
                    val = fields.GetTopEntryValue()
                elif i == 1:
                    val = fields.GetTopEntryValue(soln)
                elif i == 2:
                    val = fields.GetTopEntryValue(soln, [])
                else:
                    val = fields.GetTopEntryValue(soln, [], "Fields")
                log(f, "  GetTopEntryValue[%d] = %s" % (i, val))
            except Exception as exc:
                log(f, "  Attempt %d: %s" % (i, str(exc)[:200]))

        # ---- Test 4: Try other CalcOp operations ----
        log(f, "")
        log(f, "=== Test 4: Alternative CalcOp operations ===")
        for op_name in ["Value", "Eval", "Evaluate", "Smooth", "RL", "EnterSurf"]:
            try:
                fields.CalcStack("clear")
                fields.EnterQty("B")
                fields.CalcOp("Mag")
                fields.EnterPoint(POINT_NAME)
                fields.CalcOp(op_name)
                log(f, "  CalcOp('%s'): OK" % op_name)
                try:
                    val = fields.GetTopEntryValue(soln, [])
                    log(f, "    GetTopEntryValue = %s" % val)
                except Exception:
                    pass
            except Exception as exc:
                log(f, "  CalcOp('%s'): %s" % (op_name, str(exc)[:150]))

        # ---- Test 5: Check what's on the stack ----
        log(f, "")
        log(f, "=== Test 5: Stack inspection ===")
        try:
            fields.CalcStack("clear")
            fields.EnterQty("B")
            fields.CalcOp("Mag")
            fields.EnterPoint(POINT_NAME)
            # Try reading stack info
            try_it(f, "CalcStack('read')", lambda: fields.CalcStack("read"))
            try_it(f, "CalcStack('check')", lambda: fields.CalcStack("check"))
            try_it(f, "CalcStack('show')", lambda: fields.CalcStack("show"))
            try_it(f, "CalcStack('top')", lambda: fields.CalcStack("top"))
        except Exception as exc:
            log(f, "  Stack ops: %s" % str(exc)[:200])

        # ---- Test 6: CalcWrite then CalcRead approach ----
        log(f, "")
        log(f, "=== Test 6: CalcWrite/CalcRead ===")
        expr_file = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\_expr.calc"
        try:
            fields.CalcStack("clear")
            fields.EnterQty("B")
            fields.CalcOp("Mag")
            fields.CalcWrite(expr_file, [])
            log(f, "  CalcWrite: OK -> %s" % expr_file)
        except Exception as exc:
            log(f, "  CalcWrite: %s" % str(exc)[:200])

        log(f, "")
        log(f, "Done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
