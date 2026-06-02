# -*- coding: utf-8 -*-
"""
Run axial capped-end AEDT experiments for the four-layer ferrite shield.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/run_axial_capped_end_experiment.py

Cases:
  1. ZCAP_C2_N4_top_cap
     One circular cap on the +Z end; the -Z end remains open.
  2. ZCAP_C2_N4_two_caps_no_hole
     Circular caps on both ends. This is the ideal capped reference.
  3. ZCAP_C2_N4_two_caps_bottom_hole_r2
     +Z end is fully capped; -Z end is capped with a center hole
     of radius 2 mm for magnetometer wiring.

The script copies the already z-directed baseline project
C2_N4_t015_g008_z_shield.aedt, adds cap geometry, solves Setup1,
exports center-field components, computes SFz with the validated B0_z,
and computes IntH2 over ferrite plus cap objects.

This is an IronPython 2.7/AEDT script. Keep syntax conservative.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "axial_capped_end")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw", "axial_capped_end_exports.csv")
LOG_PATH = os.path.join(OUT_DIR, "run_axial_capped_end_experiment.log")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

BASE_PROJECT = os.path.join(PROJECT_DIR, "C2_N4_t015_g008_z_shield.aedt")
BASE_CASE_ID = "C2_N4_t015_g008_z"
B0_BZ_T = 1.25663644033e-06

RIN_MM = 100.0
LENGTH_MM = 200.0
FERRITE_TSPACE_MM = 0.84
OUTER_R_MM = RIN_MM + FERRITE_TSPACE_MM
CAP_T_MM = 0.15
WIRE_HOLE_R_MM = 2.0
MESH_DIVISOR_CAP = 3.0

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

ANALYZE = True

CASES = [
    {
        "case_id": "ZCAP_C2_N4_top_cap",
        "top_cap": True,
        "bottom_cap": False,
        "bottom_hole_r_mm": 0.0,
        "notes": "one-end-capped; +Z cap only; -Z open",
    },
    {
        "case_id": "ZCAP_C2_N4_two_caps_no_hole",
        "top_cap": True,
        "bottom_cap": True,
        "bottom_hole_r_mm": 0.0,
        "notes": "ideal two-end-capped reference; no wiring hole",
    },
    {
        "case_id": "ZCAP_C2_N4_two_caps_bottom_hole_r2",
        "top_cap": True,
        "bottom_cap": True,
        "bottom_hole_r_mm": WIRE_HOLE_R_MM,
        "notes": "two-end-capped with bottom center wiring hole, r=2 mm",
    },
]

FIELDNAMES = [
    "case_id", "base_case", "field_dir",
    "outer_radius_mm", "cap_thickness_mm",
    "top_cap", "bottom_cap", "bottom_hole_r_mm",
    "B0_Bz_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
    "Bcenter_Mag_T", "SFz", "LeakageRatioz",
    "IntH2_total_with_caps", "IntH2_ferrite_only", "IntH2_caps",
    "source_project", "status", "notes",
]


def ensure_dirs():
    for path in [OUT_DIR, os.path.dirname(OUT_CSV)]:
        if not os.path.isdir(path):
            os.makedirs(path)


def log(fp, msg):
    try:
        text = unicode(msg)
    except Exception:
        try:
            text = str(msg)
        except Exception:
            text = "<unprintable>"
    try:
        fp.write(text.encode("utf-8", "replace") + "\n")
    except Exception:
        fp.write(str(text).replace("\x00", "?") + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        value = fn()
        s = str(value) if value is not None else ""
        log(fp, label + ": OK" + (" -> " + s if s else ""))
        return True if value is None else value
    except Exception:
        log(fp, label + ": FAILED")
        log(fp, traceback.format_exc())
        return None


def append_csv_row(path, fieldnames, row):
    exists = os.path.exists(path)
    fp = open(path, "ab" if exists else "wb")
    try:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        out = {}
        for name in fieldnames:
            out[name] = row.get(name, "")
        writer.writerow(out)
    finally:
        fp.close()


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        if not raw:
            return ""
        raw = raw[0]
    try:
        return float(raw)
    except Exception:
        return str(raw)


def get_material_from_object(fp, oEditor, obj_name):
    for prop in ["Material", "MaterialValue"]:
        try:
            value = oEditor.GetPropertyValue("Geometry3DAttributeTab", obj_name, prop)
            if value:
                value = str(value).replace('"', "")
                log(fp, "cap material from " + obj_name + ": " + value)
                return value
        except Exception:
            pass
    log(fp, "cap material fallback: ferrite")
    return "ferrite"


def delete_if_exists(oEditor, names):
    for name in names:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", name])
        except Exception:
            pass


def create_cap(fp, oEditor, cap_name, z_start_mm, radius_mm, thickness_mm, material_name):
    delete_if_exists(oEditor, [cap_name])
    safe(fp, "create cap " + cap_name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", str(z_start_mm) + "mm",
              "Radius:=", str(radius_mm) + "mm",
              "Height:=", str(thickness_mm) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", cap_name,
              "Flags:=", "",
              "Color:=", "(70 120 210)",
              "Transparency:=", 0,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"' + material_name + '"',
              "SolveInside:=", True,
              "ShellElement:=", False,
              "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              "UseMaterialAppearance:=", False,
              "IsLightweight:=", False,
              "IsAlwaysHidden:=", False,
              ]))
    return cap_name


def cut_center_hole(fp, oEditor, cap_name, hole_radius_mm, z_start_mm, thickness_mm):
    if hole_radius_mm <= 0:
        return
    tool_name = cap_name + "_hole_tool"
    delete_if_exists(oEditor, [tool_name])
    safe(fp, "create hole tool " + tool_name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", str(z_start_mm - 0.5) + "mm",
              "Radius:=", str(hole_radius_mm) + "mm",
              "Height:=", str(thickness_mm + 1.0) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", tool_name,
              "Flags:=", "",
              "Color:=", "(255 0 0)",
              "Transparency:=", 0.5,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"vacuum"',
              "SolveInside:=", False,
              ]))
    safe(fp, "subtract center hole from " + cap_name,
         lambda: oEditor.Subtract(
             ["NAME:Selections",
              "Blank Parts:=", cap_name,
              "Tool Parts:=", tool_name],
             ["NAME:SubtractParameters", "KeepOriginals:=", False]))


def add_caps(fp, oEditor, case_info, material_name):
    cap_objects = []
    z_top = LENGTH_MM / 2.0
    z_bottom = -LENGTH_MM / 2.0 - CAP_T_MM
    if case_info["top_cap"]:
        cap_objects.append(create_cap(fp, oEditor, "AxialCap_Top", z_top,
                                      OUTER_R_MM, CAP_T_MM, material_name))
    if case_info["bottom_cap"]:
        bottom = create_cap(fp, oEditor, "AxialCap_Bottom", z_bottom,
                            OUTER_R_MM, CAP_T_MM, material_name)
        cut_center_hole(fp, oEditor, bottom, case_info["bottom_hole_r_mm"],
                        z_bottom, CAP_T_MM)
        cap_objects.append(bottom)
    log(fp, "cap objects: " + str(cap_objects))
    return cap_objects


def assign_cap_mesh(fp, oDesign, cap_objects):
    if not cap_objects:
        return
    mesh = oDesign.GetModule("MeshSetup")
    max_len = CAP_T_MM / MESH_DIVISOR_CAP
    if max_len <= 0:
        max_len = 0.05
    try:
        mesh.DeleteMeshOperations(["Length_axial_caps"])
    except Exception:
        pass
    safe(fp, "assign cap mesh",
         lambda: mesh.AssignLengthOp([
             "NAME:Length_axial_caps",
             "RefineInside:=", True,
             "Objects:=", cap_objects,
             "RestrictElem:=", True,
             "NumMaxElem:=", "3000",
             "RestrictLength:=", True,
             "MaxLength:=", str(max_len) + "mm",
         ]))


def eval_b_component(fields, comp):
    op = {"Bx": "ScalarX", "By": "ScalarY", "Bz": "ScalarZ"}[comp]
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp(op)
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def compute_bmag(bx, by, bz):
    try:
        x = float(bx)
        y = float(by)
        z = float(bz)
        return math.sqrt(x * x + y * y + z * z)
    except Exception:
        return ""


def eval_h2_integral_over_objects(fields, objects):
    if not objects:
        return 0.0

    def comp_integral(comp):
        op = {"x": "ScalarX", "y": "ScalarY", "z": "ScalarZ"}[comp]
        fields.CalcStack("clear")
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.CalcOp("*")
        fields.EnterVol(",".join(objects))
        fields.CalcOp("Integrate")
        fields.ClcEval(SOLN, [])
        return extract_value(fields.GetTopEntryValue(SOLN, []))

    total = 0.0
    for comp in ["x", "y", "z"]:
        val = comp_integral(comp)
        try:
            total += float(val)
        except Exception:
            pass
    return total


def process_case(fp, oDesktop, case_info):
    case_id = case_info["case_id"]
    project_path = os.path.join(OUT_DIR, case_id + "_shield.aedt")

    log(fp, "")
    log(fp, "=" * 72)
    log(fp, "CASE " + case_id)

    if not os.path.exists(BASE_PROJECT):
        log(fp, "BASE PROJECT MISSING: " + BASE_PROJECT)
        return

    for path in [BASE_PROJECT, project_path]:
        lock_path = path + ".lock"
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    if os.path.exists(project_path):
        os.remove(project_path)
    shutil.copy2(BASE_PROJECT, project_path)
    log(fp, "copied baseline -> " + project_path)

    safe(fp, "OpenProject", lambda: oDesktop.OpenProject(project_path))
    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")

    cap_material = get_material_from_object(fp, oEditor, "Cylinder2")
    delete_if_exists(oEditor, ["AxialCap_Top", "AxialCap_Bottom",
                               "AxialCap_Bottom_hole_tool"])
    cap_objects = add_caps(fp, oEditor, case_info, cap_material)
    assign_cap_mesh(fp, oDesign, cap_objects)

    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    if ANALYZE:
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    fields = oDesign.GetModule("FieldsReporter")
    bx = safe(fp, "Bcenter_Bx", lambda: eval_b_component(fields, "Bx"))
    by = safe(fp, "Bcenter_By", lambda: eval_b_component(fields, "By"))
    bz = safe(fp, "Bcenter_Bz", lambda: eval_b_component(fields, "Bz"))
    bmag = compute_bmag(bx, by, bz)

    sfz = ""
    leakage = ""
    if bz != "" and bz is not None:
        try:
            sfz = abs(B0_BZ_T) / abs(float(bz))
            leakage = abs(float(bz)) / abs(B0_BZ_T)
        except Exception:
            pass

    int_ferrite = safe(fp, "IntH2 ferrite only",
                       lambda: eval_h2_integral_over_objects(fields, FERRITE_OBJECTS))
    int_caps = safe(fp, "IntH2 caps",
                    lambda: eval_h2_integral_over_objects(fields, cap_objects))
    int_total = safe(fp, "IntH2 ferrite plus caps",
                     lambda: eval_h2_integral_over_objects(fields, FERRITE_OBJECTS + cap_objects))

    status = "exported" if bz not in ["", None] and int_total not in ["", None] else "failed"
    out = {
        "case_id": case_id,
        "base_case": BASE_CASE_ID,
        "field_dir": "z",
        "outer_radius_mm": OUTER_R_MM,
        "cap_thickness_mm": CAP_T_MM,
        "top_cap": case_info["top_cap"],
        "bottom_cap": case_info["bottom_cap"],
        "bottom_hole_r_mm": case_info["bottom_hole_r_mm"],
        "B0_Bz_T": B0_BZ_T,
        "Bcenter_Bx_T": bx,
        "Bcenter_By_T": by,
        "Bcenter_Bz_T": bz,
        "Bcenter_Mag_T": bmag,
        "SFz": sfz,
        "LeakageRatioz": leakage,
        "IntH2_total_with_caps": int_total,
        "IntH2_ferrite_only": int_ferrite,
        "IntH2_caps": int_caps,
        "source_project": project_path,
        "status": status,
        "notes": case_info["notes"],
    }
    append_csv_row(OUT_CSV, FIELDNAMES, out)

    safe(fp, "Save project", lambda: oProject.Save())
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass

    log(fp, "RESULT SFz=" + str(sfz) + " LeakageRatioz=" + str(leakage) +
        " IntH2_total_with_caps=" + str(int_total) + " status=" + status)


def run():
    ensure_dirs()
    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "run_axial_capped_end_experiment " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "ANALYZE=" + str(ANALYZE))
        log(fp, "BASE_PROJECT=" + BASE_PROJECT)
        log(fp, "OUTER_R_MM=" + str(OUTER_R_MM) + " CAP_T_MM=" + str(CAP_T_MM))
        log(fp, "cases=" + str([c["case_id"] for c in CASES]))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case_info in CASES:
            try:
                process_case(fp, oDesktop, case_info)
            except Exception:
                log(fp, "CASE FAILED " + case_info.get("case_id", "unknown"))
                log(fp, traceback.format_exc())
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
