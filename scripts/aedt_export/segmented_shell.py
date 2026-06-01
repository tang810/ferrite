# -*- coding: utf-8 -*-
"""Segmented shell correction study.

Creates 6 segmented-shield projects from continuous-shell templates.
For each ferrite layer:
  1. Deletes existing continuous cylinder
  2. Creates new full cylinder
  3. Creates 12 gap-cutting boxes at N_segments=12 positions, gap=1.6mm circumferentially
  4. Boolean-subtracts gaps -> cylinder splits into 12 separate segment solids
  5. Gap pattern: aligned (same angles per layer) or staggered (offset 15deg per layer)

Cases:
  S1_N1_t060_seg12_aligned_x    (1 layer,  aligned)
  S1_N1_t060_seg12_staggered_x  (1 layer,  staggered)
  S2_N3_t020_g010_seg12_aligned_x   (3 layers, aligned)
  S2_N3_t020_g010_seg12_staggered_x (3 layers, staggered)
  S2_N4_t015_g008_seg12_aligned_x   (4 layers, aligned)
  S2_N4_t015_g008_seg12_staggered_x (4 layers, staggered)

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
LOG_PATH = os.path.join(BASE_DIR, "logs", "segmented_shell.log")
CENTER_FIELD_OUT = os.path.join(BASE_DIR, "data", "raw", "center_field_raw.csv")
INTH2_OUT = os.path.join(BASE_DIR, "data", "raw", "intH2_layerwise_raw.csv")

DESIGN_NAME = "Maxwell3DDesign1"
POINT_NAME = "BcenterPoint_0_0_0"
SOLN = "Setup1 : LastAdaptive"
H0 = "1"
MESH_DIVISOR = 3
B0_Bx_T = 1.2566e-06

N_SEGMENTS = 12
GAP_MM = 1.6  # circumferential gap width
CYLINDER_HEIGHT_MM = 200.0
RIN_MM = 100.0

SEGMENTED_CASES = [
    {"case_id": "S1_N1_t060_seg12_aligned_x",
     "source_project": "C1_N1_t060_shield.aedt",
     "layers": 1, "a_mm": 0.60, "g_mm": 0.0, "staggered": False},
    {"case_id": "S1_N1_t060_seg12_staggered_x",
     "source_project": "C1_N1_t060_shield.aedt",
     "layers": 1, "a_mm": 0.60, "g_mm": 0.0, "staggered": True},
    {"case_id": "S2_N3_t020_g010_seg12_aligned_x",
     "source_project": "C2_N3_t020_g010_shield.aedt",
     "layers": 3, "a_mm": 0.20, "g_mm": 0.10, "staggered": False},
    {"case_id": "S2_N3_t020_g010_seg12_staggered_x",
     "source_project": "C2_N3_t020_g010_shield.aedt",
     "layers": 3, "a_mm": 0.20, "g_mm": 0.10, "staggered": True},
    {"case_id": "S2_N4_t015_g008_seg12_aligned_x",
     "source_project": "C2_N4_t015_g008_shield.aedt",
     "layers": 4, "a_mm": 0.15, "g_mm": 0.08, "staggered": False},
    {"case_id": "S2_N4_t015_g008_seg12_staggered_x",
     "source_project": "C2_N4_t015_g008_shield.aedt",
     "layers": 4, "a_mm": 0.15, "g_mm": 0.08, "staggered": True},
]

FERRITE_BASE_NAMES = ["Cylinder2", "Cylinder4", "Cylinder6", "Cylinder8"]

CENTER_FIELDNAMES = [
    "case_id", "field_dir", "Bcenter_Bx_T", "Bcenter_By_T",
    "Bcenter_Bz_T", "Bcenter_Mag_T", "source_project", "status",
]

INTH2_FIELDNAMES = [
    "case_id", "coil_dir", "source_project", "status",
    "IntH2_total", "IntH2_L1", "IntH2_L2", "IntH2_L3",
    "IntH2_L4", "IntH2_L5", "IntH2_L6", "notes",
]


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


def get_all_object_names(oEditor, oDesign):
    """Get all 3D object names using whatever API works in this AEDT version."""
    names = []

    # Approach 1: oEditor.GetAllObjects() or GetObjects()
    for method in ["GetAllObjects", "GetObjects", "GetObjectList", "GetAllObjectNames"]:
        try:
            result = getattr(oEditor, method)()
            if result:
                names = [str(x) for x in list(result)]
                return names
        except Exception:
            pass

    # Approach 2: oDesign.GetObjectNames()
    try:
        result = oDesign.GetObjectNames()
        if result:
            names = [str(x) for x in list(result)]
            return names
    except Exception:
        pass

    # Approach 3: iterate by index using GetObjectName(i)
    try:
        i = 0
        while i < 1000:
            name = oEditor.GetObjectName(i)
            if name and str(name).strip():
                names.append(str(name))
                i += 1
            else:
                break
        if names:
            return names
    except Exception:
        pass

    # Approach 4: try GetChildObject on Design -> Model -> Solids
    try:
        model = oDesign.GetChildObject("Model")
        solids = model.GetChildObject("Solids")
        result = solids.GetChildNames()
        if result:
            names = [str(x) for x in list(result)]
            return names
    except Exception:
        pass

    return names


def discover_segment_names(fp, oEditor, oDesign, base_name):
    """After boolean subtraction, find all objects derived from base_name."""
    found = []
    try:
        all_objects = get_all_object_names(oEditor, oDesign)
        log(fp, "  total objects in model: " + str(len(all_objects)))
        for obj_name in all_objects:
            s = str(obj_name)
            if s.startswith(base_name):
                found.append(s)
        # If no prefix match, try case-insensitive
        if not found:
            for obj_name in all_objects:
                s = str(obj_name).lower()
                if s.startswith(base_name.lower()):
                    found.append(str(obj_name))
        if not found:
            log(fp, "  ALL objects: " + str(all_objects[:40]))
    except Exception:
        log(fp, "discover_segment_names exception for " + base_name)
        log(fp, traceback.format_exc())
    return found


def assign_mesh_to_objects(fp, oDesign, object_names, max_len_str):
    """Apply LengthBased mesh to a list of geometry objects, with unique names."""
    mesh_module = oDesign.GetModule("MeshSetup")
    for obj_name in object_names:
        safe(fp, "SURF " + obj_name,
             lambda n=obj_name, ml=max_len_str:
             mesh_module.AssignLengthOp([
                 "NAME:Length_surf_seg_" + n,
                 "RefineInside:=", False,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))
        safe(fp, "VOL  " + obj_name,
             lambda n=obj_name, ml=max_len_str:
             mesh_module.AssignLengthOp([
                 "NAME:Length_vol_seg_" + n,
                 "RefineInside:=", True,
                 "Objects:=", [n],
                 "RestrictElem:=", True,
                 "NumMaxElem:=", "2000",
                 "RestrictLength:=", True,
                 "MaxLength:=", ml,
             ]))


def create_full_cylinder(fp, oEditor, name, inner_r_mm, outer_r_mm, height_mm):
    """Create a cylindrical shell (two concentric cylinders, subtract inner from outer)."""
    outer_name = name + "_outer"
    inner_name = name + "_inner"

    safe(fp, "create " + outer_name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", "0mm",
              "Radius:=", str(outer_r_mm) + "mm",
              "Height:=", str(height_mm) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", outer_name,
              "Flags:=", "",
              "Color:=", "(132 50 120)",
              "Transparency:=", 0,
              "PartCoordinateSystem:=", "Global",
              "UDMId:=", -1,
              "GroupId:=", -1,
              "MaterialValue:=", '"ferrite"',
              "SolveInside:=", True,
              "ShellElement:=", False,
              "ShellElementThickness:=", "0mm",
              "IsMaterialEditable:=", True,
              "IsSurfaceMaterialEditable:=", True,
              "UseMaterialAppearance:=", False,
              "IsLightweight:=", False,
              "IsAlwaysHidden:=", False,
              ]))

    safe(fp, "create " + inner_name,
         lambda: oEditor.CreateCylinder(
             ["NAME:CylinderParameters",
              "XCenter:=", "0mm",
              "YCenter:=", "0mm",
              "ZCenter:=", "0mm",
              "Radius:=", str(inner_r_mm) + "mm",
              "Height:=", str(height_mm) + "mm",
              "WhichAxis:=", "Z",
              "NumSides:=", "0"],
             ["NAME:Attributes",
              "Name:=", inner_name,
              "Flags:=", "",
              "Color:=", "(132 50 120)",
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

    # Subtract inner from outer to create cylindrical shell
    safe(fp, "subtract " + inner_name + " from " + outer_name + " -> " + name,
         lambda: oEditor.Subtract(
             ["NAME:Selections",
              "Blank Parts:=", outer_name,
              "Tool Parts:=", inner_name],
             ["NAME:SubtractParameters",
              "KeepOriginals:=", False]))
    log(fp, "created ferrite shell: " + name + " R=[" +
        fmt_float3(inner_r_mm) + "," + fmt_float3(outer_r_mm) + "] H=" +
        fmt_float3(height_mm))


def create_gap_boxes(fp, oEditor, layer_idx, n_segments, gap_mm, R_mid,
                     radial_depth, height_mm, offset_deg):
    """Create thin gap-cutting boxes at each segment gap position.

    Boxes are created along x-axis then rotated about Z to gap position.
    """
    gap_names = []
    for j in range(n_segments):
        angle_deg = j * 360.0 / n_segments + offset_deg
        gap_name = "gap_L" + str(layer_idx + 1) + "_s" + str(j + 1)

        # Create box centered at (R_mid, 0, 0), oriented with long axis along X
        pos_x = R_mid - radial_depth / 2.0
        pos_y = -gap_mm / 2.0
        pos_z = -(height_mm + 2.0) / 2.0

        safe(fp, "create gap box " + gap_name,
             lambda: oEditor.CreateBox(
                 ["NAME:BoxParameters",
                  "XPosition:=", str(pos_x) + "mm",
                  "YPosition:=", str(pos_y) + "mm",
                  "ZPosition:=", str(pos_z) + "mm",
                  "XSize:=", str(radial_depth) + "mm",
                  "YSize:=", str(gap_mm) + "mm",
                  "ZSize:=", str(height_mm + 2.0) + "mm"],
                 ["NAME:Attributes",
                  "Name:=", gap_name,
                  "Flags:=", "",
                  "Color:=", "(255 0 0)",
                  "Transparency:=", 0.5,
                  "PartCoordinateSystem:=", "Global",
                  "UDMId:=", -1,
                  "GroupId:=", -1,
                  "MaterialValue:=", '"vacuum"',
                  "SolveInside:=", False,
                  ]))

        # Rotate about Z by angle_deg
        safe(fp, "rotate " + gap_name + " by " + str(angle_deg) + "deg",
             lambda n=gap_name, a=str(angle_deg) + "deg":
             oEditor.Rotate(
                 ["NAME:Selections", "Selections:=", n],
                 ["NAME:RotateParameters",
                  "RotateAxis:=", "Z",
                  "RotateAngle:=", a]))

        gap_names.append(gap_name)
    return gap_names


def subtract_gaps_from_cylinder(fp, oEditor, cyl_name, gap_names):
    """Subtract gap boxes one at a time from the ferrite cylinder shell.

    Single-tool subtract is the only format proven to work in this AEDT version.
    After all 12 subtracts the cylinder has 12 through-gaps (still one body, but
    physically segmented — mesh and field integrals work on the full body).
    """
    success = 0
    for gname in gap_names:
        result = safe(fp, "subtract " + gname + " from " + cyl_name,
             lambda n=gname: oEditor.Subtract(
                 ["NAME:Selections",
                  "Blank Parts:=", cyl_name,
                  "Tool Parts:=", n],
                 ["NAME:SubtractParameters",
                  "KeepOriginals:=", False]))
        if result is True:  # subtract returns None on success, safe returns True
            success += 1
    log(fp, "segmented " + cyl_name + ": " + str(success) + "/" +
        str(len(gap_names)) + " gaps subtracted")


def compute_intH2_from_calc(fp, oDesign, ferrite_objects):
    """Compute IntH2 = integral(|H|^2 dV) over ferrite objects.

    Evaluates each component integral separately (Hx^2, Hy^2, Hz^2) and sums
    in Python to avoid CalcStack push/pop/Copy which are unreliable across
    Maxwell versions, and Square/Mag which may not exist.
    """
    fields = oDesign.GetModule("FieldsReporter")

    def eval_component_sq_integral(comp):
        """Evaluate integral of H_comp^2 over ferrite volume.

        Pushes H twice and extracts the component each time to get two
        scalars on the stack, then multiplies.  Avoids CalcStack("copy")
        which is not available in this Maxwell version.
        """
        scalar_op = {"x": "ScalarX", "y": "ScalarY", "z": "ScalarZ"}[comp]
        fields.CalcStack("clear")
        fields.EnterQty("H")
        fields.CalcOp(scalar_op)
        fields.EnterQty("H")
        fields.CalcOp(scalar_op)
        fields.CalcOp("*")
        fields.EnterVol(",".join(ferrite_objects))
        fields.CalcOp("Integrate")
        fields.ClcEval(SOLN, [])
        return extract_value(fields.GetTopEntryValue(SOLN, []))

    Hx2 = eval_component_sq_integral("x")
    Hy2 = eval_component_sq_integral("y")
    Hz2 = eval_component_sq_integral("z")

    total = 0.0
    for v in [Hx2, Hy2, Hz2]:
        try:
            total += float(v)
        except (ValueError, TypeError):
            pass
    return total


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
    """Bmag computed from scalar components -- ComplexMag CalcOp is unreliable."""
    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarX")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    Bx = extract_value(fields.GetTopEntryValue(SOLN, []))

    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarY")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    By = extract_value(fields.GetTopEntryValue(SOLN, []))

    fields.CalcStack("clear")
    fields.EnterQty("B")
    fields.CalcOp("ScalarZ")
    fields.EnterPoint(POINT_NAME)
    fields.CalcOp("Value")
    Bz = extract_value(fields.GetTopEntryValue(SOLN, []))

    try:
        bx = float(Bx)
        by = float(By)
        bz = float(Bz)
        return math.sqrt(bx * bx + by * by + bz * bz)
    except (ValueError, TypeError):
        return ""


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


def process_case(fp, oDesktop, case_info):
    case_id = case_info["case_id"]
    source_project = case_info["source_project"]
    layers = case_info["layers"]
    a_mm = case_info["a_mm"]
    g_mm = case_info["g_mm"]
    staggered = case_info["staggered"]
    source_path = os.path.join(PROJECT_DIR, source_project)

    seg_project_name = case_id + "_shield.aedt"
    seg_project_path = os.path.join(PROJECT_DIR, seg_project_name)

    log(fp, "")
    log(fp, "=" * 60)
    log(fp, "Processing " + case_id)
    log(fp, "  layers=" + str(layers) + " a=" + fmt_float3(a_mm) +
        "mm g=" + fmt_float3(g_mm) + "mm")
    log(fp, "  N_segments=" + str(N_SEGMENTS) + " gap=" + fmt_float3(GAP_MM) +
        "mm staggered=" + str(staggered))
    log(fp, "  copy " + source_project + " -> " + seg_project_name)

    if not os.path.exists(source_path):
        log(fp, "SOURCE MISSING: " + source_path)
        return

    # Remove stale lock
    for p in [source_path, seg_project_path]:
        lock_path = p + ".lock"
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    # Remove old segmented project
    if os.path.exists(seg_project_path):
        try:
            os.remove(seg_project_path)
        except Exception:
            pass

    shutil.copy2(source_path, seg_project_path)

    # Open
    opened = safe(fp, "OpenProject", lambda: oDesktop.OpenProject(seg_project_path))
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

    # Verify tangential-H boundaries
    th_count = count_tangential_h_faces(oBoundary)
    log(fp, "tangential-H faces: " + str(th_count))

    # Delete all existing ferrite-related objects from source project
    all_objs = get_all_object_names(oEditor, oDesign)
    for obj_name in all_objs:
        s = str(obj_name)
        for base_name in FERRITE_BASE_NAMES:
            if s.startswith(base_name):
                safe(fp, "delete old ferrite " + s,
                     lambda n=s: oEditor.Delete([
                         "NAME:Selections", "Selections:=", n]))
                break

    # Build segmented ferrite layers
    all_ferrite_segments = []
    for layer_i in range(layers):
        inner_r = RIN_MM + layer_i * (a_mm + g_mm)
        outer_r = inner_r + a_mm
        R_mid = (inner_r + outer_r) / 2.0
        radial_depth = a_mm + 4.0  # extend 2mm beyond each radial face

        cyl_name = FERRITE_BASE_NAMES[layer_i]
        log(fp, "--- Layer " + str(layer_i + 1) + " (" + cyl_name +
            "): inner=" + fmt_float3(inner_r) + " outer=" + fmt_float3(outer_r))

        # Create continuous cylindrical shell
        create_full_cylinder(fp, oEditor, cyl_name, inner_r, outer_r, CYLINDER_HEIGHT_MM)

        # Calculate offset for staggered pattern
        offset_deg = 0.0
        if staggered:
            # Odd layers get 15 deg offset
            if layer_i % 2 == 1:
                offset_deg = 360.0 / (2.0 * N_SEGMENTS)  # 15 deg

        # After create_full_cylinder, result is named cyl_name + "_outer"
        shell_name = cyl_name + "_outer"

        # Create gap boxes and subtract
        gap_names = create_gap_boxes(fp, oEditor, layer_i, N_SEGMENTS, GAP_MM,
                                     R_mid, radial_depth, CYLINDER_HEIGHT_MM, offset_deg)
        subtract_gaps_from_cylinder(fp, oEditor, shell_name, gap_names)

        # Gapped shell stays as one named object (single-tool subtract does not
        # auto-split into separate bodies), but mesh and field integrals work
        # correctly on it regardless.
        all_ferrite_segments.append(shell_name)
        log(fp, "  ferrite shell after gaps: " + shell_name)

    log(fp, "total ferrite objects: " + str(len(all_ferrite_segments)))

    if not all_ferrite_segments:
        log(fp, "FATAL: no ferrite segments created")
        return

    # Apply mesh to all segments
    clear_mesh_operations(fp, oDesign)
    max_len_mm = a_mm / float(MESH_DIVISOR)
    max_len_str = str(max_len_mm) + "mm"
    assign_mesh_to_objects(fp, oDesign, all_ferrite_segments, max_len_str)
    log(fp, "mesh applied to " + str(len(all_ferrite_segments)) +
        " segments | MaxLength=" + max_len_str)

    # Validate and solve
    safe(fp, "ValidateDesign", lambda: oDesign.ValidateDesign())
    solve_ok = safe(fp, "Analyze Setup1", lambda: oDesign.Analyze("Setup1"))
    if solve_ok is None:
        log(fp, "SKIP: solve failed, no data for " + case_id)
        try:
            oProject.Save()
        except Exception:
            pass
        try:
            oDesktop.CloseProject(oProject.GetName())
        except Exception:
            pass
        return

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
        "source_project": seg_project_path,
        "status": "exported" if Bx is not None else "failed",
    }

    SFx = ""
    if Bx is not None and Bx != "" and abs(Bx) > 1e-30:
        SFx = abs(B0_Bx_T) / abs(Bx)
    log(fp, "SFx=" + str(SFx))
    append_csv_row(CENTER_FIELD_OUT, CENTER_FIELDNAMES, center_row)

    # Export IntH2 via Fields Calculator
    IntH2_total = safe(fp, "compute IntH2_total via Calc",
                       lambda: compute_intH2_from_calc(fp, oDesign, all_ferrite_segments))
    intH2_row = {
        "case_id": case_id,
        "coil_dir": "x",
        "source_project": seg_project_path,
        "status": "exported" if IntH2_total is not None else "failed",
        "IntH2_total": IntH2_total if IntH2_total is not None else "",
        "notes": "segmented shell; " + ("staggered" if staggered else "aligned") +
                 "; " + str(N_SEGMENTS) + " segments; " +
                 fmt_float3(GAP_MM) + "mm gaps",
    }
    for layer_i in range(1, layers + 1):
        intH2_row["IntH2_L" + str(layer_i)] = ""
    for layer_i in range(layers + 1, 7):
        intH2_row["IntH2_L" + str(layer_i)] = ""

    log(fp, "IntH2_total=" + str(IntH2_total))
    append_csv_row(INTH2_OUT, INTH2_FIELDNAMES, intH2_row)

    # Save and close
    try:
        oProject.Save()
    except Exception:
        pass
    try:
        oDesktop.CloseProject(oProject.GetName())
    except Exception:
        pass

    log(fp, "Completed " + case_id + " | SFx=" + str(SFx) +
        " | IntH2=" + str(IntH2_total))


def run():
    ensure_dirs()

    fp = open(LOG_PATH, "w")
    try:
        log(fp, "segmented_shell " + time.strftime("%Y-%m-%d %H:%M:%S"))
        log(fp, "N_SEGMENTS=" + str(N_SEGMENTS) + " GAP=" + fmt_float3(GAP_MM) + "mm")
        log(fp, "MESH_DIVISOR=" + str(MESH_DIVISOR))
        log(fp, "Cases: " + str([c["case_id"] for c in SEGMENTED_CASES]))
        log(fp, "")

        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        for case_info in SEGMENTED_CASES:
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
