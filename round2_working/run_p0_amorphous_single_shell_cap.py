# -*- coding: utf-8 -*-
"""
Build and solve the updated P0 axial shield model:

    P0 = single-layer amorphous cylindrical shell + one amorphous cap

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/run_p0_amorphous_single_shell_cap.py

Geometry:
  - z-directed B0 reference project is used as the base model.
  - One continuous amorphous cylindrical shell is added.
  - One amorphous cap is added on the +Z end; the -Z end remains open.

Material:
  - amorphous, mu_r = 10000, conductivity = 1 S/m placeholder.

This is an IronPython 2.7/AEDT script. Keep syntax conservative.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
BASE_PROJECT = os.path.join(BASE_DIR, "aedt", "reference", "B0_reference_z.aedt")
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "p0_amorphous_single_shell_cap")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw", "p0_amorphous_single_shell_cap_exports.csv")
LOG_PATH = os.path.join(OUT_DIR, "run_p0_amorphous_single_shell_cap.log")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

CASE_ID = "P0_amorphous_single_shell_plusZ_cap_mu10000"
B0_BZ_T = 1.25663644033e-06

RIN_MM = 100.0
LENGTH_MM = 200.0
SHELL_T_MM = 0.20
CAP_T_MM = 0.20
CAP_AXIAL_GAP_MM = 0.03

AMORPHOUS_MATERIAL_NAME = "p0_amorphous_mu10000"
AMORPHOUS_MU_R = 10000
AMORPHOUS_SIGMA_S_PER_M = 1

SHELL_MESH_MAX_LENGTH_MM = 0.08
CAP_MESH_MAX_LENGTH_MM = 0.50

ANALYZE = True
COMPUTE_INTH2 = False

SHELL_OBJECT = "P0_Amorphous_Shell"
CAP_OBJECT = "P0_Amorphous_Cap_PlusZ"

FIELDNAMES = [
    "case_id", "base_case", "field_dir",
    "Rin_mm", "L_mm", "shell_t_mm", "cap_t_mm", "cap_side",
    "material", "mu_r", "sigma_S_per_m",
    "B0_Bz_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
    "Bcenter_Mag_T", "SFz", "LeakageRatioz",
    "IntH2_total", "source_project", "status", "notes",
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


def is_true_result(value):
    if value is True:
        return True
    try:
        text = str(value).strip().lower()
        return text in ["true", "1", "yes"]
    except Exception:
        return False


def append_csv_row(path, fieldnames, row):
    exists = os.path.exists(path) and os.path.getsize(path) > 0
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


def prepare_destination(fp, project_path):
    if os.path.exists(project_path + ".lock"):
        log(fp, "TARGET LOCK EXISTS, skip: " + project_path + ".lock")
        return False
    for path in [project_path, project_path + "results"]:
        if os.path.exists(path):
            if os.path.abspath(path).lower().startswith(os.path.abspath(OUT_DIR).lower()):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            else:
                log(fp, "Refuse to remove outside OUT_DIR: " + path)
                return False
    return True


def add_amorphous_material(fp, oProject):
    oDefMgr = oProject.GetDefinitionManager()
    props = [
        "NAME:" + AMORPHOUS_MATERIAL_NAME,
        "CoordinateSystemType:=", "Cartesian",
        "BulkOrSurfaceType:=", 1,
        ["NAME:PhysicsTypes", "Set:=", ["Electromagnetic", "Thermal"]],
        "permeability:=", str(AMORPHOUS_MU_R),
        "conductivity:=", str(AMORPHOUS_SIGMA_S_PER_M),
        "dielectric_loss_tangent:=", "0",
        "magnetic_loss_tangent:=", "0",
    ]
    try:
        oDefMgr.AddMaterial(props)
        log(fp, "created material " + AMORPHOUS_MATERIAL_NAME)
    except Exception:
        log(fp, "material may already exist: " + AMORPHOUS_MATERIAL_NAME)
    return AMORPHOUS_MATERIAL_NAME


def delete_if_exists(oEditor, names):
    for name in names:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", name])
        except Exception:
            pass


def create_cylinder(fp, oEditor, name, radius_mm, z_start_mm, height_mm, material_name, solve_inside):
    safe(fp, "create cylinder " + name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", str(z_start_mm) + "mm",
              "Radius:=", str(radius_mm) + "mm",
              "Height:=", str(height_mm) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", name,
              "Flags:=", "",
              "Color:=", "(80 120 210)",
              "Transparency:=", 0,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"' + material_name + '"',
              "SolveInside:=", solve_inside,
              "ShellElement:=", False,
              "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              "UseMaterialAppearance:=", False,
              "IsLightweight:=", False,
              "IsAlwaysHidden:=", False,
              ]))


def create_shell(fp, oEditor, mat_name):
    outer_r = RIN_MM + SHELL_T_MM
    outer_name = SHELL_OBJECT + "_outer"
    inner_name = SHELL_OBJECT + "_inner_tool"
    delete_if_exists(oEditor, [SHELL_OBJECT, outer_name, inner_name])

    create_cylinder(fp, oEditor, outer_name, outer_r, -LENGTH_MM / 2.0,
                    LENGTH_MM, mat_name, True)
    create_cylinder(fp, oEditor, inner_name, RIN_MM, -LENGTH_MM / 2.0,
                    LENGTH_MM, "vacuum", False)
    safe(fp, "subtract inner tool from shell",
         lambda: oEditor.Subtract(
             ["NAME:Selections", "Blank Parts:=", outer_name, "Tool Parts:=", inner_name],
             ["NAME:SubtractParameters", "KeepOriginals:=", False]))
    safe(fp, "rename shell",
         lambda: oEditor.ChangeProperty([
             "NAME:AllTabs",
             ["NAME:Geometry3DAttributeTab",
              ["NAME:PropServers", outer_name],
              ["NAME:ChangedProps", ["NAME:Name", "Value:=", SHELL_OBJECT]]],
         ]))
    log(fp, "shell radii mm: inner=" + str(RIN_MM) + " outer=" + str(outer_r))


def create_plus_z_cap(fp, oEditor, mat_name):
    delete_if_exists(oEditor, [CAP_OBJECT])
    z_start = LENGTH_MM / 2.0 + CAP_AXIAL_GAP_MM
    create_cylinder(fp, oEditor, CAP_OBJECT, RIN_MM + SHELL_T_MM,
                    z_start, CAP_T_MM, mat_name, True)
    log(fp, "plus-Z cap z_start_mm=" + str(z_start) +
        " radius_mm=" + str(RIN_MM + SHELL_T_MM))


def assign_mesh(fp, oDesign):
    mesh = oDesign.GetModule("MeshSetup")
    for name in ["Length_p0_amorphous_shell", "Length_p0_amorphous_cap"]:
        try:
            mesh.DeleteMeshOperations([name])
        except Exception:
            pass
    safe(fp, "assign shell mesh",
         lambda: mesh.AssignLengthOp([
             "NAME:Length_p0_amorphous_shell",
             "RefineInside:=", True,
             "Objects:=", [SHELL_OBJECT],
             "RestrictElem:=", True,
             "NumMaxElem:=", "5000",
             "RestrictLength:=", True,
             "MaxLength:=", str(SHELL_MESH_MAX_LENGTH_MM) + "mm",
         ]))
    safe(fp, "assign cap mesh",
         lambda: mesh.AssignLengthOp([
             "NAME:Length_p0_amorphous_cap",
             "RefineInside:=", True,
             "Objects:=", [CAP_OBJECT],
             "RestrictElem:=", True,
             "NumMaxElem:=", "5000",
             "RestrictLength:=", True,
             "MaxLength:=", str(CAP_MESH_MAX_LENGTH_MM) + "mm",
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
        return ""

    def object_comp_integral(obj, comp):
        op = {"x": "ScalarX", "y": "ScalarY", "z": "ScalarZ"}[comp]
        fields.CalcStack("clear")
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.EnterQty("H")
        fields.CalcOp(op)
        fields.CalcOp("*")
        fields.EnterVol(obj)
        fields.CalcOp("Integrate")
        fields.ClcEval(SOLN, [])
        return extract_value(fields.GetTopEntryValue(SOLN, []))

    total = 0.0
    for obj in objects:
        for comp in ["x", "y", "z"]:
            total += float(object_comp_integral(obj, comp))
    return total


def process_case(fp, oDesktop):
    project_path = os.path.join(OUT_DIR, CASE_ID + ".aedt")

    log(fp, "")
    log(fp, "=" * 72)
    log(fp, "CASE " + CASE_ID)

    if not os.path.exists(BASE_PROJECT):
        log(fp, "BASE PROJECT MISSING: " + BASE_PROJECT)
        return
    if not prepare_destination(fp, project_path):
        return

    shutil.copy2(BASE_PROJECT, project_path)
    log(fp, "copied B0 reference -> " + project_path)

    safe(fp, "OpenProject", lambda: oDesktop.OpenProject(project_path))
    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")

    mat_name = add_amorphous_material(fp, oProject)
    delete_if_exists(oEditor, [SHELL_OBJECT, SHELL_OBJECT + "_outer",
                               SHELL_OBJECT + "_inner_tool", CAP_OBJECT])
    create_shell(fp, oEditor, mat_name)
    create_plus_z_cap(fp, oEditor, mat_name)
    assign_mesh(fp, oDesign)

    valid = safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    if not is_true_result(valid):
        append_csv_row(OUT_CSV, FIELDNAMES, {
            "case_id": CASE_ID,
            "base_case": "B0_reference_z",
            "field_dir": "z",
            "Rin_mm": RIN_MM,
            "L_mm": LENGTH_MM,
            "shell_t_mm": SHELL_T_MM,
            "cap_t_mm": CAP_T_MM,
            "cap_side": "+Z",
            "material": "amorphous",
            "mu_r": AMORPHOUS_MU_R,
            "sigma_S_per_m": AMORPHOUS_SIGMA_S_PER_M,
            "B0_Bz_T": B0_BZ_T,
            "source_project": project_path,
            "status": "validate_failed",
            "notes": "P0 amorphous shell plus single amorphous cap",
        })
        safe(fp, "Save invalid project", lambda: oProject.Save())
        return

    safe(fp, "Save project before analyze", lambda: oProject.Save())
    analyze_ret = True
    if ANALYZE:
        start = time.time()
        log(fp, "Analyze Setup1: START " + time.strftime("%Y-%m-%d %H:%M:%S"))
        analyze_ret = safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
        log(fp, "Analyze Setup1: RETURN elapsed_s=" + str(time.time() - start))

    if analyze_ret is None:
        append_csv_row(OUT_CSV, FIELDNAMES, {
            "case_id": CASE_ID,
            "base_case": "B0_reference_z",
            "field_dir": "z",
            "Rin_mm": RIN_MM,
            "L_mm": LENGTH_MM,
            "shell_t_mm": SHELL_T_MM,
            "cap_t_mm": CAP_T_MM,
            "cap_side": "+Z",
            "material": "amorphous",
            "mu_r": AMORPHOUS_MU_R,
            "sigma_S_per_m": AMORPHOUS_SIGMA_S_PER_M,
            "B0_Bz_T": B0_BZ_T,
            "source_project": project_path,
            "status": "analyze_failed",
            "notes": "P0 amorphous shell plus single amorphous cap",
        })
        safe(fp, "Save failed project", lambda: oProject.Save())
        return

    fields = oDesign.GetModule("FieldsReporter")
    bx = safe(fp, "Bcenter_Bx", lambda: eval_b_component(fields, "Bx"))
    by = safe(fp, "Bcenter_By", lambda: eval_b_component(fields, "By"))
    bz = safe(fp, "Bcenter_Bz", lambda: eval_b_component(fields, "Bz"))
    bmag = compute_bmag(bx, by, bz)

    sfz = ""
    leakage = ""
    try:
        sfz = abs(B0_BZ_T) / abs(float(bz))
        leakage = abs(float(bz)) / abs(B0_BZ_T)
    except Exception:
        pass

    int_h2 = ""
    if COMPUTE_INTH2:
        int_h2 = safe(fp, "IntH2 amorphous shell plus cap",
                      lambda: eval_h2_integral_over_objects(fields, [SHELL_OBJECT, CAP_OBJECT]))
    else:
        log(fp, "IntH2 skipped")

    status = "exported" if bz not in ["", None] else "failed"
    append_csv_row(OUT_CSV, FIELDNAMES, {
        "case_id": CASE_ID,
        "base_case": "B0_reference_z",
        "field_dir": "z",
        "Rin_mm": RIN_MM,
        "L_mm": LENGTH_MM,
        "shell_t_mm": SHELL_T_MM,
        "cap_t_mm": CAP_T_MM,
        "cap_side": "+Z",
        "material": "amorphous",
        "mu_r": AMORPHOUS_MU_R,
        "sigma_S_per_m": AMORPHOUS_SIGMA_S_PER_M,
        "B0_Bz_T": B0_BZ_T,
        "Bcenter_Bx_T": bx,
        "Bcenter_By_T": by,
        "Bcenter_Bz_T": bz,
        "Bcenter_Mag_T": bmag,
        "SFz": sfz,
        "LeakageRatioz": leakage,
        "IntH2_total": int_h2,
        "source_project": project_path,
        "status": status,
        "notes": "P0 amorphous shell plus single +Z amorphous cap; IntH2 skipped" if not COMPUTE_INTH2 else "P0 amorphous shell plus single +Z amorphous cap",
    })

    safe(fp, "Save project", lambda: oProject.Save())
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass

    log(fp, "RESULT SFz=" + str(sfz) + " LeakageRatioz=" + str(leakage) +
        " status=" + status)


def run():
    ensure_dirs()
    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "run_p0_amorphous_single_shell_cap " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "BASE_PROJECT=" + BASE_PROJECT)
        log(fp, "CASE_ID=" + CASE_ID)
        log(fp, "RIN_MM=" + str(RIN_MM) + " LENGTH_MM=" + str(LENGTH_MM))
        log(fp, "SHELL_T_MM=" + str(SHELL_T_MM) + " CAP_T_MM=" + str(CAP_T_MM) +
            " CAP_AXIAL_GAP_MM=" + str(CAP_AXIAL_GAP_MM))
        log(fp, "AMORPHOUS_MU_R=" + str(AMORPHOUS_MU_R) +
            " AMORPHOUS_SIGMA_S_PER_M=" + str(AMORPHOUS_SIGMA_S_PER_M))
        log(fp, "SHELL_MESH_MAX_LENGTH_MM=" + str(SHELL_MESH_MAX_LENGTH_MM) +
            " CAP_MESH_MAX_LENGTH_MM=" + str(CAP_MESH_MAX_LENGTH_MM))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()
        process_case(fp, oDesktop)
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
