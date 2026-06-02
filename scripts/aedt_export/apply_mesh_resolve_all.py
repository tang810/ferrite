# -*- coding: utf-8 -*-
"""Apply per-layer mesh refinement to all 7 shield projects and re-solve.

This script assumes the projects already have correct x-directed tangential-H
boundary conditions (from rebuild_shields_tangentialH.py).  It only:
  1. Opens each project
  2. Clears old mesh operations
  3. Assigns LengthBased mesh (MaxLength = a / MESH_DIVISOR) per ferrite layer
  4. Validates and solves
  5. Exports center field + IntH2 data
  6. Saves and closes

IronPython 2.7 safe -- NO str.format() with precision specifiers.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
LOG_PATH = os.path.join(BASE_DIR, "logs", "apply_mesh_resolve.log")
CENTER_FIELD_OUT = os.path.join(BASE_DIR, "data", "raw", "center_field_raw.csv")
INTH2_OUT = os.path.join(BASE_DIR, "data", "raw", "intH2_layerwise_raw.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
B0_Bx_T = 1.2566e-06
MESH_DIVISOR = 3

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

CASES = [
    {"case_id": "C1_N1_t008_x", "project": "C1_N1_t008_shield.aedt", "layers": 1, "a_mm": 0.08},
    {"case_id": "C1_N1_t020_x", "project": "C1_N1_t020_shield.aedt", "layers": 1, "a_mm": 0.20},
    {"case_id": "C1_N1_t040_x", "project": "C1_N1_t040_shield.aedt", "layers": 1, "a_mm": 0.40},
    {"case_id": "C1_N1_t060_x", "project": "C1_N1_t060_shield.aedt", "layers": 1, "a_mm": 0.60},
    {"case_id": "C2_N2_t020_g010_x", "project": "C2_N2_t020_g010_shield.aedt", "layers": 2, "a_mm": 0.20},
    {"case_id": "C2_N3_t020_g010_x", "project": "C2_N3_t020_g010_shield.aedt", "layers": 3, "a_mm": 0.20},
    {"case_id": "C2_N4_t015_g008_x", "project": "C2_N4_t015_g008_shield.aedt", "layers": 4, "a_mm": 0.15},
]

CENTER_FIELDNAMES = [
    "case_id", "field_dir", "Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T",
    "Bcenter_Mag_T", "source_project", "status",
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


def fmt_float4(v):
    return "%.4f" % (float(v),)


def fmt_sci4(v):
    return "%.4e" % (float(v),)


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


def assign_ferrite_mesh(fp, oDesign, case_info):
    """Apply LengthBased mesh on ferrite layers. No existence check --
    pass hardcoded object names directly, as proven in mesh_conv_v2."""
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
                 "NAME:Length_surf_" + n,
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
                 "NAME:Length_vol_" + n,
                 "RefineInside:=", True,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))

    log(fp, "assigned mesh: a=" + fmt_float3(a_mm) + "mm MaxLength=" +
        max_len + " divisor=" + str(MESH_DIVISOR) + " objects=" + str(ferrite_objs))


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


def write_csv_header(fp_out, fieldnames):
    try:
        f = open(fp_out, "wb")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.close()
    except Exception:
        pass


def append_csv_row(fp_out, fieldnames, row):
    f = open(fp_out, "ab")
    try:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        out = {}
        for k in fieldnames:
            out[k] = row.get(k, "")
        writer.writerow(out)
    finally:
        f.close()


def process_case(fp, oDesktop, case_info):
    case_id = case_info["case_id"]
    project_file = case_info["project"]
    a_mm = case_info["a_mm"]
    layers = case_info["layers"]
    project_path = os.path.join(PROJECT_DIR, project_file)

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, "Processing " + case_id + " | layers=" + str(layers) +
        " | a=" + fmt_float3(a_mm) + "mm")

    if not os.path.exists(project_path):
        log(fp, "PROJECT MISSING: " + project_path)
        return

    # Remove stale lock
    lock_path = project_path + ".lock"
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
            log(fp, "removed lock: " + lock_path)
        except Exception:
            pass

    # Open
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(project_path))
    if opened is None:
        log(fp, "SKIP: OpenProject failed")
        return

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        log(fp, "SKIP: GetActiveProject None")
        return

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)

    # Apply mesh
    clear_mesh_operations(fp, oDesign)
    assign_ferrite_mesh(fp, oDesign, case_info)

    # Validate and solve
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    # Export center field
    fields = oDesign.GetModule("FieldsReporter")
    Bx = safe(fp, "eval Bcenter_Bx", lambda: eval_bx(fields))
    By = safe(fp, "eval Bcenter_By", lambda: eval_by(fields))
    Bz = safe(fp, "eval Bcenter_Bz", lambda: eval_bz(fields))
    Bmag = safe(fp, "eval Bcenter_Mag", lambda: eval_bmag(fields))

    center_row = {
        "case_id": case_id,
        "field_dir": "x",
        "Bcenter_Bx_T": Bx if Bx is not None else "",
        "Bcenter_By_T": By if By is not None else "",
        "Bcenter_Bz_T": Bz if Bz is not None else "",
        "Bcenter_Mag_T": Bmag if Bmag is not None else "",
        "source_project": project_path,
        "status": "exported" if Bx is not None else "failed",
    }

    SFx = ""
    if Bx is not None and Bx != "" and abs(Bx) > 1e-30:
        SFx = abs(B0_Bx_T) / abs(Bx)
    log(fp, "SFx=" + str(SFx))
    log(fp, "Center field: " + str(center_row))
    append_csv_row(CENTER_FIELD_OUT, CENTER_FIELDNAMES, center_row)

    # Export IntH2
    IntH2_total = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))
    intH2_row = {
        "case_id": case_id,
        "coil_dir": "x",
        "source_project": project_path,
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

    # Clear output CSVs
    for csv_path in [CENTER_FIELD_OUT, INTH2_OUT]:
        if os.path.exists(csv_path):
            bak = csv_path + ".bak"
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(csv_path, bak)

    write_csv_header(CENTER_FIELD_OUT, CENTER_FIELDNAMES)
    write_csv_header(INTH2_OUT, INTH2_FIELDNAMES)

    fp = open(LOG_PATH, "w")
    try:
        log(fp, "apply_mesh_resolve_all " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "MESH_DIVISOR=" + str(MESH_DIVISOR) + " (MaxLength = a/" + str(MESH_DIVISOR) + ")")
        log(fp, "Cases: " + str([c["case_id"] for c in CASES]))
        log(fp, "ALL str.format() FREE -- IronPython 2.7 safe")
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
