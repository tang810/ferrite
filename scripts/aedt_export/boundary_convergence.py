# -*- coding: utf-8 -*-
"""Boundary convergence study -- vary Box1 size (2R/3R/5R).

Starting from the existing x-directed shield projects (which use an 800mm Box1,
i.e. ~4R half-extent), this script:
  1. Copies source project to work directory
  2. Deletes old Box1 + boundaries
  3. Creates new Box1 at target half-extent (200/300/500 mm)
  4. Re-applies x-directed tangential-H boundaries
  5. Applies mesh refinement (MESH_DIVISOR=3, medium)
  6. Solves and exports Bcenter + IntH2

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
LOG_PATH = os.path.join(BASE_DIR, "logs", "boundary_convergence.log")
OUT_CSV = os.path.join(BASE_DIR, "data", "validation", "boundary_convergence.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"
MESH_DIVISOR = 3
B0_Bx_T = 1.2566e-06

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

# R ~ 100 mm (outer radius of shield)
BOUNDARY_LEVELS = [
    ("2R", 200.0),
    ("3R", 300.0),
    ("5R", 500.0),
]

TARGET_CASES = [
    {"case_id": "C1_N1_t008_x", "source_project": "C1_N1_t008_shield.aedt",
     "layers": 1, "a_mm": 0.08},
    {"case_id": "C2_N4_t015_g008_x", "source_project": "C2_N4_t015_g008_shield.aedt",
     "layers": 4, "a_mm": 0.15},
]

FIELDNAMES = [
    "case_id", "boundary_level", "half_extent_mm",
    "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
    "Bcenter_Mag_T", "SFx", "IntH2_total",
    "source_project", "status",
]

INT_H2_NAMES = ["IntH2_total", "IntH2_total_1"]


def ensure_dirs():
    for p in [os.path.dirname(LOG_PATH), os.path.dirname(OUT_CSV)]:
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


def clear_all_mesh_ops_force(fp, oDesign, layers):
    """Force-delete all expected mesh ops by known names."""
    mesh_module = oDesign.GetModule("MeshSetup")
    ferrite_objs = FERRITE_OBJECTS[:layers]
    for obj_name in ferrite_objs:
        for prefix in ["Length_surf_bnd_", "Length_vol_bnd_",
                       "Length_surf_", "Length_vol_"]:
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
                 "NAME:Length_surf_bnd_" + n,
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
                 "NAME:Length_vol_bnd_" + n,
                 "RefineInside:=", True,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))

    log(fp, "assigned mesh: a=" + fmt_float3(a_mm) + "mm MaxLength=" +
        max_len + " divisor=" + str(MESH_DIVISOR) + " objects=" + str(ferrite_objs))


def delete_box1(fp, oEditor):
    """Delete existing Box1 and its children (will cascade to boundaries)."""
    safe(fp, "delete Box1", lambda: oEditor.Delete([
        "NAME:Selections", "Selections:=", "Box1",
    ]))
    log(fp, "deleted Box1")


def create_box1(fp, oEditor, half_ext_mm):
    """Create a new Box1 centered at origin with given half-extent."""
    he = float(half_ext_mm)
    pos_x = str(-he) + "mm"
    pos_y = str(-he) + "mm"
    pos_z = str(-he) + "mm"
    size_x = str(2.0 * he) + "mm"
    size_y = str(2.0 * he) + "mm"
    size_z = str(2.0 * he) + "mm"

    safe(fp, "create Box1 (" + str(2.0 * he) + "mm cube)",
         lambda: oEditor.CreateBox(
             ["NAME:BoxParameters",
              "XPosition:=", pos_x,
              "YPosition:=", pos_y,
              "ZPosition:=", pos_z,
              "XSize:=", size_x,
              "YSize:=", size_y,
              "ZSize:=", size_z],
             ["NAME:Attributes",
              "Name:=", "Box1",
              "Flags:=", "",
              "Color:=", "(143 175 143)",
              "Transparency:=", 0,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"vacuum"',
              "SolveInside:=", True,
              "ShellElement:=", False,
              "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              "UseMaterialAppearance:=", False,
              "IsLightweight:=", False,
              "IsAlwaysHidden:=", False,
              ]))
    log(fp, "created Box1: half-extent=" + str(he) + "mm (" +
        size_x + " x " + size_y + " x " + size_z + ")")


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
    assigned = 0
    for face, center in groups["y"] + groups["z"]:
        origin = [str(center[0]) + "mm", str(center[1]) + "mm",
                  str(center[2]) + "mm"]
        upos = [str(center[0] + 10.0) + "mm", str(center[1]) + "mm",
                str(center[2]) + "mm"]
        result = safe(fp, "AssignTangentialHField face " + str(face),
                      lambda face=face, origin=origin, upos=upos:
                      oBoundary.AssignTangentialHField([
                          "NAME:B0x_TH_" + str(face),
                          "ComponentXReal:=", H0,
                          "ComponentYReal:=", "0",
                          ["NAME:CoordSysVector",
                           "Origin:=", origin, "UPos:=", upos],
                          "ReverseV:=", False,
                          "Faces:=", [face],
                      ]))
        if result is not None:
            assigned += 1

    normal_faces = [face for face, _ in groups["x"]]
    if normal_faces:
        safe(fp, "AssignZeroTangentialHField x-normal faces",
             lambda: oBoundary.AssignZeroTangentialHField([
                 "NAME:B0x_open_flux_faces",
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


def append_csv(row):
    exists = os.path.exists(OUT_CSV)
    f = open(OUT_CSV, "ab" if exists else "wb")
    try:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        out = {}
        for k in FIELDNAMES:
            out[k] = row.get(k, "")
        writer.writerow(out)
    finally:
        f.close()


def process_level(fp, oDesktop, case_info, level_name, half_ext_mm):
    case_id = case_info["case_id"]
    source_project = case_info["source_project"]
    layers = case_info["layers"]
    a_mm = case_info["a_mm"]
    source_path = os.path.join(PROJECT_DIR, source_project)

    boundary_case_id = "BND_" + case_id + "_" + level_name
    work_project_name = boundary_case_id + ".aedt"
    work_project_path = os.path.join(PROJECT_DIR, work_project_name)

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, boundary_case_id + " | half_ext=" + str(half_ext_mm) + "mm | " +
        str(2.0 * half_ext_mm) + "mm cube")

    if not os.path.exists(source_path):
        log(fp, "SOURCE MISSING: " + source_path)
        return None

    # Remove stale lock
    for p in [source_path, work_project_path]:
        lock_path = p + ".lock"
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    # Remove old work project
    if os.path.exists(work_project_path):
        try:
            os.remove(work_project_path)
        except Exception:
            pass

    shutil.copy2(source_path, work_project_path)
    log(fp, "copied -> " + work_project_name)

    # Open
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(work_project_path))
    if opened is None:
        return None

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        return None

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oEditor = oDesign.SetActiveEditor("3D Modeler")
    oBoundary = oDesign.GetModule("BoundarySetup")

    # Delete old Box1 (boundaries auto-deleted since they reference Box1 faces)
    delete_box1(fp, oEditor)

    # Create new Box1 at target size
    create_box1(fp, oEditor, half_ext_mm)

    # Get face centers of new Box1 and classify
    faces = face_centers(oEditor)
    log(fp, "new Box1 faces: " + str(faces))
    groups = classify_box_faces(faces)

    # Apply x-directed tangential-H on new Box1
    assigned = assign_x_tangential_h(fp, oBoundary, groups)
    log(fp, "assigned " + str(assigned) + " tangential-H faces")

    # Apply mesh
    clear_all_mesh_ops_force(fp, oDesign, layers)
    assign_ferrite_mesh(fp, oDesign, case_info)

    # Validate and solve
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    # Export
    fields = oDesign.GetModule("FieldsReporter")
    Bx = safe(fp, "eval Bcenter_Bx", lambda: eval_bx(fields))
    By = safe(fp, "eval Bcenter_By", lambda: eval_by(fields))
    Bz = safe(fp, "eval Bcenter_Bz", lambda: eval_bz(fields))
    Bmag = safe(fp, "eval Bcenter_Mag", lambda: eval_bmag(fields))

    SFx = ""
    if Bx is not None and Bx != "" and abs(Bx) > 1e-30:
        SFx = abs(B0_Bx_T) / abs(Bx)

    IntH2 = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))

    row = {
        "case_id": boundary_case_id,
        "boundary_level": level_name,
        "half_extent_mm": half_ext_mm,
        "Bcenter_Bx_T": Bx if Bx is not None else "",
        "Bcenter_By_T": By if By is not None else "",
        "Bcenter_Bz_T": Bz if Bz is not None else "",
        "Bcenter_Mag_T": Bmag if Bmag is not None else "",
        "SFx": SFx,
        "IntH2_total": IntH2 if IntH2 is not None else "",
        "source_project": work_project_path,
        "status": "exported" if (SFx != "" and IntH2 is not None) else "failed",
    }

    log(fp, "SFx=" + str(SFx) + " IntH2=" + str(IntH2))
    append_csv(row)

    # Save and close
    try:
        oProject.Save()
    except Exception:
        pass
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass

    return row


def run():
    ensure_dirs()

    fp = open(LOG_PATH, "w")
    try:
        log(fp, "boundary_convergence " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "MESH_DIVISOR=" + str(MESH_DIVISOR) + " (medium mesh)")
        log(fp, "Boundary levels: " + str(BOUNDARY_LEVELS))
        log(fp, "Target cases: " + str([c["case_id"] for c in TARGET_CASES]))
        log(fp, "")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        all_rows = []
        for case_info in TARGET_CASES:
            for level_name, half_ext_mm in BOUNDARY_LEVELS:
                try:
                    row = process_level(fp, oDesktop, case_info, level_name, half_ext_mm)
                    if row is not None:
                        all_rows.append(row)
                except Exception:
                    log(fp, "LEVEL FAILED: " + case_info["case_id"] + " " + level_name)
                    log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "=" * 60)
        log(fp, "BOUNDARY CONVERGENCE SUMMARY")
        for row in all_rows:
            sfx = row["SFx"]
            ih2 = row["IntH2_total"]
            log(fp, "  " + str(row["case_id"]) + " | " +
                str(row["boundary_level"]) + " | SFx=" + str(sfx) +
                " | IntH2=" + str(ih2))

        log(fp, "")
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        fp.close()


run()
