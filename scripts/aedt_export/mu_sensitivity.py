# -*- coding: utf-8 -*-
"""Permeability sensitivity study for selected multilayer cases.

Copies x-directed shield projects, changes mu_r of ferrite material,
applies mesh refinement, solves, and exports Bcenter + IntH2 data.

Cases: C2_N3_t020_g010_x and C2_N4_t015_g008_x
mu_r values: 500, 2000, 5000 (baseline 1000 is already in main dataset)

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
LOG_PATH = os.path.join(BASE_DIR, "logs", "mu_sensitivity.log")
CENTER_FIELD_OUT = os.path.join(BASE_DIR, "data", "raw", "center_field_raw.csv")
INTH2_OUT = os.path.join(BASE_DIR, "data", "raw", "intH2_layerwise_raw.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"
MESH_DIVISOR = 3

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

MU_VARIANTS = [
    {"mu_r": 500, "suffix": "mu500"},
    {"mu_r": 2000, "suffix": "mu2000"},
    {"mu_r": 5000, "suffix": "mu5000"},
]

CASES = [
    {"case_id": "C2_N3_t020_g010_x", "source_project": "C2_N3_t020_g010_shield.aedt", "layers": 3, "a_mm": 0.20},
    {"case_id": "C2_N4_t015_g008_x", "source_project": "C2_N4_t015_g008_shield.aedt", "layers": 4, "a_mm": 0.15},
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


def change_ferrite_mu(fp, oEditor, mu_r):
    """Change the relative permeability of all ferrite objects.

    In Maxwell, material properties are set via the material library.
    We create/adjust a material named 'ferrite_muXXX' with the target mu_r.
    """
    mat_name = "ferrite_mu" + str(mu_r)

    # Set all ferrite objects to use the new material
    for obj in FERRITE_OBJECTS:
        safe(fp, "set material " + obj + " -> " + mat_name,
             lambda o=obj, m=mat_name:
             oEditor.ChangeProperty([
                 "NAME:AllTabs",
                 ["NAME:Geometry3DAttributeTab",
                  ["NAME:PropServers", o],
                  ["NAME:ChangedProps",
                   ["NAME:Material", "Value:=", '"' + m + '"'],
                   ["NAME:Solve Inside", "Value:=", True]]],
             ]))

    log(fp, "changed ferrite material to " + mat_name + " (mu_r=" + str(mu_r) + ")")


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


def count_tangential_h_faces(oBoundary):
    count = 0
    try:
        for name in list(oBoundary.GetBoundaries()):
            if "TH_" in str(name):
                count = count + 1
    except Exception:
        return -1
    return count


def process_variant(fp, oDesktop, case_info, mu_r, suffix):
    case_id = case_info["case_id"]
    source_project = case_info["source_project"]
    layers = case_info["layers"]
    a_mm = case_info["a_mm"]
    mu_case_id = "MU_" + case_id + "_" + suffix
    source_path = os.path.join(PROJECT_DIR, source_project)

    mu_project_name = mu_case_id + "_shield.aedt"
    mu_project_path = os.path.join(PROJECT_DIR, mu_project_name)

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, "Processing " + mu_case_id + " | layers=" + str(layers) +
        " | a=" + fmt_float3(a_mm) + "mm | mu_r=" + str(mu_r))

    if not os.path.exists(source_path):
        log(fp, "SOURCE MISSING: " + source_path)
        return

    # Remove stale locks
    for p in [source_path, mu_project_path]:
        lock_path = p + ".lock"
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    # Remove old mu project if exists
    if os.path.exists(mu_project_path):
        try:
            os.remove(mu_project_path)
        except Exception:
            log(fp, "WARNING: could not remove old mu project")

    shutil.copy2(source_path, mu_project_path)
    log(fp, "copied " + source_project + " -> " + mu_project_name)

    # Open
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(mu_project_path))
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

    # Verify tangential-H boundaries exist
    th_count = count_tangential_h_faces(oBoundary)
    log(fp, "tangential-H faces: " + str(th_count))
    if th_count < 4:
        log(fp, "WARNING: fewer than 4 tangential-H faces, boundaries may be wrong")

    # Change ferrite mu_r
    change_ferrite_mu(fp, oEditor, mu_r)

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
        "case_id": mu_case_id,
        "field_dir": "x",
        "Bcenter_Bx_T": Bx if Bx is not None else "",
        "Bcenter_By_T": By if By is not None else "",
        "Bcenter_Bz_T": Bz if Bz is not None else "",
        "Bcenter_Mag_T": Bmag if Bmag is not None else "",
        "source_project": mu_project_path,
        "status": "exported" if Bx is not None else "failed",
    }

    SFx = ""
    if Bx is not None and Bx != "" and abs(Bx) > 1e-30:
        SFx = abs(1.2566e-06) / abs(Bx)
    log(fp, "SFx=" + str(SFx))
    log(fp, "Center field: " + str(center_row))
    append_csv_row(CENTER_FIELD_OUT, CENTER_FIELDNAMES, center_row)

    # Export IntH2
    IntH2_total = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))
    intH2_row = {
        "case_id": mu_case_id,
        "coil_dir": "x",
        "source_project": mu_project_path,
        "status": "exported" if IntH2_total is not None else "failed",
        "IntH2_total": IntH2_total if IntH2_total is not None else "",
        "notes": "mu_r=" + str(mu_r),
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
        log(fp, "mu_sensitivity " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "MESH_DIVISOR=" + str(MESH_DIVISOR))
        log(fp, "Cases: " + str([c["case_id"] for c in CASES]))
        log(fp, "mu_r variants: " + str([v["mu_r"] for v in MU_VARIANTS]))
        log(fp, "")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case_info in CASES:
            for variant in MU_VARIANTS:
                try:
                    process_variant(fp, oDesktop, case_info,
                                    variant["mu_r"], variant["suffix"])
                except Exception:
                    log(fp, "VARIANT FAILED: " + case_info["case_id"] +
                        " mu" + str(variant["mu_r"]))
                    log(fp, traceback.format_exc())

        log(fp, "")
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        fp.close()


run()
