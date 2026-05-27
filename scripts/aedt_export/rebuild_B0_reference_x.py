# -*- coding: utf-8 -*-
"""Rebuild and validate the clean x-directed B0 reference in AEDT.

中文说明：
本脚本只处理 `B0_reference_x`。它复制已有单层 shield 工程作为几何模板，
删除旧的 torus/current 外场近似，将 ferrite 设置为 vacuum，并在空气盒外表面
施加 x-directed tangential H-field boundary。脚本求解后只导出
`data/raw/B0_reference_x.csv`，不会导出任何 shielded case。
"""

import csv
import math
import os
import shutil
import time
import traceback


ROOT = r"D:\tangyumengnew\aaaaaaaaximukeji"
TEMPLATE_PROJECT = os.path.join(ROOT, "round2_working", "manufacturable_thin", "C1_N1_t008_shield.aedt")
OUT_PROJECT = os.path.join(ROOT, "aedt", "reference", "B0_reference_x.aedt")
OUT_CSV = os.path.join(ROOT, "data", "raw", "B0_reference_x.csv")
LOG_PATH = os.path.join(ROOT, "logs", "rebuild_B0_reference_x.log")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"

FERRITE_OBJECTS = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]
EXTERNAL_FIELD_OBJECTS = [
    "Torus2",
    "Torus3",
    "Torus2_Section1",
    "Torus3_Section1",
    "Torus2_Section1_Separate1",
    "Torus3_Section1_Separate1",
    "Iext_plus_sheet",
    "Iext_minus_sheet",
    "Iext_plus_sheet_1",
    "Iext_minus_sheet_1",
]


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        value = fn()
        log(fp, "{}: OK{}".format(label, (" -> " + str(value)) if value is not None else ""))
        return True if value is None else value
    except Exception:
        log(fp, "{}: FAILED".format(label))
        log(fp, traceback.format_exc())
        return None


def ensure_dirs():
    for path in [os.path.dirname(OUT_PROJECT), os.path.dirname(OUT_CSV), os.path.dirname(LOG_PATH)]:
        if not os.path.isdir(path):
            os.makedirs(path)


def fresh_project_copy(fp):
    for path in [OUT_PROJECT, OUT_PROJECT + ".lock"]:
        if os.path.exists(path):
            os.remove(path)
    results_dir = OUT_PROJECT + "results"
    if os.path.isdir(results_dir):
        shutil.rmtree(results_dir)
    shutil.copy2(TEMPLATE_PROJECT, OUT_PROJECT)
    log(fp, "Copied template to {}".format(OUT_PROJECT))


def delete_old_boundaries(fp, oBoundary):
    names = []
    for getter in ["GetExcitations", "GetBoundaries"]:
        try:
            values = getattr(oBoundary, getter)()
            if values:
                names.extend(list(values))
        except Exception as exc:
            log(fp, "{} unavailable: {}".format(getter, str(exc)[:160]))
    for name in sorted(set(names + ["Iext_plus", "Iext_minus", "Current1", "Current2"])):
        safe(fp, "delete boundary {}".format(name), lambda n=name: oBoundary.DeleteBoundaries([n]))


def cleanup_geometry(fp, oEditor):
    for obj in EXTERNAL_FIELD_OBJECTS:
        safe(fp, "delete external-field object {}".format(obj), lambda o=obj: oEditor.Delete([
            "NAME:Selections",
            "Selections:=", o,
        ]))

    for obj in FERRITE_OBJECTS:
        safe(fp, "{} -> vacuum".format(obj), lambda o=obj: oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DAttributeTab",
             ["NAME:PropServers", o],
             ["NAME:ChangedProps",
              ["NAME:Material", "Value:=", '"vacuum"'],
              ["NAME:Solve Inside", "Value:=", True]]],
        ]))


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
        origin = ["{}mm".format(center[0]), "{}mm".format(center[1]), "{}mm".format(center[2])]
        upos = ["{}mm".format(center[0] + 10.0), "{}mm".format(center[1]), "{}mm".format(center[2])]
        result = safe(fp, "AssignTangentialHField face {}".format(face), lambda face=face, origin=origin, upos=upos: oBoundary.AssignTangentialHField([
            "NAME:B0x_TH_{}".format(face),
            "ComponentXReal:=", H0,
            "ComponentYReal:=", "0",
            ["NAME:CoordSysVector", "Origin:=", origin, "UPos:=", upos],
            "ReverseV:=", False,
            "Faces:=", [face],
        ]))
        if result is not None:
            assigned += 1

    if normal_faces:
        safe(fp, "AssignZeroTangentialHField x-normal faces", lambda: oBoundary.AssignZeroTangentialHField([
            "NAME:B0x_open_flux_faces",
            "Faces:=", normal_faces,
        ]))
    return assigned


def extract_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    try:
        return float(raw)
    except Exception:
        return str(raw)


def eval_b_component(fields, key):
    op = {"Mag": "Mag", "Bx": "ScalarX", "By": "ScalarY", "Bz": "ScalarZ"}[key]
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp(op)
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    return extract_value(fields.GetTopEntryValue(SOLN, []))


def write_csv(row):
    with open(OUT_CSV, "wb") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "field_dir",
                "B0_Bx_T",
                "B0_By_T",
                "B0_Bz_T",
                "B0_Mag_T",
                "source_project",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerow(row)


def run():
    ensure_dirs()
    with open(LOG_PATH, "w") as fp:
        log(fp, "rebuild_B0_reference_x {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        try:
            fresh_project_copy(fp)

            import ScriptEnv

            ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
            oDesktop.RestoreWindow()
            oDesktop.OpenProject(OUT_PROJECT)
            oProject = oDesktop.GetActiveProject()
            oDesign = oProject.SetActiveDesign(DESIGN_NAME)
            oEditor = oDesign.SetActiveEditor("3D Modeler")
            oBoundary = oDesign.GetModule("BoundarySetup")

            delete_old_boundaries(fp, oBoundary)
            cleanup_geometry(fp, oEditor)
            faces = face_centers(oEditor)
            log(fp, "Box1 faces: {}".format(faces))
            groups = classify_box_faces(faces)
            assigned_h_faces = assign_x_tangential_h(fp, oBoundary, groups)
            safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())

            solved = None
            if assigned_h_faces > 0:
                solved = safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
            else:
                log(fp, "No tangential H field boundaries were assigned; skipping Analyze.")
            fields = oDesign.GetModule("FieldsReporter")
            row = {
                "case_id": "B0_reference_x",
                "field_dir": "x",
                "source_project": OUT_PROJECT,
                "status": "exported" if solved is not None else "failed",
            }
            for key, out_key in [
                ("Bx", "B0_Bx_T"),
                ("By", "B0_By_T"),
                ("Bz", "B0_Bz_T"),
                ("Mag", "B0_Mag_T"),
            ]:
                value = safe(fp, "eval {}".format(out_key), lambda k=key: eval_b_component(fields, k))
                row[out_key] = "" if value is None else value

            try:
                bx = abs(float(row["B0_Bx_T"]))
                by = abs(float(row["B0_By_T"]))
                bz = abs(float(row["B0_Bz_T"]))
                ratio = bx / max(by, bz, 1e-300)
                log(fp, "direction ratio abs(Bx)/max(abs(By),abs(Bz)) = {}".format(ratio))
                if ratio < 10.0:
                    row["status"] = "failed"
            except Exception:
                row["status"] = "failed"

            write_csv(row)
            safe(fp, "save project", lambda: oProject.Save())
            try:
                oDesktop.CloseProject(oProject.GetName())
            except Exception:
                pass
            log(fp, "Wrote {}".format(OUT_CSV))
        except Exception:
            log(fp, "SCRIPT FAILED")
            log(fp, traceback.format_exc())
            write_csv({
                "case_id": "B0_reference_x",
                "field_dir": "x",
                "B0_Bx_T": "",
                "B0_By_T": "",
                "B0_Bz_T": "",
                "B0_Mag_T": "",
                "source_project": OUT_PROJECT,
                "status": "failed",
            })


run()
