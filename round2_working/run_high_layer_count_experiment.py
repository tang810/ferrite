# -*- coding: utf-8 -*-
"""
run_high_layer_count_experiment.py
==================================
Build and solve N=5/N=6 ferrite-only continuous-shell experiments.

Run inside Ansys Electronics Desktop:

    Tools -> Run Script -> D:\ferrite\aaaaaaaaximukeji\round2_working\run_high_layer_count_experiment.py

Design logic:
    - Keep Rin = 100 mm and L = 200 mm.
    - Keep total ferrite thickness at 0.60 mm.
    - Keep radial inter-layer gap at 0.08 mm.
    - Compare N=5 and N=6 against the existing N=4 baseline.

The script copies the validated C2_N4_t015_g008_x project, removes the old
four ferrite shells, creates new N-layer ferrite shells, solves Setup1, and
exports Bcenter, SFx and IntH2 values into a separate raw CSV.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
BASE_PROJECT = os.path.join(
    BASE_DIR, "round2_working", "manufacturable_thin", "C2_N4_t015_g008_shield.aedt"
)
OUT_DIR = os.path.join(BASE_DIR, "round2_working", "high_layer_count")
OUT_CSV = os.path.join(BASE_DIR, "data", "raw", "high_layer_count_exports.csv")
LOG_PATH = os.path.join(OUT_DIR, "run_high_layer_count_experiment.log")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

ANALYZE = True
CASE_ID_FILTER = []  # Example: ["C2_N5_t012_g008_x"]

RIN_MM = 100.0
LENGTH_MM = 200.0
GAP_MM = 0.08
TOTAL_FERRITE_MM = 0.60
FERRITE_MU_R = 1000
FERRITE_SIGMA_S_PER_M = 0.01
B0_BX_T = 1.25663682659e-06
BASELINE_SFX = 3.62910729
BASELINE_INTH2 = 4.16011287324e-06
MESH_DIVISOR_LAYER = 2.0

OLD_FERRITE_OBJECTS = [
    "Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8",
    "FerriteLayer1", "FerriteLayer2", "FerriteLayer3", "FerriteLayer4",
    "FerriteLayer5", "FerriteLayer6",
]

CASES = [
    {
        "case_id": "C2_N5_t012_g008_x",
        "N_layers": 5,
        "t_ferrite_mm": 0.12,
        "g_radial_mm": GAP_MM,
        "notes": "fixed total ferrite thickness 0.60 mm; N=5 continuation",
    },
    {
        "case_id": "C2_N6_t010_g008_x",
        "N_layers": 6,
        "t_ferrite_mm": 0.10,
        "g_radial_mm": GAP_MM,
        "notes": "fixed total ferrite thickness 0.60 mm; N=6 continuation",
    },
]

FIELDNAMES = [
    "case_id", "base_case", "field_dir",
    "Rin_mm", "L_mm", "N_layers", "t_ferrite_mm", "g_radial_mm",
    "T_ferrite_total_mm", "T_space_mm", "outer_radius_mm",
    "mu_r", "sigma_S_per_m",
    "B0_Bx_T", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T", "Bcenter_Mag_T",
    "SFx", "ResidualRatiox", "SFx_gain_vs_N4",
    "IntH2_total", "IntH2_ratio_vs_N4", "chiH",
    "source_project", "status", "notes",
]


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def log(fp, msg):
    fp.write((str(msg) + "\n").encode("utf-8"))
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


def fnum(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    try:
        return float(raw)
    except Exception:
        return str(raw)


def compute_bmag(bx, by, bz):
    try:
        x = float(bx)
        y = float(by)
        z = float(bz)
        return math.sqrt(x * x + y * y + z * z)
    except Exception:
        return ""


def get_material_from_object(fp, oEditor, obj_name):
    for prop in ["Material", "MaterialValue"]:
        try:
            raw = oEditor.GetPropertyValue("Geometry3DAttributeTab", obj_name, prop)
            if raw:
                material = str(raw).replace('"', "").strip()
                if material:
                    log(fp, "ferrite material from %s/%s: %s" % (obj_name, prop, material))
                    return material
        except Exception:
            pass
    log(fp, "ferrite material fallback: ferrite")
    return "ferrite"


def delete_if_exists(oEditor, names):
    for name in names:
        try:
            oEditor.Delete(["NAME:Selections", "Selections:=", name])
        except Exception:
            pass


def total_space_mm(n_layers, t_mm, g_mm):
    return n_layers * t_mm + (n_layers - 1) * g_mm


def create_cylinder(fp, oEditor, name, radius_mm, material_name, solve_inside):
    safe(fp, "create cylinder " + name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", str(-LENGTH_MM / 2.0) + "mm",
              "Radius:=", str(radius_mm) + "mm",
              "Height:=", str(LENGTH_MM) + "mm",
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


def create_shell(fp, oEditor, shell_name, inner_r_mm, outer_r_mm, material_name):
    outer_name = shell_name + "_outer"
    inner_name = shell_name + "_inner_tool"
    delete_if_exists(oEditor, [shell_name, outer_name, inner_name])

    create_cylinder(fp, oEditor, outer_name, outer_r_mm, material_name, True)
    create_cylinder(fp, oEditor, inner_name, inner_r_mm, "vacuum", False)

    safe(fp, "subtract inner tool from " + outer_name,
         lambda: oEditor.Subtract(
             ["NAME:Selections", "Blank Parts:=", outer_name, "Tool Parts:=", inner_name],
             ["NAME:SubtractParameters", "KeepOriginals:=", False]))

    safe(fp, "rename " + outer_name + " to " + shell_name,
         lambda: oEditor.ChangeProperty([
             "NAME:AllTabs",
             ["NAME:Geometry3DAttributeTab",
              ["NAME:PropServers", outer_name],
              ["NAME:ChangedProps", ["NAME:Name", "Value:=", shell_name]]],
         ]))


def rebuild_ferrite_layers(fp, oEditor, case, material_name):
    n_layers = int(case["N_layers"])
    t_mm = fnum(case["t_ferrite_mm"])
    g_mm = fnum(case["g_radial_mm"])
    ferrite_objects = []

    delete_if_exists(oEditor, OLD_FERRITE_OBJECTS)
    for i in range(n_layers):
        inner_r = RIN_MM + i * (t_mm + g_mm)
        outer_r = inner_r + t_mm
        name = "FerriteLayer%d" % (i + 1)
        create_shell(fp, oEditor, name, inner_r, outer_r, material_name)
        ferrite_objects.append(name)
        log(fp, "%s radii mm: inner=%.6f outer=%.6f" % (name, inner_r, outer_r))

    return ferrite_objects


def assign_layer_mesh(fp, oDesign, ferrite_objects, t_mm):
    mesh = oDesign.GetModule("MeshSetup")
    max_len = t_mm / MESH_DIVISOR_LAYER
    if max_len <= 0:
        max_len = 0.05
    try:
        mesh.DeleteMeshOperations(["Length_high_layer_count"])
    except Exception:
        pass
    safe(fp, "assign mesh to high-layer ferrite",
         lambda: mesh.AssignLengthOp([
             "NAME:Length_high_layer_count",
             "RefineInside:=", True,
             "Objects:=", ferrite_objects,
             "RestrictElem:=", True,
             "NumMaxElem:=", "2000",
             "RestrictLength:=", True,
             "MaxLength:=", str(max_len) + "mm",
         ]))
    log(fp, "layer mesh MaxLength mm: " + str(max_len))


def eval_b_component(fields, comp):
    op = {"Bx": "ScalarX", "By": "ScalarY", "Bz": "ScalarZ"}[comp]
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp(op)
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_h2_integral_over_objects(fields, objects):
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


def append_csv_row(path, fieldnames, row):
    ensure_dir(os.path.dirname(path))
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, "ab") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def prepare_destination(fp, project_path):
    if os.path.exists(project_path + ".lock"):
        log(fp, "TARGET LOCK EXISTS, skip: " + project_path + ".lock")
        return False
    results_dir = project_path + "results"
    for path in [project_path, results_dir]:
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


def process_case(fp, oDesktop, case):
    case_id = case["case_id"]
    project_path = os.path.join(OUT_DIR, case_id + "_shield.aedt")
    n_layers = int(case["N_layers"])
    t_mm = fnum(case["t_ferrite_mm"])
    g_mm = fnum(case["g_radial_mm"])
    t_space = total_space_mm(n_layers, t_mm, g_mm)
    outer_radius = RIN_MM + t_space

    log(fp, "")
    log(fp, "=" * 72)
    log(fp, "CASE " + case_id)
    log(fp, "N=%d t=%.6fmm g=%.6fmm T_ferrite=%.6fmm Tspace=%.6fmm outer_radius=%.6fmm" %
        (n_layers, t_mm, g_mm, TOTAL_FERRITE_MM, t_space, outer_radius))

    if not os.path.exists(BASE_PROJECT):
        log(fp, "BASE PROJECT MISSING: " + BASE_PROJECT)
        return
    if os.path.exists(BASE_PROJECT + ".lock"):
        log(fp, "BASE PROJECT LOCK EXISTS: " + BASE_PROJECT + ".lock")
        return
    if not prepare_destination(fp, project_path):
        return

    shutil.copy2(BASE_PROJECT, project_path)
    log(fp, "copied baseline -> " + project_path)

    safe(fp, "OpenProject", lambda: oDesktop.OpenProject(project_path))
    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")

    material_name = get_material_from_object(fp, oEditor, "Cylinder2")
    ferrite_objects = rebuild_ferrite_layers(fp, oEditor, case, material_name)
    assign_layer_mesh(fp, oDesign, ferrite_objects, t_mm)
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())

    if ANALYZE:
        analyze_start = time.time()
        log(fp, "Analyze Setup1: START " + time.strftime("%Y-%m-%d %H:%M:%S"))
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
        log(fp, "Analyze Setup1: RETURN elapsed_s=" + str(time.time() - analyze_start))

    fields = oDesign.GetModule("FieldsReporter")
    bx = safe(fp, "Bcenter Bx", lambda: eval_b_component(fields, "Bx"))
    by = safe(fp, "Bcenter By", lambda: eval_b_component(fields, "By"))
    bz = safe(fp, "Bcenter Bz", lambda: eval_b_component(fields, "Bz"))
    bmag = compute_bmag(bx, by, bz)
    int_total = safe(fp, "IntH2_total ferrite layers",
                     lambda: eval_h2_integral_over_objects(fields, ferrite_objects))

    sfx = ""
    residual = ""
    sfx_gain = ""
    int_ratio = ""
    chi_h = ""
    try:
        sfx = B0_BX_T / abs(float(bx))
        residual = abs(float(bx)) / B0_BX_T
        sfx_gain = float(sfx) / BASELINE_SFX
    except Exception:
        pass
    try:
        int_ratio = float(int_total) / BASELINE_INTH2
        if sfx and float(sfx) > 1:
            chi_h = float(int_total) / math.log(float(sfx))
    except Exception:
        pass

    status = "exported" if bx not in ["", None] and int_total not in ["", None] else "failed"
    row = {
        "case_id": case_id,
        "base_case": "C2_N4_t015_g008_x",
        "field_dir": "x",
        "Rin_mm": RIN_MM,
        "L_mm": LENGTH_MM,
        "N_layers": n_layers,
        "t_ferrite_mm": t_mm,
        "g_radial_mm": g_mm,
        "T_ferrite_total_mm": TOTAL_FERRITE_MM,
        "T_space_mm": t_space,
        "outer_radius_mm": outer_radius,
        "mu_r": FERRITE_MU_R,
        "sigma_S_per_m": FERRITE_SIGMA_S_PER_M,
        "B0_Bx_T": B0_BX_T,
        "Bcenter_Bx_T": bx,
        "Bcenter_By_T": by,
        "Bcenter_Bz_T": bz,
        "Bcenter_Mag_T": bmag,
        "SFx": sfx,
        "ResidualRatiox": residual,
        "SFx_gain_vs_N4": sfx_gain,
        "IntH2_total": int_total,
        "IntH2_ratio_vs_N4": int_ratio,
        "chiH": chi_h,
        "source_project": project_path,
        "status": status,
        "notes": case.get("notes", ""),
    }
    append_csv_row(OUT_CSV, FIELDNAMES, row)

    safe(fp, "Save project", lambda: oProject.Save())
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass
    log(fp, "RESULT SFx=" + str(sfx) + " SFx_gain_vs_N4=" + str(sfx_gain) +
        " IntH2_ratio_vs_N4=" + str(int_ratio) + " status=" + status)


def run():
    ensure_dir(OUT_DIR)
    cases = []
    for case in CASES:
        if CASE_ID_FILTER and case["case_id"] not in CASE_ID_FILTER:
            continue
        cases.append(case)

    fp = open(LOG_PATH, "wb")
    try:
        log(fp, "run_high_layer_count_experiment " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "ANALYZE=" + str(ANALYZE))
        log(fp, "cases=" + str([c["case_id"] for c in cases]))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case in cases:
            try:
                process_case(fp, oDesktop, case)
            except Exception:
                log(fp, "CASE FAILED: " + case.get("case_id", "unknown"))
                log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        fp.close()


run()

