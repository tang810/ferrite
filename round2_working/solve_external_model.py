"""
solve_external_model.py
=======================
Analyze Setup1 on the external-field model.
Saves progress to solve_external_model.log.
"""
import os
import time
import traceback

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_external.aedt"
LOG_PATH     = r"D:\ferrite\aaaaaaaaximukeji\round2_working\solve_external_model.log"


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "solve_external_model  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Project: %s" % PROJECT_PATH)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_PATH)
            log(f, "OpenProject: OK")
        except Exception as exc:
            log(f, "OpenProject error (may be open): %s" % exc)

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")

        log(f, "Project: %s" % oProject.GetName())
        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            try:
                log(f, "  %s = %s" % (vn, oDesign.GetVariableValue(vn)))
            except Exception:
                pass

        log(f, "")
        log(f, "Starting AnalyzeAll at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "This may take 10-60 minutes depending on mesh complexity...")

        try:
            oDesign.AnalyzeAll()
            log(f, "AnalyzeAll: OK at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as exc:
            log(f, "AnalyzeAll: FAILED")
            log(f, traceback.format_exc())

        log(f, "Done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        try:
            oProject.Save()
            log(f, "Project saved.")
        except Exception:
            pass


run()
