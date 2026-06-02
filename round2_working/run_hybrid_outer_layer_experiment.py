# -*- coding: utf-8 -*-
"""
Run hybrid outer-layer AEDT experiments.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> round2_working/run_hybrid_outer_layer_experiment.py

What it does:
  1. Copies the validated baseline shield project C2_N4_t015_g008_shield.aedt.
  2. Adds an outer amorphous or nanocrystalline cylindrical shell.
  3. Optionally cuts one axial slit in the outer shell.
  4. Solves Setup1.
  5. Exports Bcenter components and computes SFx with the validated B0_Bx.
  6. Computes IntH2_total and IntH2_outer from the field calculator.

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
HYBRID_MATRIX = os.path.join(BASE_DIR, "hybrid_outer_layer_design_points.csv")
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "hybrid_outer_layer")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw", "hybrid_outer_layer_exports.csv")
LOG_PATH = os.path.join(OUT_DIR, "run_hybrid_outer_layer_experiment.log")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

BASE_PROJECT = os.path.join(PROJECT_DIR, "C2_N4_t015_g008_shield.aedt")
BASE_CASE_ID = "C2_N4_t015_g008_x"
BASE_SFX = 3.62910729
BASE_INTH2 = 4.16011287324e-06
B0_BX_T = 1.25663682659e-06

RIN_MM = 100.0
LENGTH_MM = 200.0
FERRITE_LAYERS = 4
FERRITE_T_MM = 0.15
FERRITE_G_MM = 0.08
FERRITE_TSPACE_MM = 0.84
MESH_DIVISOR_OUTER = 2.0

# To start with the most defensible first run, keep only one case enabled.
# Add more case IDs here after the first log/export is checked.
CASE_ID_FILTER = [
    "H_C2_N4_t015_g008_x_outer_nanocrystalline_1wrap",
]

ANALYZE = True


FIELDNAMES = [
    "case_id", "base_case", "outer_material", "outer_wraps",
    "outer_total_t_mm", "outer_gap_from_ferrite_mm", "outer_mu_r_prime",
    "outer_mu_r_double_prime", "outer_sigma_S_per_m", "outer_pattern",
    "axial_slit_width_mm", "field_dir",
    "B0_Bx_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
    "Bcenter_Mag_T", "SFx", "ResidualRatiox", "SFx_gain",
    "IntH2_total", "IntH2_outer", "IntH2_ratio", "chiH",
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


def f(row, key, default=0.0):
    try:
        text = str(row.get(key, "")).strip()
        if text == "":
            return default
        return float(text)
    except Exception:
        return default


def read_cases():
    rows = []
    with open(HYBRID_MATRIX, "r") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            case_id = row.get("case_id", "")
            if CASE_ID_FILTER and case_id not in CASE_ID_FILTER:
                continue
            rows.append(row)
    return rows


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


def add_or_update_material(fp, oProject, row):
    material = row["outer_material"]
    mu = row.get("outer_mu_r_prime", "")
    sigma = row.get("outer_sigma_S_per_m", "")
    mu_pp = row.get("outer_mu_r_double_prime", "")
    mat_name = "hybrid_outer_" + material
    if mu:
        mat_name = mat_name + "_mu" + str(int(float(mu)))

    if sigma == "":
        # Placeholder. Replace with measured/vendor data before final claims.
        sigma = "1"

    oDefMgr = oProject.GetDefinitionManager()
    props = [
        "NAME:" + mat_name,
        "CoordinateSystemType:=", "Cartesian",
        "BulkOrSurfaceType:=", 1,
        ["NAME:PhysicsTypes", "Set:=", ["Electromagnetic", "Thermal"]],
        "permeability:=", str(mu if mu else "10000"),
        "conductivity:=", str(sigma),
        "dielectric_loss_tangent:=", "0",
        "magnetic_loss_tangent:=", "0",
    ]
    if mu_pp:
        # AEDT material models differ by version. Keep mu'' in notes/log and
        # use magnetic_loss_tangent as an approximate placeholder only if the
        # user later decides to provide a frequency-specific loss model.
        log(fp, "outer mu_double_prime recorded but not directly assigned: " + str(mu_pp))

    try:
        oDefMgr.AddMaterial(props)
        log(fp, "created material " + mat_name)
    except Exception:
        log(fp, "AddMaterial may already exist: " + mat_name)
    return mat_name


def create_outer_shell(fp, oEditor, mat_name, row):
    outer_t = f(row, "outer_total_t_mm")
    outer_gap = f(row, "outer_gap_from_ferrite_mm")
    inner_r = RIN_MM + FERRITE_TSPACE_MM + outer_gap
    outer_r = inner_r + outer_t
    outer_name = "HybridOuterLayer_outer"
    inner_name = "HybridOuterLayer_inner"

    for name in [outer_name, inner_name, "HybridOuterLayer"]:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", name])
        except Exception:
            pass

    safe(fp, "create outer cylinder",
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", "-" + str(LENGTH_MM / 2.0) + "mm",
              "Radius:=", str(outer_r) + "mm",
              "Height:=", str(LENGTH_MM) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", outer_name,
              "Flags:=", "",
              "Color:=", "(45 90 180)",
              "Transparency:=", 0,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"' + mat_name + '"',
              "SolveInside:=", True,
              "ShellElement:=", False,
              "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              "UseMaterialAppearance:=", False,
              "IsLightweight:=", False,
              "IsAlwaysHidden:=", False,
              ]))

    safe(fp, "create inner tool cylinder",
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", "-" + str(LENGTH_MM / 2.0) + "mm",
              "Radius:=", str(inner_r) + "mm",
              "Height:=", str(LENGTH_MM) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", inner_name,
              "Flags:=", "",
              "Color:=", "(255 0 0)",
              "Transparency:=", 0.7,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"vacuum"',
              "SolveInside:=", False,
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              ]))

    safe(fp, "subtract inner tool from outer shell",
         lambda: oEditor.Subtract(
             ["NAME:Selections",
              "Blank Parts:=", outer_name,
              "Tool Parts:=", inner_name],
             ["NAME:SubtractParameters", "KeepOriginals:=", False]))

    safe(fp, "rename outer shell",
         lambda: oEditor.ChangeProperty([
             "NAME:AllTabs",
             ["NAME:Geometry3DAttributeTab",
              ["NAME:PropServers", outer_name],
              ["NAME:ChangedProps", ["NAME:Name", "Value:=", "HybridOuterLayer"]]],
         ]))

    log(fp, "outer shell radii mm: inner=" + str(inner_r) + " outer=" + str(outer_r))
    return "HybridOuterLayer"


def cut_axial_slit(fp, oEditor, row, outer_name):
    pattern = row.get("outer_pattern", "")
    if pattern != "single_axial_slit":
        return

    slit = f(row, "axial_slit_width_mm", 1.6)
    outer_t = f(row, "outer_total_t_mm")
    outer_gap = f(row, "outer_gap_from_ferrite_mm")
    inner_r = RIN_MM + FERRITE_TSPACE_MM + outer_gap
    outer_r = inner_r + outer_t
    radial_depth = outer_t + 4.0
    box_name = "HybridOuterLayer_AxialSlitTool"

    try:
        oEditor.Delete(["NAME:Selections", "Selections:=", box_name])
    except Exception:
        pass

    x_pos = inner_r - 2.0
    y_pos = -slit / 2.0
    z_pos = -LENGTH_MM / 2.0 - 1.0
    safe(fp, "create axial slit tool",
         lambda: oEditor.CreateBox(
             ["NAME:BoxParameters",
              "XPosition:=", str(x_pos) + "mm",
              "YPosition:=", str(y_pos) + "mm",
              "ZPosition:=", str(z_pos) + "mm",
              "XSize:=", str(radial_depth) + "mm",
              "YSize:=", str(slit) + "mm",
              "ZSize:=", str(LENGTH_MM + 2.0) + "mm"],
             ["NAME:Attributes",
              "Name:=", box_name,
              "Flags:=", "",
              "Color:=", "(255 0 0)",
              "Transparency:=", 0.5,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"vacuum"',
              "SolveInside:=", False,
              ]))

    safe(fp, "subtract axial slit from outer shell",
         lambda: oEditor.Subtract(
             ["NAME:Selections",
              "Blank Parts:=", outer_name,
              "Tool Parts:=", box_name],
             ["NAME:SubtractParameters", "KeepOriginals:=", False]))


def assign_outer_mesh(fp, oDesign, outer_name, outer_t_mm):
    mesh = oDesign.GetModule("MeshSetup")
    max_len = outer_t_mm / MESH_DIVISOR_OUTER
    if max_len <= 0:
        max_len = 0.01
    try:
        mesh.DeleteMeshOperations(["Length_outer_hybrid"])
    except Exception:
        pass
    safe(fp, "assign mesh to outer layer",
         lambda: mesh.AssignLengthOp([
             "NAME:Length_outer_hybrid",
             "RefineInside:=", True,
             "Objects:=", [outer_name],
             "RestrictElem:=", True,
             "NumMaxElem:=", "2000",
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


def process_case(fp, oDesktop, row):
    case_id = row["case_id"]
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

    mat_name = add_or_update_material(fp, oProject, row)
    outer_name = create_outer_shell(fp, oEditor, mat_name, row)
    cut_axial_slit(fp, oEditor, row, outer_name)
    assign_outer_mesh(fp, oDesign, outer_name, f(row, "outer_total_t_mm"))

    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    if ANALYZE:
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    fields = oDesign.GetModule("FieldsReporter")
    bx = safe(fp, "Bcenter_Bx", lambda: eval_b_component(fields, "Bx"))
    by = safe(fp, "Bcenter_By", lambda: eval_b_component(fields, "By"))
    bz = safe(fp, "Bcenter_Bz", lambda: eval_b_component(fields, "Bz"))
    bmag = compute_bmag(bx, by, bz)

    sfx = ""
    residual = ""
    sfx_gain = ""
    if bx != "" and bx is not None:
        try:
            sfx = abs(B0_BX_T) / abs(float(bx))
            residual = abs(float(bx)) / abs(B0_BX_T)
            sfx_gain = sfx / BASE_SFX
        except Exception:
            pass

    ferrite_objects = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]
    int_total = safe(fp, "IntH2_total all ferrite plus outer",
                     lambda: eval_h2_integral_over_objects(fields, ferrite_objects + [outer_name]))
    int_outer = safe(fp, "IntH2_outer",
                     lambda: eval_h2_integral_over_objects(fields, [outer_name]))

    int_ratio = ""
    chi_h = ""
    try:
        int_ratio = float(int_total) / BASE_INTH2
        if sfx and float(sfx) > 1:
            chi_h = float(int_total) / math.log(float(sfx))
    except Exception:
        pass

    status = "exported" if bx not in ["", None] and int_total not in ["", None] else "failed"
    notes = "continuous outer first-pass"
    if row.get("outer_pattern", "") == "single_axial_slit":
        notes = "single axial slit outer layer"

    out = {
        "case_id": case_id,
        "base_case": BASE_CASE_ID,
        "outer_material": row.get("outer_material", ""),
        "outer_wraps": row.get("outer_wraps", ""),
        "outer_total_t_mm": row.get("outer_total_t_mm", ""),
        "outer_gap_from_ferrite_mm": row.get("outer_gap_from_ferrite_mm", ""),
        "outer_mu_r_prime": row.get("outer_mu_r_prime", ""),
        "outer_mu_r_double_prime": row.get("outer_mu_r_double_prime", ""),
        "outer_sigma_S_per_m": row.get("outer_sigma_S_per_m", ""),
        "outer_pattern": row.get("outer_pattern", ""),
        "axial_slit_width_mm": row.get("axial_slit_width_mm", ""),
        "field_dir": "x",
        "B0_Bx_T": B0_BX_T,
        "Bcenter_Bx_T": bx,
        "Bcenter_By_T": by,
        "Bcenter_Bz_T": bz,
        "Bcenter_Mag_T": bmag,
        "SFx": sfx,
        "ResidualRatiox": residual,
        "SFx_gain": sfx_gain,
        "IntH2_total": int_total,
        "IntH2_outer": int_outer,
        "IntH2_ratio": int_ratio,
        "chiH": chi_h,
        "source_project": project_path,
        "status": status,
        "notes": notes,
    }
    append_csv_row(OUT_CSV, FIELDNAMES, out)

    safe(fp, "Save project", lambda: oProject.Save())
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass

    log(fp, "RESULT SFx=" + str(sfx) + " SFx_gain=" + str(sfx_gain) +
        " IntH2_ratio=" + str(int_ratio) + " status=" + status)


def run():
    ensure_dirs()
    cases = read_cases()
    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "run_hybrid_outer_layer_experiment " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "ANALYZE=" + str(ANALYZE))
        log(fp, "cases=" + str([c["case_id"] for c in cases]))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for row in cases:
            try:
                process_case(fp, oDesktop, row)
            except Exception:
                log(fp, "CASE FAILED " + row.get("case_id", "unknown"))
                log(fp, traceback.format_exc())
    finally:
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
        fp.close()


run()
