# -*- coding: utf-8 -*-
"""
run_manufacturable_thin_continuous.py
=====================================
Prepare manufacturable thin-ferrite continuous-shell AEDT projects.

This script is meant to be run inside Ansys Electronics Desktop:

    Tools -> Run Script -> run_manufacturable_thin_continuous.py

It creates external-field shield models for the priority-1 continuous-shell
cases and a no-shield B0 reference model. It intentionally does not create
the segmented prototype geometry; that is a second-stage correction after the
continuous-shell screen is evaluated.

Set ANALYZE = True to run Setup1 for every generated project.
"""

import csv
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PARAM_CSV = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin_params.csv")
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
LOG_PATH = os.path.join(OUT_DIR, "run_manufacturable_thin_continuous.log")

ANALYZE = False
MAX_PRIORITY = 1

DESIGN_NAME = "Maxwell3DDesign1"

SOURCE_PROJECT_BY_LAYER = {
    1: os.path.join(BASE_DIR, "Project100_1ceng.aedt"),
    2: os.path.join(BASE_DIR, "Project100_2ceng.aedt"),
    3: os.path.join(BASE_DIR, "Project100_3ceng.aedt"),
    4: os.path.join(BASE_DIR, "Project100_4ceng.aedt"),
}

FERRITE_OBJECTS_BY_LAYER = {
    1: ["Cylinder2"],
    2: ["Cylinder2", "Cylinder4"],
    3: ["Cylinder2", "Cylinder4", "Cylinder6"],
    4: ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"],
}

TORUS2_CENTER = ("150mm", "0mm", "0mm")
TORUS3_CENTER = ("-150mm", "0mm", "0mm")
TORUS_AXIS = "X"
TORUS_MAJOR_R = "300mm"
TORUS_MINOR_R = "2mm"


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        out = fn()
        log(fp, "%s: OK%s" % (label, (" -> " + str(out)) if out is not None else ""))
        return out
    except Exception:
        log(fp, "%s: FAILED" % label)
        log(fp, traceback.format_exc())
        return None


def read_cases():
    with open(PARAM_CSV, "r") as f:
        rows = list(csv.DictReader(f))

    cases = []
    for row in rows:
        if row["model_type"] != "continuous_shell":
            continue
        if int(float(row["priority"])) > MAX_PRIORITY:
            continue
        layer = int(float(row["layer"]))
        if layer not in SOURCE_PROJECT_BY_LAYER:
            continue
        cases.append(row)
    return cases


def change_local_variables(oDesign, row):
    layer = int(float(row["layer"]))
    a = float(row["a_mm"])
    g = float(row["g_mm"])
    t_space = float(row["T_mm"])

    props = [
        ["NAME:a", "Value:=", "%.12gmm" % a],
        ["NAME:g", "Value:=", "%.12gmm" % g],
        ["NAME:T", "Value:=", "%.12gmm" % t_space],
    ]
    oDesign.ChangeProperty([
        "NAME:AllTabs",
        ["NAME:LocalVariableTab",
         ["NAME:PropServers", "LocalVariables"],
         ["NAME:ChangedProps"] + props],
    ])


def cleanup_external_objects(oEditor, oBoundary):
    for bnd in ["Iext_plus", "Iext_minus", "Current1", "Current2"]:
        try:
            oBoundary.DeleteBoundaries([bnd])
        except Exception:
            pass

    stale_objects = [
        "Torus2_Section1", "Torus3_Section1",
        "Torus2_Section1_Separate1", "Torus3_Section1_Separate1",
        "Iext_plus_sheet", "Iext_minus_sheet",
        "Iext_plus_sheet_1", "Iext_minus_sheet_1",
    ]
    for obj in stale_objects:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", obj])
        except Exception:
            pass


def enlarge_airbox_if_needed(fp, oEditor):
    props = {}
    for prop in ["X Size", "Y Size", "Z Size"]:
        try:
            props[prop] = oEditor.GetPropertyValue("Geometry3DCmdTab", "Box1", prop)
            log(fp, "  Box1 %s = %s" % (prop, props[prop]))
        except Exception:
            props[prop] = ""

    def parse_mm(text):
        try:
            return float(str(text).replace("mm", "").strip())
        except Exception:
            return None

    def set_box_prop(prop, val_mm):
        oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DCmdTab",
             ["NAME:PropServers", "Box1:CreateBox:1"],
             ["NAME:ChangedProps", ["NAME:" + prop, "Value:=", "%smm" % val_mm]]],
        ])

    for prop, needed in [("X Size", 320.0), ("Y Size", 620.0), ("Z Size", 620.0)]:
        cur = parse_mm(props.get(prop, ""))
        if cur is not None and cur < needed:
            set_box_prop(prop, needed)
            log(fp, "  enlarged Box1 %s to %smm" % (prop, needed))


def create_or_repair_torus(oEditor, name, center):
    existing = []
    try:
        existing = list(oEditor.GetObjectsInGroup("Solids"))
    except Exception:
        pass

    if name not in existing:
        oEditor.CreateTorus(
            [
                "NAME:TorusParameters",
                "IsCovered:=", True,
                "XCenter:=", center[0],
                "YCenter:=", center[1],
                "ZCenter:=", center[2],
                "MajorRadius:=", TORUS_MAJOR_R,
                "MinorRadius:=", TORUS_MINOR_R,
                "WhichAxis:=", TORUS_AXIS,
                "NumSegments:=", "0",
            ],
            [
                "NAME:Attributes",
                "Name:=", name,
                "Flags:=", "",
                "Color:=", "(255 0 0)",
                "Transparency:=", 0,
                "PartCoordinateSystem:=", "Global",
                "UDMId:=", "",
                "MaterialValue:=", '"copper"',
                "SurfaceMaterialValue:=", '""',
                "SolveInside:=", True,
                "ShellElement:=", False,
                "ShellElementThickness:=", "0mm",
                "IsMaterialEditable:=", True,
                "UseMaterialAppearance:=", False,
                "IsLightweight:=", False,
            ],
        )
    else:
        oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DAttributeTab",
             ["NAME:PropServers", name],
             ["NAME:ChangedProps",
              ["NAME:Material", "Value:=", '"copper"'],
              ["NAME:Solve Inside", "Value:=", True]]],
        ])


def setup_external_field(fp, oDesign, oEditor, oBoundary):
    cleanup_external_objects(oEditor, oBoundary)
    enlarge_airbox_if_needed(fp, oEditor)
    create_or_repair_torus(oEditor, "Torus2", TORUS2_CENTER)
    create_or_repair_torus(oEditor, "Torus3", TORUS3_CENTER)

    def section_torus(torus_name):
        return oEditor.Section(
            ["NAME:Selections", "Selections:=", torus_name, "NewPartsModelFlag:=", "Model"],
            ["NAME:SectionToParameters", "CreateNewObjects:=", True, "SectionPlane:=", "ZX"],
        )

    safe(fp, "section Torus2", lambda: section_torus("Torus2"))
    safe(fp, "section Torus3", lambda: section_torus("Torus3"))

    def separate_section(section_name):
        return oEditor.SeparateBody(
            ["NAME:Selections", "Selections:=", section_name, "NewPartsModelFlag:=", "Model"]
        )

    safe(fp, "separate Torus2_Section1", lambda: separate_section("Torus2_Section1"))
    safe(fp, "separate Torus3_Section1", lambda: separate_section("Torus3_Section1"))

    for sep_name in ["Torus2_Section1_Separate1", "Torus3_Section1_Separate1"]:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", sep_name])
        except Exception:
            pass

    def assign_current(name, section, point_out):
        return oBoundary.AssignCurrent([
            "NAME:" + name,
            "Objects:=", [section],
            "Current:=", "1A",
            "IsSolid:=", True,
            "Point out of terminal:=", point_out,
        ])

    safe(fp, "assign Iext_plus", lambda: assign_current("Iext_plus", "Torus2_Section1", False))
    safe(fp, "assign Iext_minus", lambda: assign_current("Iext_minus", "Torus3_Section1", True))

    try:
        oEditor.GetObjectByName("BcenterPoint_0_0_0")
    except Exception:
        safe(fp, "create BcenterPoint_0_0_0", lambda: oEditor.CreatePoint(
            ["NAME:PointParameters", "X:=", "0mm", "Y:=", "0mm", "Z:=", "0mm", "PointType:=", "NonModel"],
            ["NAME:Attributes", "Name:=", "BcenterPoint_0_0_0", "Color:=", "(255 255 0)", "PartCoordinateSystem:=", "Global"],
        ))

    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())


def set_ferrite_to_vacuum(fp, oEditor, layer):
    for obj in FERRITE_OBJECTS_BY_LAYER.get(layer, []):
        safe(fp, "%s -> vacuum" % obj, lambda o=obj: oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DAttributeTab",
             ["NAME:PropServers", o],
             ["NAME:ChangedProps",
              ["NAME:Material", "Value:=", '"vacuum"'],
              ["NAME:Solve Inside", "Value:=", True]]],
        ]))


def solve_if_requested(fp, oDesign):
    if not ANALYZE:
        return
    try:
        oDesign.Solve(["NAME:Selections", "Selections:=", "Setup1"])
        log(fp, "Solve Setup1: OK")
    except Exception:
        log(fp, "Solve Setup1 via Solve failed, trying Analyze")
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))


def close_project(fp, oDesktop, oProject, label):
    try:
        name = oProject.GetName()
        oDesktop.CloseProject(name)
        log(fp, "close %s project: OK (%s)" % (label, name))
    except Exception:
        log(fp, "close %s project: FAILED" % label)
        log(fp, traceback.format_exc())


def prepare_case(fp, oDesktop, row):
    layer = int(float(row["layer"]))
    case_id = row["case_id"]
    src = SOURCE_PROJECT_BY_LAYER[layer]
    shield_dst = os.path.join(OUT_DIR, "%s_shield.aedt" % case_id)
    b0_dst = os.path.join(OUT_DIR, "%s_B0.aedt" % case_id)

    for dst in [shield_dst, b0_dst]:
        if os.path.exists(dst):
            try:
                os.remove(dst)
            except Exception:
                pass

    shutil.copy2(src, shield_dst)
    log(fp, "")
    log(fp, "=" * 70)
    log(fp, "Preparing %s from %s" % (case_id, src))

    safe(fp, "open shield project", lambda: oDesktop.OpenProject(shield_dst))
    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    oBoundary = oDesign.GetModule("BoundarySetup")

    safe(fp, "set variables", lambda: change_local_variables(oDesign, row))
    setup_external_field(fp, oDesign, oEditor, oBoundary)
    solve_if_requested(fp, oDesign)
    safe(fp, "save shield", lambda: oProject.Save())
    close_project(fp, oDesktop, oProject, "shield")

    shutil.copy2(shield_dst, b0_dst)
    safe(fp, "open B0 project", lambda: oDesktop.OpenProject(b0_dst))
    oProjectB0 = oDesktop.GetActiveProject()
    oDesignB0 = oProjectB0.SetActiveDesign(DESIGN_NAME)
    oEditorB0 = oDesignB0.SetActiveEditor("3D Modeler")
    set_ferrite_to_vacuum(fp, oEditorB0, layer)
    solve_if_requested(fp, oDesignB0)
    safe(fp, "save B0", lambda: oProjectB0.Save())
    close_project(fp, oDesktop, oProjectB0, "B0")


def run():
    ensure_dir(OUT_DIR)
    cases = read_cases()

    with open(LOG_PATH, "w") as fp:
        log(fp, "run_manufacturable_thin_continuous %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "ANALYZE = %s" % ANALYZE)
        log(fp, "Cases: %s" % ", ".join([c["case_id"] for c in cases]))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for row in cases:
            try:
                prepare_case(fp, oDesktop, row)
            except Exception:
                log(fp, "CASE FAILED: %s" % row.get("case_id", "unknown"))
                log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "Done %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
