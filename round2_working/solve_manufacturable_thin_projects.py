# -*- coding: utf-8 -*-
"""
solve_manufacturable_thin_projects.py
====================================
Solve Setup1 for generated manufacturable-thin continuous-shell projects.

Run inside AEDT, or from command line with ansysedt -RunScriptAndExit.
"""

import csv
import os
import time
import traceback


BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
PARAM_CSV = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin_params.csv")
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
LOG_PATH = os.path.join(PROJECT_DIR, "solve_manufacturable_thin_projects.log")

MAX_PRIORITY = 1
# Leave empty to run all priority cases. Fill with case IDs to run a small batch.
CASE_ID_FILTER = []
SOLVE_B0_FOR_EACH_CASE = False


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def read_cases():
    with open(PARAM_CSV, "r") as f:
        rows = list(csv.DictReader(f))
    cases = []
    for row in rows:
        if row["model_type"] != "continuous_shell":
            continue
        if int(float(row["priority"])) > MAX_PRIORITY:
            continue
        if int(float(row["layer"])) > 4:
            continue
        cases.append(row)
    return cases


def solve_project(fp, oDesktop, project_path):
    log(fp, "")
    log(fp, "Project: %s" % project_path)
    if not os.path.exists(project_path):
        log(fp, "  MISSING")
        return

    try:
        oDesktop.OpenProject(project_path)
        log(fp, "  OpenProject: OK")
    except Exception:
        log(fp, "  OpenProject: FAILED")
        log(fp, traceback.format_exc())
        return

    try:
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
    except Exception:
        log(fp, "  SetActiveDesign: FAILED")
        log(fp, traceback.format_exc())
        return

    for vn in ["a", "g", "T"]:
        try:
            log(fp, "  %s = %s" % (vn, oDesign.GetVariableValue(vn)))
        except Exception:
            pass

    start = time.time()
    try:
        oDesign.Solve(["NAME:Selections", "Selections:=", "Setup1"])
        log(fp, "  Solve Setup1: OK")
    except Exception:
        log(fp, "  Solve failed, trying Analyze('Setup1')")
        try:
            oDesign.Analyze("Setup1")
            log(fp, "  Analyze Setup1: OK")
        except Exception:
            log(fp, "  Analyze Setup1: FAILED")
            log(fp, traceback.format_exc())

    try:
        oProject.Save()
        log(fp, "  Save: OK")
    except Exception:
        log(fp, "  Save: FAILED")

    try:
        name = oProject.GetName()
        oDesktop.CloseProject(name)
        log(fp, "  CloseProject: OK")
    except Exception:
        log(fp, "  CloseProject: FAILED")

    log(fp, "  elapsed_s = %.1f" % (time.time() - start))


def run():
    with open(LOG_PATH, "w") as fp:
        log(fp, "solve_manufacturable_thin_projects %s" % time.strftime("%Y-%m-%d %H:%M:%S"))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case in read_cases():
            case_id = case["case_id"]
            if CASE_ID_FILTER and case_id not in CASE_ID_FILTER:
                continue
            for suffix in ["shield", "B0"]:
                if suffix == "B0" and not SOLVE_B0_FOR_EACH_CASE and case_id != "C1_N1_t008":
                    log(fp, "Skip %s_B0; reuse C1_N1_t008_B0 as common no-shield reference" % case_id)
                    continue
                project_path = os.path.join(PROJECT_DIR, "%s_%s.aedt" % (case_id, suffix))
                solve_project(fp, oDesktop, project_path)

        log(fp, "")
        log(fp, "Done %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
