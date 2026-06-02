# -*- coding: utf-8 -*-
"""
create_B0_reference_model.py
=============================
Creates a B0 (no-shield) reference model by copying the external-field project
and suppressing the ferrite cylinders (material -> vacuum).

The external coils (Torus2, Torus3), currents, Box1, and center point are
preserved exactly. This ensures B0 and Bcenter are measured under identical
excitation for valid SF calculation.

Run after setup_external_field_complete.py has successfully validated.
"""

import os
import shutil
import time
import traceback

# ---------- user settings ----------
PROJECT_SRC = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
PROJECT_DST = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_B0.aedt"
LOG_PATH    = r"D:\ferrite\aaaaaaaaximukeji\round2_working\create_B0_reference_model.log"

ANALYZE     = False   # set True to auto-run Setup1 after creating B0 model
# --------------------------------

# Ferrite cylinders to suppress (set to vacuum instead of ferrite)
FERRITE_CYLINDERS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

# Also need to handle the internal coil (Torus1) - keep it as is, or suppress?
# The internal coil is for H-field generation inside the shield.
# For B0 measurement, we want NO shield but KEEP the external coils.
# The internal coil Torus1 should probably be suppressed too for clean SF.
# But the user's document says "保留同样电流" for external coils only...
# Let's keep Torus1 as-is for now and let the user decide.
# Set to True to also suppress the internal driving coil.
SUPPRESS_INTERNAL_COIL = False


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
    fp.flush()


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "create_B0_reference_model  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Source (with shield):  %s" % PROJECT_SRC)
        log(f, "Dest   (no shield):    %s" % PROJECT_DST)

        # ---- 0. copy project ----
        if os.path.exists(PROJECT_DST):
            os.remove(PROJECT_DST)
        shutil.copy2(PROJECT_SRC, PROJECT_DST)
        log(f, "Copied to %s" % PROJECT_DST)

        # ---- 1. open in AEDT ----
        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        try:
            oDesktop.OpenProject(PROJECT_DST)
            log(f, "OpenProject: OK")
        except Exception as exc:
            log(f, "OpenProject error (may already be open): %s" % exc)

        oProject = oDesktop.GetActiveProject()
        oDesign  = oProject.SetActiveDesign("Maxwell3DDesign1")
        oEditor  = oDesign.SetActiveEditor("3D Modeler")

        # ---- 2. suppress ferrite cylinders ----
        log(f, "")
        log(f, "=== Suppressing ferrite shields (material -> vacuum) ===")
        for cyl_name in FERRITE_CYLINDERS:
            try:
                oEditor.ChangeProperty([
                    "NAME:AllTabs",
                    ["NAME:Geometry3DAttributeTab",
                     ["NAME:PropServers", cyl_name],
                     ["NAME:ChangedProps",
                      ["NAME:Material", "Value:=", '"vacuum"'],
                      ["NAME:Solve Inside", "Value:=", True]]]
                ])
                log(f, "  %s -> vacuum : OK" % cyl_name)
            except Exception as exc:
                log(f, "  %s -> vacuum : FAILED (%s)" % (cyl_name, exc))

        # ---- 3. optionally suppress internal coil ----
        if SUPPRESS_INTERNAL_COIL:
            log(f, "")
            log(f, "=== Suppressing internal coil Torus1 ===")
            try:
                oEditor.ChangeProperty([
                    "NAME:AllTabs",
                    ["NAME:Geometry3DAttributeTab",
                     ["NAME:PropServers", "Torus1"],
                     ["NAME:ChangedProps",
                      ["NAME:Material", "Value:=", '"vacuum"'],
                      ["NAME:Solve Inside", "Value:=", True]]]
                ])
                log(f, "  Torus1 -> vacuum : OK")
            except Exception as exc:
                log(f, "  Torus1 -> vacuum : FAILED (%s)" % exc)

        # ---- 4. verify external coils are intact ----
        log(f, "")
        log(f, "=== Verification ===")
        for obj_name in ["Torus2", "Torus3", "Box1", "BcenterPoint_0_0_0"]:
            try:
                oEditor.GetObjectByName(obj_name)
                log(f, "  %s: present" % obj_name)
            except Exception:
                log(f, "  %s: MISSING!" % obj_name)

        for mat_obj in ["Torus2", "Torus3"]:
            try:
                mat = oEditor.GetPropertyValue("Geometry3DAttributeTab", mat_obj, "Material")
                log(f, "  %s material = %s" % (mat_obj, mat))
            except Exception:
                log(f, "  %s material: could not read" % mat_obj)

        # ---- 5. validate ----
        log(f, "")
        log(f, "=== Validation ===")
        try:
            result = oDesign.ValidateDesign()
            log(f, "  ValidateDesign: %s" % str(result))
        except Exception as exc:
            log(f, "  ValidateDesign: FAILED (%s)" % exc)

        # ---- 6. save ----
        log(f, "")
        try:
            oProject.Save()
            log(f, "Saved: %s" % PROJECT_DST)
        except Exception as exc:
            log(f, "Save: FAILED (%s)" % exc)

        # ---- 7. optionally analyze ----
        if ANALYZE:
            log(f, "")
            log(f, "=== Analysis ===")
            try:
                oDesign.AnalyzeAll()
                log(f, "  AnalyzeAll: OK")
            except Exception as exc:
                log(f, "  AnalyzeAll: FAILED (%s)" % exc)

        log(f, "")
        log(f, "Done.  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
