# -*- coding: utf-8 -*-
"""
solve_B0_setup1.py
==================
Solve Setup1 on the B0 (no-shield) reference model.
"""

import time
import traceback

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_B0.aedt"
LOG_PATH     = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\solve_B0_setup1.log"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "solve_B0_setup1  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Project: %s" % PROJECT_PATH)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        oProject = None
        for attempt in range(3):
            try:
                oDesktop.OpenProject(PROJECT_PATH)
                log(f, "OpenProject: OK (attempt %d)" % (attempt+1))
                oProject = oDesktop.GetActiveProject()
                if oProject is not None:
                    break
            except Exception as exc:
                log(f, "OpenProject attempt %d: %s" % (attempt+1, exc))
                time.sleep(2)

        if oProject is None:
            log(f, "FATAL: could not open project after 3 attempts")
            return
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")

        log(f, "Variables:")
        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            try:
                log(f, "  %s = %s" % (vn, oDesign.GetVariableValue(vn)))
            except Exception:
                pass

        log(f, "")
        log(f, "Starting Setup1 solve at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            oDesign.Solve(["NAME:Selections", "Selections:=", "Setup1"])
            log(f, "Setup1 solve: OK at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception:
            log(f, "Setup1 solve via Solve() failed, trying Analyze()...")
            try:
                oDesign.Analyze("Setup1")
                log(f, "Setup1 Analyze: OK at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
            except Exception as exc2:
                log(f, "Setup1 solve: FAILED")
                log(f, traceback.format_exc())

        log(f, "Done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            oProject.Save()
            log(f, "Saved.")
        except Exception:
            pass


run()
