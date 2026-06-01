# -*- coding: utf-8 -*-
"""Build z-directed shielded cases from x-directed templates.

Copies selected x-directed shield projects, changes tangential-H boundaries
from x-directed to z-directed, applies mesh refinement, solves, and exports
Bcenter + IntH2 data.

z-directed tangential-H:
  - Tangential-H on x/y faces of Box1 (H0=1 A/m, z-directed)
  - Zero tangential-H on z faces (open flux boundary)

IronPython 2.7 safe -- NO str.format() with precision specifiers.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
LOG_PATH = os.path.join(BASE_DIR, "logs", "rebuild_z_shields.log")
CENTER_FIELD_OUT = os.path.join(BASE_DIR, "data", "raw", "center_field_raw.csv")
INTH2_OUT = os.path.join(BASE_DIR, "data", "raw", "intH2_layerwise_raw.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"
MESH_DIVISOR = 3

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

CASES = [
    {"case_id": "C1_N1_t060_z", "source_project": "C1_N1_t060_shield.aedt", "layers": 1, "a_mm": 0.60},
    {"case_id": "C2_N3_t020_g010_z", "source_project": "C2_N3_t020_g010_shield.aedt", "layers": 3, "a_mm": 0.20},
    {"case_id": "C2_N4_t015_g008_z", "source_project": "C2_N4_t015_g008_shield.aedt", "layers": 4, "a_mm": 0.15},
]

CENTER_FIELDNAMES = [
    "case_id", "field_dir", "Bcenter_Bx_T", "Bcenter_By_T",
    "Bcenter_Bz_T", "Bcenter_Mag_T", "source_project", "status",
]

INTH2_FIELDNAMES = [
    "case_id", "coil_dir", "source_project", "status",
    "IntH2_total", "IntH2_L1", "IntH2_L2", "IntH2_L3",
    "IntH2_L4", "IntH2_L5", "IntH2_L6", "notes",
]

INT_H2_NAMES = ["IntH2_total", "IntH2_total_1"]
INT_H2_PER_LAYER_FALLBACKS = {
    1: ["IntH2_L1", "IntH2_s1", "InH2_s1"],
    2: ["IntH2_L2", "IntH2_s2", "InH2_s2"],
    3: ["IntH2_L3", "IntH2_s3", "InH2_s3"],
    4: ["IntH2_L4", "IntH2_s4", "InH2_s4"],
    5: ["IntH2_L5", "IntH2_s5"],
    6: ["IntH2_L6", "IntH2_s6"],
}


def ensure_dirs():
    for p in [os.path.dirname(LOG_PATH), os.path.dirname(CENTER_FIELD_OUT)]:
        if not os.path.isdir(p):
            os.makedirs(p)


def log(fp, msg):
    fp.write(str(msg) + "\n")
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


def fmt_float3(v):
    return "%.3f" % (float(v),)


def clear_all_boundaries(fp, oBoundary):
    """Delete all existing excitation and boundary operations."""
    names = []
    for getter in ["GetExcitations", "GetBoundaries"]:
        try:
            values = getattr(oBoundary, getter)()
            if values:
                names.extend(list(values))
        except Exception:
            pass
    for name in names:
        safe(fp, "delete boundary " + str(name),
             lambda n=name: oBoundary.DeleteBoundaries([n]))
    log(fp, "cleared " + str(len(names)) + " boundary/excitations")


def clear_mesh_operations(fp, oDesign):
    try:
        mesh_module = oDesign.GetModule("MeshSetup")
        existing = []
        try:
            existing = list(mesh_module.GetMeshOperations())
        except Exception:
            pass
        for name in existing:
            safe(fp, "delete mesh op " + str(name),
                 lambda n=name: mesh_module.DeleteMeshOperations([n]))
        log(fp, "cleared " + str(len(existing)) + " mesh ops")
    except Exception:
        log(fp, "clear_mesh_operations: " + traceback.format_exc())


def clear_all_mesh_ops_force(fp, oDesign, layers):
    """Force-delete all expected mesh ops by their known names (z prefix)."""
    mesh_module = oDesign.GetModule("MeshSetup")
    ferrite_objs = FERRITE_OBJECTS[:layers]
    for obj_name in ferrite_objs:
        for prefix in ["Length_surf_z_", "Length_vol_z_"]:
            try:
                mesh_module.DeleteMeshOperations([prefix + obj_name])
            except Exception:
                pass
    # Also try the unprefixed names (from original project)
    for obj_name in ferrite_objs:
        for prefix in ["Length_surf_", "Length_vol_"]:
            try:
                mesh_module.DeleteMeshOperations([prefix + obj_name])
            except Exception:
                pass


def assign_ferrite_mesh(fp, oDesign, case_info):
    a_mm = case_info["a_mm"]
    layers = case_info["layers"]
    max_len_mm = a_mm / float(MESH_DIVISOR)
    max_len = str(max_len_mm) + "mm"
    ferrite_objs = FERRITE_OBJECTS[:layers]

    mesh_module = oDesign.GetModule("MeshSetup")
    for obj_name in ferrite_objs:
        safe(fp, "SURF " + obj_name,
             lambda n=obj_name, ml=max_len:
             mesh_module.AssignLengthOp([
                 "NAME:Length_surf_z_" + n,
                 "RefineInside:=", False,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))
        safe(fp, "VOL  " + obj_name,
             lambda n=obj_name, ml=max_len:
             mesh_module.AssignLengthOp([
                 "NAME:Length_vol_z_" + n,
                 "RefineInside:=", True,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))

    log(fp, "assigned mesh: a=" + fmt_float3(a_mm) + "mm MaxLength=" +
        max_len + " divisor=" + str(MESH_DIVISOR) + " objects=" + str(ferrite_objs))


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


def assign_z_tangential_h(fp, oBoundary, groups):
    """Apply z-directed tangential-H: tangential-H on x/y faces, zero on z faces."""
    tangent_faces = [face for face, _ in groups["x"] + groups["y"]]
    normal_faces = [face for face, _ in groups["z"]]
    log(fp, "z-normal faces (open flux): " + str(normal_faces))
    log(fp, "z-tangential H faces: " + str(tangent_faces))

    assigned = 0
    for face, center in groups["x"] + groups["y"]:
        origin = [str(center[0]) + "mm", str(center[1]) + "mm",
                  str(center[2]) + "mm"]
        upos = [str(center[0]) + "mm", str(center[1]) + "mm",
                str(center[2] + 10.0) + "mm"]
        result = safe(fp, "AssignTangentialHField_z face " + str(face),
                      lambda face=face, origin=origin, upos=upos:
                      oBoundary.AssignTangentialHField([
                          "NAME:B0z_TH_" + str(face),
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
        safe(fp, "AssignZeroTangentialHField z-normal faces",
             lambda: oBoundary.AssignZeroTangentialHField([
                 "NAME:B0z_open_flux_faces",
                 "Faces:=", normal_faces,
             ]))
    return assigned


def eval_bx(fields):
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarX")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_by(fields):
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarY")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_bz(fields):
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarZ")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_bmag(fields):
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ComplexMag")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_intH2_total(fields):
    for name in INT_H2_NAMES:
        try:
            fields.CalcStack("clear")
            fields.CopyNamedExprToStack(name)
            fields.ClcEval(SOLN, [])
            v = extract_value(fields.GetTopEntryValue(SOLN, []))
            if v is not None and v != "":
                return v
        except Exception:
            continue
    return None


def eval_intH2_layer(fields, layer_i):
    names = INT_H2_PER_LAYER_FALLBACKS.get(layer_i, [])
    for name in names:
        try:
            fields.CalcStack("clear")
            fields.CopyNamedExprToStack(name)
            fields.ClcEval(SOLN, [])
            v = extract_value(fields.GetTopEntryValue(SOLN, []))
            if v is not None and v != "":
                return v
        except Exception:
            continue
    return None


def append_csv_row(fp_out, fieldnames, row):
    exists = os.path.exists(fp_out)
    f = open(fp_out, "ab" if exists else "wb")
    try:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        out = {}
        for k in fieldnames:
            out[k] = row.get(k, "")
        writer.writerow(out)
    finally:
        f.close()


def process_case(fp, oDesktop, case_info):
    case_id = case_info["case_id"]
    source_project = case_info["source_project"]
    layers = case_info["layers"]
    a_mm = case_info["a_mm"]
    source_path = os.path.join(PROJECT_DIR, source_project)

    # Copy to new z-directed project
    z_project_name = case_id + "_shield.aedt"
    z_project_path = os.path.join(PROJECT_DIR, z_project_name)

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, "Processing " + case_id + " | layers=" + str(layers) +
        " | a=" + fmt_float3(a_mm) + "mm")
    log(fp, "Copy: " + source_path + " -> " + z_project_path)

    if not os.path.exists(source_path):
        log(fp, "SOURCE MISSING: " + source_path)
        return

    # Remove stale lock
    for p in [source_path, z_project_path]:
        lock_path = p + ".lock"
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    # Remove old z project if exists
    if os.path.exists(z_project_path):
        try:
            os.remove(z_project_path)
        except Exception:
            log(fp, "WARNING: could not remove old z project")

    shutil.copy2(source_path, z_project_path)
    log(fp, "copied project file")

    # Open z project
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(z_project_path))
    if opened is None:
        log(fp, "SKIP: OpenProject failed")
        return

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        log(fp, "SKIP: GetActiveProject None")
        return

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    oBoundary = oDesign.GetModule("BoundarySetup")

    # Delete all existing boundaries (x-directed)
    clear_all_boundaries(fp, oBoundary)

    # Apply z-directed tangential-H
    faces = face_centers(oEditor)
    log(fp, "Box1 faces: " + str(faces))
    groups = classify_box_faces(faces)
    assigned_h_faces = assign_z_tangential_h(fp, oBoundary, groups)

    # Apply mesh
    clear_all_mesh_ops_force(fp, oDesign, layers)
    assign_ferrite_mesh(fp, oDesign, case_info)

    # Validate and solve
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())

    if assigned_h_faces > 0:
        safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
    else:
        log(fp, "No tangential H boundaries assigned; skipping solve.")
        return

    # Export center field
    fields = oDesign.GetModule("FieldsReporter")
    Bx = safe(fp, "eval Bcenter_Bx", lambda: eval_bx(fields))
    By = safe(fp, "eval Bcenter_By", lambda: eval_by(fields))
    Bz = safe(fp, "eval Bcenter_Bz", lambda: eval_bz(fields))
    Bmag = safe(fp, "eval Bcenter_Mag", lambda: eval_bmag(fields))

    center_row = {
        "case_id": case_id,
        "field_dir": "z",
        "Bcenter_Bx_T": Bx if Bx is not None else "",
        "Bcenter_By_T": By if By is not None else "",
        "Bcenter_Bz_T": Bz if Bz is not None else "",
        "Bcenter_Mag_T": Bmag if Bmag is not None else "",
        "source_project": z_project_path,
        "status": "exported" if Bz is not None else "failed",
    }

    SFz = ""
    if Bz is not None and Bz != "" and abs(Bz) > 1e-30:
        SFz = abs(1.2566e-06) / abs(Bz)
    log(fp, "SFz=" + str(SFz))
    log(fp, "Center field: " + str(center_row))
    append_csv_row(CENTER_FIELD_OUT, CENTER_FIELDNAMES, center_row)

    # Export IntH2
    IntH2_total = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))
    intH2_row = {
        "case_id": case_id,
        "coil_dir": "z",
        "source_project": z_project_path,
        "status": "exported" if IntH2_total is not None else "failed",
        "IntH2_total": IntH2_total if IntH2_total is not None else "",
        "notes": "",
    }
    for layer_i in range(1, layers + 1):
        key = "IntH2_L" + str(layer_i)
        val = safe(fp, "eval " + key, lambda li=layer_i: eval_intH2_layer(fields, li))
        intH2_row[key] = val if val is not None else ""
    for layer_i in range(layers + 1, 7):
        intH2_row["IntH2_L" + str(layer_i)] = ""

    log(fp, "IntH2: " + str(intH2_row))
    append_csv_row(INTH2_OUT, INTH2_FIELDNAMES, intH2_row)

    # Save and close
    try:
        oProject.Save()
        log(fp, "Save: OK")
    except Exception:
        log(fp, "Save: FAILED")
    try:
        oDesktop.CloseProject(oProject.GetName())
        log(fp, "CloseProject: OK")
    except Exception:
        log(fp, "CloseProject: FAILED")


def run():
    ensure_dirs()

    fp = open(LOG_PATH, "w")
    try:
        log(fp, "rebuild_z_shields " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "MESH_DIVISOR=" + str(MESH_DIVISOR))
        log(fp, "Cases: " + str([c["case_id"] for c in CASES]))
        log(fp, "")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case_info in CASES:
            try:
                process_case(fp, oDesktop, case_info)
            except Exception:
                log(fp, "CASE FAILED: " + case_info["case_id"])
                log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        fp.close()


run()
