# -*- coding: utf-8 -*-
"""Mesh convergence study v2 -- IronPython 2.7 safe version.

NO str.format() with precision specifiers anywhere.
All logging uses plain %s with explicit float formatting beforehand.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
ORIGINAL_PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
WORK_DIR = os.path.join(BASE_DIR, "data", "mesh_study_work")
LOG_PATH = os.path.join(BASE_DIR, "logs", "mesh_convergence.log")
OUT_CSV = os.path.join(BASE_DIR, "data", "validation", "mesh_convergence.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
B0_Bx_T = 1.2566e-06
MIN_TANGENTIAL_H_FACES = 4

MESH_LEVELS = [
    ("coarse", 1),
    ("medium", 3),
    ("fine",   5),
]

TARGET_CASES = [
    {
        "case_id": "C1_N1_t008_x",
        "project": "C1_N1_t008_shield.aedt",
        "layers": 1,
        "a_mm": 0.08,
        "ferrite_objects": ["Cylinder2"],
    },
    {
        "case_id": "C2_N4_t015_g008_x",
        "project": "C2_N4_t015_g008_shield.aedt",
        "layers": 4,
        "a_mm": 0.15,
        "ferrite_objects": ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"],
    },
]

FIELDNAMES = [
    "case_id", "mesh_level", "max_length_mm", "a_mm",
    "Bcenter_x_T", "SFx", "IntH2_total",
    "relative_change_SFx", "relative_change_IntH2", "status",
]


def ensure_dirs():
    for p in [os.path.dirname(LOG_PATH), os.path.dirname(OUT_CSV), WORK_DIR]:
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
    """Return '%.3f' % v, safe for any numeric type."""
    return "%.3f" % (float(v),)


def fmt_float4(v):
    return "%.4f" % (float(v),)


def fmt_sci4(v):
    return "%.4e" % (float(v),)


def copy_project_tree(fp, src_project_name):
    src_aedt = os.path.join(ORIGINAL_PROJECT_DIR, src_project_name)
    src_results = src_aedt + "results"
    dst_aedt = os.path.join(WORK_DIR, src_project_name)
    dst_results = dst_aedt + "results"

    if not os.path.exists(src_aedt):
        log(fp, "SOURCE MISSING: " + src_aedt)
        return None

    for stale in [dst_aedt, dst_results, dst_aedt + ".lock"]:
        if os.path.exists(stale):
            try:
                if os.path.isdir(stale):
                    shutil.rmtree(stale)
                else:
                    os.remove(stale)
                log(fp, "removed stale: " + stale)
            except Exception:
                log(fp, "could not remove stale: " + stale)

    shutil.copy2(src_aedt, dst_aedt)
    log(fp, "copied " + src_aedt + " -> " + dst_aedt)

    if os.path.exists(src_results):
        try:
            shutil.copytree(src_results, dst_results)
            log(fp, "copied results folder")
        except Exception:
            log(fp, "copytree results failed (continuing anyway)")

    return dst_aedt


def count_tangential_h_faces(oBoundary):
    count = 0
    try:
        all_names = list(oBoundary.GetBoundaries())
        for name in all_names:
            if name.startswith("B0x_TH_"):
                count = count + 1
    except Exception:
        return -1
    return count


def clear_all_mesh_ops(fp, oDesign):
    try:
        mesh_module = oDesign.GetModule("MeshSetup")
        existing = []
        try:
            existing = list(mesh_module.GetMeshOperations())
        except Exception:
            log(fp, "GetMeshOperations() not available; assuming empty")
        for name in existing:
            safe(fp, "delete mesh op [" + str(name) + "]",
                 lambda n=name: mesh_module.DeleteMeshOperations([n]))
        log(fp, "cleared " + str(len(existing)) + " mesh ops")
    except Exception:
        log(fp, "clear_all_mesh_ops: " + traceback.format_exc())


def apply_per_layer_mesh(fp, oDesign, case_info, divisor):
    a_mm = case_info["a_mm"]
    max_len = str(a_mm / divisor) + "mm"
    ferrite_objs = case_info["ferrite_objects"][:case_info["layers"]]
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

    log(fp, "applied mesh: a=" + fmt_float3(a_mm) + "mm MaxLength=" +
        max_len + " divisor=" + str(divisor) + " objects=" + str(ferrite_objs))


def eval_bx(fields):
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarX")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def eval_intH2_total(fields):
    for name in ["IntH2_total", "IntH2_total_1"]:
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
    mode = "ab" if exists else "wb"
    f = open(OUT_CSV, mode)
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


def process_one_level(fp, oDesktop, case_info, level_name, divisor):
    case_id = case_info["case_id"]
    project_file = case_info["project"]
    a_mm = case_info["a_mm"]
    ml_mm = a_mm / float(divisor)

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, case_id + " | level=" + level_name + " | a=" +
        fmt_float3(a_mm) + "mm | MaxLength=" + fmt_float4(ml_mm) + "mm")

    work_path = copy_project_tree(fp, project_file)
    if work_path is None:
        return None

    lock_path = work_path + ".lock"
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
        except Exception:
            pass

    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(work_path))
    if opened is None:
        log(fp, "SKIP: OpenProject failed")
        return None

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        return None

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)
    oBoundary = oDesign.GetModule("BoundarySetup")
    th_count = count_tangential_h_faces(oBoundary)
    log(fp, "tangential-H faces found: " + str(th_count) +
        " (need >= " + str(MIN_TANGENTIAL_H_FACES) + ")")
    if th_count < MIN_TANGENTIAL_H_FACES:
        log(fp, "WARNING: project may not have x-directed tangential-H boundaries")

    clear_all_mesh_ops(fp, oDesign)
    apply_per_layer_mesh(fp, oDesign, case_info, divisor)

    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    fields = oDesign.GetModule("FieldsReporter")
    Bcenter_x = safe(fp, "eval Bcenter_x", lambda: eval_bx(fields))
    IntH2_total = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))

    SFx = ""
    if Bcenter_x is not None and Bcenter_x != "":
        try:
            if abs(Bcenter_x) > 1e-30:
                SFx = abs(B0_Bx_T) / abs(Bcenter_x)
        except Exception:
            pass

    row = {
        "case_id": case_id,
        "mesh_level": level_name,
        "max_length_mm": ml_mm,
        "a_mm": a_mm,
        "Bcenter_x_T": Bcenter_x,
        "SFx": SFx,
        "IntH2_total": IntH2_total,
        "relative_change_SFx": "",
        "relative_change_IntH2": "",
        "status": "exported" if (SFx != "" and IntH2_total is not None) else "failed",
    }

    ih2_disp = float(IntH2_total) if IntH2_total is not None and IntH2_total != "" else -1.0
    log(fp, "Result: SFx=" + str(SFx) + " IntH2=" + fmt_sci4(ih2_disp))

    try:
        oDesktop.CloseProject(oProject.GetName())
        log(fp, "CloseProject: OK")
    except Exception:
        log(fp, "CloseProject: FAILED")

    return row


def compute_relative_changes(rows):
    for case_id in sorted(set(r["case_id"] for r in rows if r)):
        case_rows = [r for r in rows if r["case_id"] == case_id]
        case_rows.sort(key=lambda r: [l for l, _ in MESH_LEVELS].index(r["mesh_level"]))
        ref = case_rows[0]
        ref_sfx = ref["SFx"]
        ref_h2 = ref["IntH2_total"]
        for r in case_rows:
            if ref_sfx and r["SFx"] and ref_sfx != 0:
                rel = (float(r["SFx"]) - float(ref_sfx)) / float(ref_sfx)
                r["relative_change_SFx"] = rel
            if ref_h2 and r["IntH2_total"] and ref_h2 != 0:
                rel = (float(r["IntH2_total"]) - float(ref_h2)) / float(ref_h2)
                r["relative_change_IntH2"] = rel


def run():
    ensure_dirs()

    fp = open(LOG_PATH, "w")
    try:
        log(fp, "mesh_convergence v2 " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "Target: " + str([c["case_id"] for c in TARGET_CASES]))
        log(fp, "Levels: " + str(MESH_LEVELS))
        log(fp, "Work dir: " + WORK_DIR)
        log(fp, "ALL FORMAT STRINGS REMOVED -- IronPython 2.7 safe")
        log(fp, "")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        all_rows = []
        for case_info in TARGET_CASES:
            for level_name, divisor in MESH_LEVELS:
                try:
                    row = process_one_level(fp, oDesktop, case_info, level_name, divisor)
                    if row is not None:
                        all_rows.append(row)
                        append_csv(row)
                except Exception:
                    log(fp, "LEVEL FAILED: " + case_info["case_id"] + " " + level_name)
                    log(fp, traceback.format_exc())

        compute_relative_changes(all_rows)

        if os.path.exists(OUT_CSV):
            os.remove(OUT_CSV)
        for row in all_rows:
            append_csv(row)

        log(fp, "")
        log(fp, "=" * 60)
        log(fp, "CONVERGENCE SUMMARY")
        for row in all_rows:
            ds = row.get("relative_change_SFx")
            dh = row.get("relative_change_IntH2")
            ds_pct = float(ds) * 100.0 if ds is not None and ds != "" else 0.0
            dh_pct = float(dh) * 100.0 if dh is not None and dh != "" else 0.0
            sfx_s = "%.4f" % (float(row["SFx"]),) if row["SFx"] != "" else "N/A"
            ih2_s = "%.4e" % (float(row["IntH2_total"]),) if row["IntH2_total"] and row["IntH2_total"] != "" else "N/A"
            ds_s = "%.4f" % (ds_pct,)
            dh_s = "%.2f" % (dh_pct,)
            log(fp, "  " + str(row["case_id"]) + " | " + str(row["mesh_level"]) +
                " | SFx=" + sfx_s + " | dSFx=" + ds_s + "% | IntH2=" + ih2_s +
                " | dIntH2=" + dh_s + "%")

        log(fp, "")
        log(fp, "Done " + time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        fp.close()


run()
