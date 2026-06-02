# -*- coding: utf-8 -*-
"""Mesh convergence study for representative single-layer and multilayer cases.

Target cases:
  1. C1_N1_t008_x  -- thinnest single layer (a=0.08 mm), hardest to mesh
  2. C2_N4_t015_g008_x -- best-performing four-layer candidate (a=0.15 mm)

Three mesh levels per case:
  coarse : MaxLength = a       (1 element across thickness)
  medium : MaxLength = a/3     (3 elements across thickness)
  fine   : MaxLength = a/5     (5 elements across thickness)

SAFETY: Each case is copied to a temporary working directory before running.
         Original project files in round2_working/manufacturable_thin/ are
         NEVER modified.  The working copies live in data/mesh_study_work/
         and can be deleted after the study concludes.

For each level the script:
  1. Copies the original shield project to a working directory
  2. Opens the working copy
  3. Validates that x-directed tangential-H boundaries exist
  4. Deletes all existing mesh operations
  5. Applies per-layer LengthBased refinement at the target density
  6. Solves (magnetostatic, adaptive)
  7. Exports Bcenter_x, IntH2_total
  8. Computes SFx from B0 reference
  9. Closes

Output: data/validation/mesh_convergence.csv

Run in AEDT: Tools -> Run Script -> select this file.
"""

import csv
import math
import os
import shutil
import time
import traceback


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
ORIGINAL_PROJECT_DIR = os.path.join(BASE_DIR, "round2_working", "manufacturable_thin")
WORK_DIR = os.path.join(BASE_DIR, "data", "mesh_study_work")
LOG_PATH = os.path.join(BASE_DIR, "logs", "mesh_convergence.log")
OUT_CSV = os.path.join(BASE_DIR, "data", "validation", "mesh_convergence.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"

# ---- B0 reference value (from validated B0_reference_x) ----
B0_Bx_T = 1.2566e-06

# ---- Minimum x-tangential H faces expected ----
MIN_TANGENTIAL_H_FACES = 4  # 2 y-normal + 2 z-normal faces of Box1

# ---- Convergence study configuration ----
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
    "case_id",
    "mesh_level",
    "max_length_mm",
    "a_mm",
    "num_passes_est",
    "Bcenter_x_T",
    "SFx",
    "IntH2_total",
    "relative_change_SFx",
    "relative_change_IntH2",
    "status",
]

# ---- Helpers ----


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
        log(fp, "{}: OK{}".format(
            label, " -> " + str(value) if value is not None else ""))
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


def copy_project_tree(fp, src_project_name):
    """Copy a .aedt project and its companion .aedtresults folder to WORK_DIR.

    Returns the path to the working copy of the .aedt file, or None.
    """
    src_aedt = os.path.join(ORIGINAL_PROJECT_DIR, src_project_name)
    src_results = src_aedt + "results"
    dst_aedt = os.path.join(WORK_DIR, src_project_name)
    dst_results = dst_aedt + "results"

    if not os.path.exists(src_aedt):
        log(fp, "SOURCE MISSING: {}".format(src_aedt))
        return None

    # Remove stale work copy and lock
    for stale in [dst_aedt, dst_results, dst_aedt + ".lock"]:
        if os.path.exists(stale):
            try:
                if os.path.isdir(stale):
                    shutil.rmtree(stale)
                else:
                    os.remove(stale)
                log(fp, "removed stale: {}".format(stale))
            except Exception:
                log(fp, "could not remove stale: {}".format(stale))

    shutil.copy2(src_aedt, dst_aedt)
    log(fp, "copied {} -> {}".format(src_aedt, dst_aedt))

    if os.path.exists(src_results):
        try:
            shutil.copytree(src_results, dst_results)
            log(fp, "copied results folder")
        except Exception:
            log(fp, "copytree results failed (continuing anyway)")

    return dst_aedt


def count_tangential_h_faces(oBoundary):
    """Return the number of active x-directed tangential-H boundaries.

    We count boundaries whose name begins with 'B0x_TH_' (the naming
    convention used by assign_x_tangential_h in the rebuild script).
    """
    count = 0
    try:
        all_names = list(oBoundary.GetBoundaries())
        for name in all_names:
            if name.startswith("B0x_TH_"):
                count += 1
    except Exception:
        return -1
    return count


def clear_all_mesh_ops(fp, oDesign):
    """Delete every existing mesh operation so we start from a clean slate."""
    try:
        mesh_module = oDesign.GetModule("MeshSetup")
        existing = []
        try:
            existing = list(mesh_module.GetMeshOperations())
        except Exception:
            log(fp, "GetMeshOperations() not available; assuming empty")
        for name in existing:
            safe(fp, "delete mesh op [{}]".format(name),
                 lambda n=name: mesh_module.DeleteMeshOperations([n]))
        log(fp, "cleared {} mesh ops".format(len(existing)))
    except Exception:
        log(fp, "clear_all_mesh_ops: {}".format(traceback.format_exc()))


def apply_per_layer_mesh(fp, oDesign, case_info, divisor):
    """Apply LengthBased mesh refinement to every ferrite layer at the given density.

    Each layer gets two operations:
      - surface (RefineInside=false)
      - volume (RefineInside=true)

    MaxLength = a_mm / divisor.
    """
    a_mm = case_info["a_mm"]
    max_len = "{}mm".format(a_mm / divisor)
    ferrite_objs = case_info["ferrite_objects"][:case_info["layers"]]
    mesh_module = oDesign.GetModule("MeshSetup")

    for obj_name in ferrite_objs:
        # ---- surface ----
        safe(fp, "SURF {}".format(obj_name),
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
        # ---- volume ----
        safe(fp, "VOL  {}".format(obj_name),
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

    log(fp, "applied mesh: a=%.3fmm MaxLength=%s divisor=%d objects=%s" % (
        a_mm, max_len, divisor, str(ferrite_objs)))


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


def append_convergence_row(row):
    exists = os.path.exists(OUT_CSV)
    mode = "ab" if exists else "wb"
    with open(OUT_CSV, mode) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


# ---- Main processing ----


def process_one_level(fp, oDesktop, case_info, level_name, divisor):
    case_id = case_info["case_id"]
    project_file = case_info["project"]
    a_mm = case_info["a_mm"]

    log(fp, "")
    log(fp, "-" * 60)
    log(fp, "%s | level=%s | a=%.3fmm | MaxLength=%.4fmm" % (
        case_id, level_name, a_mm, a_mm / float(divisor)))

    # ---- Copy project to safe working directory ----
    work_path = copy_project_tree(fp, project_file)
    if work_path is None:
        return None

    # ---- Remove stale lock from work copy ----
    lock_path = work_path + ".lock"
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
        except Exception:
            pass

    # ---- Open work copy ----
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(work_path))
    if opened is None:
        log(fp, "SKIP: OpenProject failed")
        return None

    oProject = oDesktop.GetActiveProject()
    if oProject is None:
        return None

    oDesign = oProject.SetActiveDesign(DESIGN_NAME)

    # ---- Validate tangential-H boundaries ----
    oBoundary = oDesign.GetModule("BoundarySetup")
    th_count = count_tangential_h_faces(oBoundary)
    log(fp, "tangential-H faces found: {} (need >= {})".format(
        th_count, MIN_TANGENTIAL_H_FACES))
    if th_count < MIN_TANGENTIAL_H_FACES:
        log(fp, "WARNING: less than {} tangential-H faces. This project may "
               "not have been rebuilt with x-directed tangential-H. Results "
               "will be UNRELIABLE.".format(MIN_TANGENTIAL_H_FACES))

    # ---- Clear old mesh + apply new per-layer mesh ----
    clear_all_mesh_ops(fp, oDesign)
    apply_per_layer_mesh(fp, oDesign, case_info, divisor)

    # ---- Validate & solve ----
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))

    # ---- Export Bcenter_x ----
    fields = oDesign.GetModule("FieldsReporter")
    Bcenter_x = safe(fp, "eval Bcenter_x", lambda: eval_bx(fields))

    # ---- Export IntH2_total ----
    IntH2_total = safe(fp, "eval IntH2_total", lambda: eval_intH2_total(fields))

    # ---- Compute SFx ----
    SFx = ""
    if Bcenter_x is not None and Bcenter_x != "" and abs(Bcenter_x) > 1e-30:
        SFx = abs(B0_Bx_T) / abs(Bcenter_x)

    row = {
        "case_id": case_id,
        "mesh_level": level_name,
        "max_length_mm": round(a_mm / divisor, 6),
        "a_mm": a_mm,
        "num_passes_est": "",
        "Bcenter_x_T": Bcenter_x,
        "SFx": SFx,
        "IntH2_total": IntH2_total,
        "relative_change_SFx": "",
        "relative_change_IntH2": "",
        "status": "exported" if (SFx != "" and IntH2_total is not None) else "failed",
    }
    ih2_display = float(IntH2_total) if IntH2_total else -1.0
    log(fp, "Result: SFx=%s, IntH2_total=%.4e" % (str(SFx), ih2_display))

    # ---- Close work copy (do NOT save -- keep original pristine) ----
    try:
        oDesktop.CloseProject(oProject.GetName())
        log(fp, "CloseProject: OK")
    except Exception:
        log(fp, "CloseProject: FAILED")

    return row


def compute_relative_changes(rows):
    """Fill relative_change columns using the coarsest level as reference."""
    for case_id in sorted(set(r["case_id"] for r in rows if r)):
        case_rows = [r for r in rows if r["case_id"] == case_id]
        case_rows.sort(key=lambda r: [l for l, _ in MESH_LEVELS].index(r["mesh_level"]))
        ref = case_rows[0]
        ref_sfx = ref["SFx"]
        ref_h2 = ref["IntH2_total"]
        for r in case_rows:
            if ref_sfx and r["SFx"] and ref_sfx != 0:
                rel = (r["SFx"] - ref_sfx) / ref_sfx
                r["relative_change_SFx"] = round(rel, 8)
            if ref_h2 and r["IntH2_total"] and ref_h2 != 0:
                rel = (r["IntH2_total"] - ref_h2) / ref_h2
                r["relative_change_IntH2"] = round(rel, 8)


def run():
    ensure_dirs()

    with open(LOG_PATH, "w") as fp:
        log(fp, "mesh_convergence {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        log(fp, "Target cases: {}".format([c["case_id"] for c in TARGET_CASES]))
        log(fp, "Mesh levels: {}".format(MESH_LEVELS))
        log(fp, "Working directory (copies): {}".format(WORK_DIR))
        log(fp, "Original projects are NOT modified.")
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
                        append_convergence_row(row)
                except Exception:
                    log(fp, "LEVEL FAILED: {} {}".format(
                        case_info["case_id"], level_name))
                    log(fp, traceback.format_exc())

        # ---- Compute relative changes ----
        compute_relative_changes(all_rows)

        # ---- Rewrite CSV with relative-change columns populated ----
        if os.path.exists(OUT_CSV):
            os.remove(OUT_CSV)
        for row in all_rows:
            append_convergence_row(row)

        # ---- Summary ----
        log(fp, "")
        log(fp, "=" * 60)
        log(fp, "CONVERGENCE SUMMARY")
        log(fp, "Relative changes computed against coarsest level per case.")
        for row in all_rows:
            d_sfx = float(row.get("relative_change_SFx") or 0.0) * 100.0
            d_h2 = float(row.get("relative_change_IntH2") or 0.0) * 100.0
            sfx_v = float(row["SFx"]) if row["SFx"] != "" else 0.0
            ih2_v = float(row["IntH2_total"]) if row["IntH2_total"] else 0.0
            log(fp, "  %-22s | %-6s | SFx=%.4f | dSFx=%+.4f%% | IntH2=%.4e | dIntH2=%+.2f%%" % (
                str(row["case_id"]), str(row["mesh_level"]),
                sfx_v, d_sfx, ih2_v, d_h2))

        log(fp, "")
        log(fp, "Done {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))


run()
