# -*- coding: utf-8 -*-
"""Rebuild shield projects with x-directed tangential-H external field.

中文说明：
本脚本将单层及多层 shield 工程的外部场从旧的 torus/current 近似改为与
B0_reference_x 完全相同的 x-directed tangential-H / uniform external field。
脚本会删除旧的 torus/current 激励和几何体，在空气盒（Box1）表面施加 x 切向
H 场，保留铁氧体材料（不改为 vacuum），求解并导出中心场和 IntH2 数据。

运行方式：在 AEDT 中 Tools -> Run Script -> 选择本脚本。
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
LOG_PATH = os.path.join(BASE_DIR, "logs", "rebuild_shields_tangentialH.log")

CENTER_FIELD_OUT = os.path.join(BASE_DIR, "data", "raw", "center_field_raw.csv")
INTH2_OUT = os.path.join(BASE_DIR, "data", "raw", "intH2_layerwise_raw.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"

CASES = [
    {"case_id": "C1_N1_t008_x", "project": "C1_N1_t008_shield.aedt", "layers": 1},
    {"case_id": "C1_N1_t020_x", "project": "C1_N1_t020_shield.aedt", "layers": 1},
    {"case_id": "C1_N1_t040_x", "project": "C1_N1_t040_shield.aedt", "layers": 1},
    {"case_id": "C1_N1_t060_x", "project": "C1_N1_t060_shield.aedt", "layers": 1},
    {"case_id": "C2_N2_t020_g010_x", "project": "C2_N2_t020_g010_shield.aedt", "layers": 2},
    {"case_id": "C2_N3_t020_g010_x", "project": "C2_N3_t020_g010_shield.aedt", "layers": 3},
    {"case_id": "C2_N4_t015_g008_x", "project": "C2_N4_t015_g008_shield.aedt", "layers": 4},
]

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

# ---- Mesh refinement settings ----
# Each ferrite layer gets a LengthBased mesh operation with MaxLength = a / MESH_DIVISOR.
# For convergence studies, decrease MESH_DIVISOR to increase mesh density.
#    coarse : MESH_DIVISOR = 1   (MaxLength = a)
#    medium : MESH_DIVISOR = 3   (MaxLength = a/3)
#    fine   : MESH_DIVISOR = 5   (MaxLength = a/5)
# Default medium ensures ~3 tetrahedra across each layer thickness.
MESH_DIVISOR = 3
# For single-layer cases, the ferrite thickness is extracted from the case_id.
# Multilayer cases use FERRITE_LAYER_THICKNESS_MM below.
FERRITE_LAYER_THICKNESS_MM = {
    "C1_N1_t008_x": 0.08,
    "C1_N1_t020_x": 0.20,
    "C1_N1_t040_x": 0.40,
    "C1_N1_t060_x": 0.60,
    "C2_N2_t020_g010_x": 0.20,
    "C2_N3_t020_g010_x": 0.20,
    "C2_N4_t015_g008_x": 0.15,
}

EXTERNAL_FIELD_OBJECTS = [
    "Torus2", "Torus3",
    "Torus2_Section1", "Torus3_Section1",
    "Torus2_Section1_Separate1", "Torus3_Section1_Separate1",
    "Iext_plus_sheet", "Iext_minus_sheet",
    "Iext_plus_sheet_1", "Iext_minus_sheet_1",
]

CENTER_FIELD_FIELDNAMES = [
    "case_id", "field_dir", "Bcenter_Bx_T", "Bcenter_By_T",
    "Bcenter_Bz_T", "Bcenter_Mag_T", "source_project", "status",
]

MAX_LAYERS = 6
INTH2_FIELDNAMES = [
    "case_id", "coil_dir", "source_project", "status",
    "IntH2_total",
] + ["IntH2_L{}".format(i) for i in range(1, MAX_LAYERS + 1)] + [
    "notes",
]


def ensure_dirs():
    for p in [os.path.dirname(LOG_PATH), os.path.dirname(CENTER_FIELD_OUT),
              os.path.dirname(INTH2_OUT)]:
        if not os.path.isdir(p):
            os.makedirs(p)


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        value = fn()
        log(fp, "{}: OK{}".format(
            label, (" -> " + str(value)) if value is not None else ""))
        return True if value is None else value
    except Exception:
        log(fp, "{}: FAILED".format(label))
        log(fp, traceback.format_exc())
        return None


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        try:
            return float(raw[0])
        except (ValueError, TypeError, IndexError):
            return str(raw[0]) if raw else ""
    try:
        return float(raw)
    except (ValueError, TypeError):
        return str(raw)


def delete_old_boundaries(fp, oBoundary):
    names = []
    for getter in ["GetExcitations", "GetBoundaries"]:
        try:
            values = getattr(oBoundary, getter)()
            if values:
                names.extend(list(values))
        except Exception as exc:
            log(fp, "{} unavailable: {}".format(getter, str(exc)[:160]))
    for name in sorted(set(names + [
        "Iext_plus", "Iext_minus", "Current1", "Current2",
    ])):
        safe(fp, "delete boundary {}".format(name),
             lambda n=name: oBoundary.DeleteBoundaries([n]))


def cleanup_geometry(fp, oEditor):
    for obj in EXTERNAL_FIELD_OBJECTS:
        safe(fp, "delete external-field object {}".format(obj),
             lambda o=obj: oEditor.Delete([
                 "NAME:Selections", "Selections:=", o,
             ]))


def ensure_ferrite_material(fp, oEditor):
    for obj in FERRITE_OBJECTS:
        try:
            oEditor.GetObjectByName(obj)
            safe(fp, "{} -> ferrite".format(obj),
                 lambda o=obj: oEditor.ChangeProperty([
                     "NAME:AllTabs",
                     ["NAME:Geometry3DAttributeTab",
                      ["NAME:PropServers", o],
                      ["NAME:ChangedProps",
                       ["NAME:Material", "Value:=", '"ferrite"'],
                       ["NAME:Solve Inside", "Value:=", True]]],
                 ]))
        except Exception:
            pass


def clear_mesh_operations(fp, oDesign):
    """Delete all existing mesh operations to ensure a clean baseline."""
    try:
        mesh_module = oDesign.GetModule("MeshSetup")
        existing = []
        try:
            existing = list(mesh_module.GetMeshOperations())
        except Exception:
            pass
        for name in existing:
            safe(fp, "delete mesh op {}".format(name),
                 lambda n=name: mesh_module.DeleteMeshOperations([n]))
        log(fp, "Cleared {} existing mesh operations".format(len(existing)))
    except Exception:
        log(fp, "clear_mesh_operations: {}".format(traceback.format_exc()))


def assign_ferrite_mesh(fp, oDesign, oEditor, case_id, layers):
    """Apply LengthBased mesh refinement on every ferrite layer.

    Each layer gets MaxLength = a / MESH_DIVISOR, where a is the per-layer
    ferrite thickness.  The same length constraint is applied to both surface
    (RefineInside=false) and volume (RefineInside=true) operations.
    """
    a_mm = FERRITE_LAYER_THICKNESS_MM.get(case_id)
    if a_mm is None:
        log(fp, "WARNING: no thickness for {}, skipping mesh ops".format(case_id))
        return

    max_len_mm = a_mm / MESH_DIVISOR
    max_len = "{}mm".format(max_len_mm)
    ferrite_objs = []
    for obj in FERRITE_OBJECTS[:layers]:
        try:
            oEditor.GetObjectByName(obj)
            ferrite_objs.append(obj)
        except Exception:
            pass

    if not ferrite_objs:
        log(fp, "WARNING: no ferrite objects found for mesh assignment")
        return

    mesh_module = oDesign.GetModule("MeshSetup")
    for obj_name in ferrite_objs:
        # Surface refinement (RefineInside=false)
        safe(fp, "Mesh surface {}".format(obj_name),
             lambda n=obj_name, ml=max_len:
             mesh_module.AssignLengthOp([
                 "NAME:Length_surf_{}".format(n),
                 "RefineInside:=", False,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))
        # Volume refinement (RefineInside=true)
        safe(fp, "Mesh volume  {}".format(obj_name),
             lambda n=obj_name, ml=max_len:
             mesh_module.AssignLengthOp([
                 "NAME:Length_vol_{}".format(n),
                 "RefineInside:=", True,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))

    log(fp, "Assigned mesh: a=%.3fmm, MaxLength=%.4fmm (divisor=%d) on %s" % (
        a_mm, max_len_mm, MESH_DIVISOR, str(ferrite_objs)))


def face_centers(oEditor):
    faces = []
    for face in list(oEditor.GetFaceIDs("Box1")):
        center = [float(x) for x in oEditor.GetFaceCenter(face)]
        faces.append((int(face), center))
    return faces


def classify_box_faces(faces):
    groups = {"x": [], "y": [], "z": []}
    for face, center in faces:
        axis = max(range(3), key=lambda i: abs(center[i]))
        groups[["x", "y", "z"][axis]].append((face, center))
    return groups


def assign_x_tangential_h(fp, oBoundary, groups):
    tangent_faces = [face for face, _ in groups["y"] + groups["z"]]
    normal_faces = [face for face, _ in groups["x"]]
    log(fp, "x-normal faces: {}".format(normal_faces))
    log(fp, "x-tangential H faces: {}".format(tangent_faces))

    assigned = 0
    for face, center in groups["y"] + groups["z"]:
        origin = ["{}mm".format(center[0]), "{}mm".format(center[1]),
                  "{}mm".format(center[2])]
        upos = ["{}mm".format(center[0] + 10.0), "{}mm".format(center[1]),
                "{}mm".format(center[2])]
        result = safe(fp, "AssignTangentialHField face {}".format(face),
                      lambda face=face, origin=origin, upos=upos:
                      oBoundary.AssignTangentialHField([
                          "NAME:B0x_TH_{}".format(face),
                          "ComponentXReal:=", H0,
                          "ComponentYReal:=", "0",
                          ["NAME:CoordSysVector",
                           "Origin:=", origin, "UPos:=", upos],
                          "ReverseV:=", False,
                          "Faces:=", [face],
                      ]))
        if result is not None:
            assigned += 1

    if normal_faces:
        safe(fp, "AssignZeroTangentialHField x-normal faces",
             lambda: oBoundary.AssignZeroTangentialHField([
                 "NAME:B0x_open_flux_faces",
                 "Faces:=", normal_faces,
             ]))
    return assigned


def ensure_center_point(fp, oEditor):
    try:
        oEditor.GetObjectByName(POINT_NAME)
        log(fp, "{} already exists".format(POINT_NAME))
    except Exception:
        safe(fp, "create {}".format(POINT_NAME),
             lambda: oEditor.CreatePoint(
                 ["NAME:PointParameters",
                  "X:=", "0mm", "Y:=", "0mm", "Z:=", "0mm",
                  "PointType:=", "NonModel"],
                 ["NAME:Attributes",
                  "Name:=", POINT_NAME,
                  "Color:=", "(255 255 0)",
                  "PartCoordinateSystem:=", "Global"],
             ))


def eval_b_component(fields, key):
    op = {"Mag": "Mag", "Bx": "ScalarX", "By": "ScalarY", "Bz": "ScalarZ"}[key]
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp(op)
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_named_expr(fields, expr_name):
    fields.CalcStack("clear")
    fields.CopyNamedExprToStack(expr_name)
    fields.ClcEval(SOLN, [])
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def append_center_field(row):
    path = CENTER_FIELD_OUT
    exists = os.path.exists(path)
    mode = "ab" if exists else "wb"
    with open(path, mode) as f:
        writer = csv.DictWriter(f, fieldnames=CENTER_FIELD_FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in CENTER_FIELD_FIELDNAMES})


def append_intH2(row):
    path = INTH2_OUT
    exists = os.path.exists(path)
    mode = "ab" if exists else "wb"
    with open(path, mode) as f:
        writer = csv.DictWriter(f, fieldnames=INTH2_FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in INTH2_FIELDNAMES})


def export_center_field(fp, oDesign, case_id):
    fields = oDesign.GetModule("FieldsReporter")
    row = {
        "case_id": case_id,
        "field_dir": "x",
        "source_project": "",
        "status": "exported",
    }
    for comp, out_key in [
        ("Bx", "Bcenter_Bx_T"),
        ("By", "Bcenter_By_T"),
        ("Bz", "Bcenter_Bz_T"),
        ("Mag", "Bcenter_Mag_T"),
    ]:
        value = safe(fp, "eval Bcenter_{}".format(comp),
                     lambda c=comp: eval_b_component(fields, c))
        row[out_key] = "" if value is None else value
    return row


def export_intH2(fp, oDesign, case_id, layers):
    fields = oDesign.GetModule("FieldsReporter")
    row = {
        "case_id": case_id,
        "coil_dir": "x",
        "source_project": "",
        "status": "exported",
        "notes": "",
    }
    # IntH2_total
    for expr_name in ["IntH2_total", "IntH2_total_1"]:
        value = safe(fp, "eval IntH2_total via {}".format(expr_name),
                     lambda e=expr_name: eval_named_expr(fields, e))
        if value is not None and value != "":
            row["IntH2_total"] = value
            break

    # Per-layer IntH2 with legacy aliases (IntH2_total is NOT a valid L1 alias
    # for multilayer; L1=total only holds for single-layer cases)
    if layers == 1:
        legacy_aliases = {
            1: ["IntH2_L1", "IntH2_total", "IntH2_s1", "IntH2_cyl2", "InH2_s1"],
        }
    else:
        legacy_aliases = {
            1: ["IntH2_L1", "IntH2_s1", "IntH2_cyl2", "InH2_s1"],
            2: ["IntH2_L2", "IntH2_s2", "IntH2_cyl4", "InH2_s2"],
            3: ["IntH2_L3", "IntH2_s3", "InH2_s3"],
            4: ["IntH2_L4", "IntH2_s4", "InH2_s4"],
            5: ["IntH2_L5", "IntH2_s5"],
            6: ["IntH2_L6", "IntH2_s6"],
        }
    for layer_i in range(1, layers + 1):
        key = "IntH2_L{}".format(layer_i)
        candidates = legacy_aliases.get(layer_i, [key])
        found = False
        for expr_name in candidates:
            value = safe(fp, "eval {} via {}".format(key, expr_name),
                         lambda e=expr_name: eval_named_expr(fields, e))
            if value is not None and value != "":
                row[key] = value
                found = True
                break
        if not found:
            row[key] = ""
            log(fp, "  WARNING: no expression found for {}".format(key))

    return row


def process_case(fp, oDesktop, case_info):
    case_id = case_info["case_id"]
    project_file = case_info["project"]
    project_path = os.path.join(PROJECT_DIR, project_file)

    log(fp, "")
    log(fp, "=" * 70)
    log(fp, "Processing {}".format(case_id))
    log(fp, "Project: {}".format(project_path))

    if not os.path.exists(project_path):
        log(fp, "PROJECT MISSING: {}".format(project_path))
        return

    # ---- Remove stale lock file ----
    lock_path = project_path + ".lock"
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
            log(fp, "Removed stale lock: {}".format(lock_path))
        except Exception:
            log(fp, "Could not remove lock: {}".format(lock_path))

    # ---- Open project ----
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(project_path))
    if opened is None:
        log(fp, "SKIP {}: OpenProject failed".format(case_id))
        return

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        log(fp, "SKIP {}: GetActiveProject returned None".format(case_id))
        return

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    oBoundary = oDesign.GetModule("BoundarySetup")

    # ---- Remove old torus/current excitation ----
    delete_old_boundaries(fp, oBoundary)
    cleanup_geometry(fp, oEditor)

    # ---- Ensure ferrite is ferrite (not vacuum) ----
    ensure_ferrite_material(fp, oEditor)

    # ---- Apply per-layer mesh refinement ----
    clear_mesh_operations(fp, oDesign)
    layers = case_info.get("layers", 1)
    assign_ferrite_mesh(fp, oDesign, oEditor, case_id, layers)

    # ---- Apply x-directed tangential-H ----
    faces = face_centers(oEditor)
    log(fp, "Box1 faces: {}".format(faces))
    groups = classify_box_faces(faces)
    assigned_h_faces = assign_x_tangential_h(fp, oBoundary, groups)

    # ---- Ensure center point exists ----
    ensure_center_point(fp, oEditor)

    # ---- Validate and solve ----
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())

    if assigned_h_faces > 0:
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
    else:
        log(fp, "No tangential H boundaries assigned; skipping solve.")

    # ---- Export center field ----
    center_row = export_center_field(fp, oDesign, case_id)
    center_row["source_project"] = project_path
    log(fp, "Center field: {}".format(center_row))
    append_center_field(center_row)

    # ---- Export IntH2 ----
    layers = case_info.get("layers", 1)
    intH2_row = export_intH2(fp, oDesign, case_id, layers)
    intH2_row["source_project"] = project_path
    log(fp, "IntH2: {}".format(intH2_row))
    append_intH2(intH2_row)

    # ---- Save and close ----
    try:
        oProject.Save()
        log(fp, "Save project: OK")
    except Exception:
        log(fp, "Save project: FAILED")
    try:
        oDesktop.CloseProject(oProject.GetName())
        log(fp, "CloseProject: OK")
    except Exception:
        log(fp, "CloseProject: FAILED")


def run():
    ensure_dirs()

    # ---- Full rebuild: clear old CSV exports so we start fresh ----
    for csv_path in [CENTER_FIELD_OUT, INTH2_OUT]:
        if os.path.exists(csv_path):
            bak = csv_path + ".bak"
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(csv_path, bak)
    # ---- Also back up the old-mesh backups made manually ----
    # (center_field_raw_old_mesh.csv and intH2_layerwise_raw_old_mesh.csv
    #  are already safe from the manual cp step.)

    with open(LOG_PATH, "w") as fp:
        log(fp, "rebuild_shields_tangentialH {}".format(
            time.strftime("%Y-%m-%d %H:%M:%S")))
        log(fp, "Mesh: MESH_DIVISOR={} (MaxLength = a/{})".format(MESH_DIVISOR, MESH_DIVISOR))
        log(fp, "Cases: {}".format([c["case_id"] for c in CASES]))

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case_info in CASES:
            try:
                process_case(fp, oDesktop, case_info)
            except Exception:
                log(fp, "CASE FAILED: {}".format(case_info["case_id"]))
                log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "Done {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))


run()
