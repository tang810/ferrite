# -*- coding: utf-8 -*-
"""
Minimal AEDT diagnostic: copy the validated baseline and solve Setup1 without
adding hybrid geometry. Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/run_baseline_setup1_diagnostic.py
"""

import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
SOURCE_PROJECT = os.path.join(
    BASE_DIR, "round2_working", "manufacturable_thin",
    "C2_N4_t015_g008_shield.aedt")
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "baseline_setup1_diagnostic")
TARGET_PROJECT = os.path.join(OUT_DIR, "C2_N4_t015_g008_shield_diagnostic.aedt")
LOG_PATH = os.path.join(OUT_DIR, "run_baseline_setup1_diagnostic.log")
DESIGN_NAME = "Maxwell3DDesign1"


def log(fp, msg):
    try:
        text = unicode(msg)
    except Exception:
        text = str(msg)
    try:
        fp.write(text.encode("utf-8", "replace") + "\n")
    except Exception:
        fp.write(str(text).replace("\x00", "?") + "\n")
    fp.flush()


def prepare_destination(fp):
    lock_path = TARGET_PROJECT + ".lock"
    results_path = TARGET_PROJECT + "results"
    if os.path.exists(lock_path):
        log(fp, "TARGET PROJECT LOCK EXISTS: " + lock_path)
        log(fp, "Close the diagnostic project before rerunning.")
        return False
    if os.path.exists(TARGET_PROJECT):
        os.remove(TARGET_PROJECT)
        log(fp, "removed stale target project -> " + TARGET_PROJECT)
    if os.path.isdir(results_path):
        abs_out = os.path.abspath(OUT_DIR)
        abs_results = os.path.abspath(results_path)
        if not abs_results.startswith(abs_out + os.sep):
            log(fp, "REFUSING TO REMOVE RESULTS OUTSIDE OUT_DIR: " + abs_results)
            return False
        shutil.rmtree(results_path)
        log(fp, "removed stale target results -> " + results_path)
    return True


def run():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "run_baseline_setup1_diagnostic " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "PURPOSE: solve unmodified baseline Setup1 without hybrid geometry")
        if not os.path.exists(SOURCE_PROJECT):
            log(fp, "SOURCE PROJECT MISSING: " + SOURCE_PROJECT)
            return
        if os.path.exists(SOURCE_PROJECT + ".lock"):
            log(fp, "SOURCE PROJECT LOCK EXISTS: " + SOURCE_PROJECT + ".lock")
            log(fp, "Close the baseline project before rerunning.")
            return
        if not prepare_destination(fp):
            return
        shutil.copy2(SOURCE_PROJECT, TARGET_PROJECT)
        log(fp, "copied baseline -> " + TARGET_PROJECT)

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()
        oDesktop.OpenProject(TARGET_PROJECT)
        log(fp, "OpenProject: OK")
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign(DESIGN_NAME)
        log(fp, "SetActiveDesign: OK -> " + DESIGN_NAME)
        log(fp, "ValidateDesign: START")
        result = oDesign.ValidateDesign()
        log(fp, "ValidateDesign: RETURN -> " + str(result))
        solve_start = time.time()
        log(fp, "Analyze Setup1: START " + time.strftime("%Y-%m-%d %H:%M:%S"))
        oDesign.Analyze("Setup1")
        log(fp, "Analyze Setup1: RETURN elapsed_s=" + str(time.time() - solve_start))
        oProject.Save()
        log(fp, "Save project: OK")
        oDesktop.CloseProject(oProject.GetName())
        log(fp, "Close project: OK")
    except Exception:
        log(fp, "DIAGNOSTIC FAILED")
        log(fp, traceback.format_exc())
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
