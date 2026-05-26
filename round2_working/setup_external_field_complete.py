"""
setup_external_field_complete.py
=================================
Comprehensive script to set up Helmholtz coil pair (Torus2, Torus3) on the
4-layer fixed-T=10mm, g=0.2mm model for external B-field / SF measurement.

Run this inside AEDT via Tools > Run Script.

What it does:
  1. Opens a CLEAN copy of the project (nominal version).
  2. Sets design variables a=2.35mm, g=0.2mm, T=10mm.
  3. Inspects Box1 size; enlarges if the Helmholtz coils won't fit.
  4. Creates Torus2 & Torus3 (copper, SolveInside) if missing.
     If they already exist, repairs material/size.
  5. Removes any stale section objects / boundary excitations.
  6. Sections both tori with XZ plane to create current-terminal faces.
  7. Assigns 1 A Current excitation to each section.
  8. Creates a BcenterPoint_0_0_0 non-model point at origin for field export.
  9. Validates the design.
 10. Optionally runs Setup1 (set ANALYZE=True below).
"""

import os
import sys
import time
import traceback

# ---------- user settings ----------
PROJECT_SRC = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_nominal.aedt"
PROJECT_DST = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_ext.aedt"
LOG_PATH    = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\setup_external_field_complete.log"

ANALYZE     = False   # set True to auto-run Setup1 after validation
# --------------------------------

# Helmholtz coil geometry (intended paper configuration)
TORUS2_CENTER = ("150mm", "0mm", "0mm")
TORUS3_CENTER = ("-150mm", "0mm", "0mm")
TORUS_AXIS    = "X"
TORUS_MAJOR_R = "300mm"
TORUS_MINOR_R = "2mm"


def log(fp, msg):
    line = str(msg)
    fp.write(line + "\n")
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


def run():
    with open(LOG_PATH, "w") as f:
        log(f, "=" * 60)
        log(f, "setup_external_field_complete  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f, "Source: %s" % PROJECT_SRC)
        log(f, "Dest:   %s" % PROJECT_DST)

        # ---- 0. init AEDT ----
        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        # ---- 1. copy clean project to working copy ----
        import shutil
        if os.path.exists(PROJECT_DST):
            os.remove(PROJECT_DST)
        shutil.copy2(PROJECT_SRC, PROJECT_DST)
        log(f, "Copied project to %s" % PROJECT_DST)

        safe(f, "open project", lambda: oDesktop.OpenProject(PROJECT_DST))
        oProject = safe(f, "get active project", lambda: oDesktop.GetActiveProject())
        if oProject is None:
            log(f, "FATAL: could not get active project")
            return

        oDesign = safe(f, "set active design", lambda: oProject.SetActiveDesign("Maxwell3DDesign1"))
        oEditor = safe(f, "get 3D editor", lambda: oDesign.SetActiveEditor("3D Modeler"))
        oBoundary = safe(f, "get boundary module", lambda: oDesign.GetModule("BoundarySetup"))

        log(f, "")
        log(f, "=== Model inspection ===")

        # ---- 2. set design variables ----
        safe(f, "set a=2.35mm", lambda: oDesign.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:LocalVariableTab",
             ["NAME:PropServers", "LocalVariables"],
             ["NAME:ChangedProps", ["NAME:a", "Value:=", "2.35mm"]]]
        ]))
        safe(f, "set g=0.2mm", lambda: oDesign.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:LocalVariableTab",
             ["NAME:PropServers", "LocalVariables"],
             ["NAME:ChangedProps", ["NAME:g", "Value:=", "0.2mm"]]]
        ]))
        safe(f, "set T=10mm", lambda: oDesign.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:LocalVariableTab",
             ["NAME:PropServers", "LocalVariables"],
             ["NAME:ChangedProps", ["NAME:T", "Value:=", "10mm"]]]
        ]))

        for vn in ["Rin", "H", "Iexc", "a", "g", "T"]:
            safe(f, "  variable %s" % vn, lambda v=vn: oDesign.GetVariableValue(v))

        # ---- 3. inspect existing objects ----
        log(f, "")
        log(f, "=== Object inventory ===")
        for grp in ["Solids", "Sheets", "Lines", "Unclassified"]:
            safe(f, "  %s" % grp, lambda g=grp: oEditor.GetObjectsInGroup(g))

        # ---- 4. inspect Box1 and enlarge if needed ----
        log(f, "")
        log(f, "=== Box1 check ===")
        box_props = {}
        for prop in ["X Size", "Y Size", "Z Size", "XCenter", "YCenter", "ZCenter"]:
            try:
                val = oEditor.GetPropertyValue("Geometry3DCmdTab", "Box1", prop)
                box_props[prop] = val
                log(f, "  Box1 %s = %s" % (prop, val))
            except Exception:
                log(f, "  Box1 %s: could not read" % prop)

        # Check if torus coils will fit. Torus ring reaches major_radius from its center.
        # For axis X, the ring is in the YZ plane, so Y_extent = center_Y +/- major_radius
        # and Z_extent = center_Z +/- major_radius.
        # We need the box to contain these extents plus margin.
        NEEDED_Y = 310.0  # 300 mm major radius + 10 mm margin
        NEEDED_Z = 310.0
        NEEDED_X = 160.0  # torus center at X=150 + 10 mm margin (X extent is just minor radius)

        def _parse_mm(val_str):
            """Extract numeric mm value from a string like '300mm' or '300'."""
            if val_str is None:
                return None
            s = str(val_str).replace("mm", "").strip()
            try:
                return float(s)
            except ValueError:
                return None

        def _set_box_prop(prop, val_mm):
            oEditor.ChangeProperty([
                "NAME:AllTabs",
                ["NAME:Geometry3DCmdTab",
                 ["NAME:PropServers", "Box1:CreateBox:1"],
                 ["NAME:ChangedProps", ["NAME:" + prop, "Value:=", "%smm" % str(val_mm)]]]
            ])

        # Enlarge Box1 if too small
        for prop, needed in [("Y Size", NEEDED_Y * 2), ("Z Size", NEEDED_Z * 2),
                             ("X Size", NEEDED_X * 2)]:
            cur = _parse_mm(box_props.get(prop))
            if cur is not None and cur < needed:
                log(f, "  Box1 %s = %s mm < %s mm, enlarging..." % (prop, cur, needed))
                safe(f, "  enlarge Box1 %s to %s" % (prop, needed),
                     lambda p=prop, n=needed: _set_box_prop(p, n))
            elif cur is not None:
                log(f, "  Box1 %s = %s mm is sufficient" % (prop, cur))

        # ---- 5. cleanup old external-field objects / boundaries ----
        log(f, "")
        log(f, "=== Cleanup ===")
        stale_boundaries = ["Iext_plus", "Iext_minus", "Current1", "Current2"]
        for bnd in stale_boundaries:
            try:
                oBoundary.DeleteBoundaries([bnd])
                log(f, "  deleted boundary: %s" % bnd)
            except Exception:
                pass  # doesn't exist, fine

        stale_objects = [
            "Torus2_Section1", "Torus3_Section1",
            "Torus2_Section1_Separate1", "Torus3_Section1_Separate1",
            "Iext_plus_sheet", "Iext_minus_sheet",
            "Iext_plus_sheet_1", "Iext_minus_sheet_1",
        ]
        for obj in stale_objects:
            try:
                oEditor.Delete(["NAME:Selections", "Selections:=", obj])
                log(f, "  deleted object: %s" % obj)
            except Exception:
                pass

        # ---- 6. create or repair Torus2 and Torus3 ----
        log(f, "")
        log(f, "=== External coils (Torus2, Torus3) ===")

        existing_solids = oEditor.GetObjectsInGroup("Solids")

        def _create_torus(name, x_center):
            """Create a torus with Axis=X, major=300mm, minor=2mm, material=copper."""
            oEditor.CreateTorus(
                [
                    "NAME:TorusParameters",
                    "IsCovered:="  , True,
                    "XCenter:="    , x_center,
                    "YCenter:="    , "0mm",
                    "ZCenter:="    , "0mm",
                    "MajorRadius:=", TORUS_MAJOR_R,
                    "MinorRadius:=", TORUS_MINOR_R,
                    "WhichAxis:="  , TORUS_AXIS,
                    "NumSegments:=", "0",
                ],
                [
                    "NAME:Attributes",
                    "Name:="                  , name,
                    "Flags:="                 , "",
                    "Color:="                 , "(255 0 0)",
                    "Transparency:="          , 0,
                    "PartCoordinateSystem:="  , "Global",
                    "UDMId:="                 , "",
                    "MaterialValue:="         , '"copper"',
                    "SurfaceMaterialValue:="  , '""',
                    "SolveInside:="           , True,
                    "ShellElement:="          , False,
                    "ShellElementThickness:=" , "0mm",
                    "IsMaterialEditable:="    , True,
                    "UseMaterialAppearance:=" , False,
                    "IsLightweight:="         , False,
                ],
            )

        def _repair_torus(name, x_center):
            """Repair an existing torus: fix dimensions, position, material, SolveInside."""
            oEditor.ChangeProperty([
                "NAME:AllTabs",
                ["NAME:Geometry3DCmdTab",
                 ["NAME:PropServers", name + ":CreateTorus:1"],
                 ["NAME:ChangedProps",
                  ["NAME:Center Position", "X:=", x_center, "Y:=", "0mm", "Z:=", "0mm"],
                  ["NAME:Axis"           , "Value:=", TORUS_AXIS],
                  ["NAME:Minor Radius"   , "Value:=", TORUS_MINOR_R],
                  ["NAME:Major Radius"   , "Value:=", TORUS_MAJOR_R]]]
            ])
            # Fix material & SolveInside via attribute tab
            oEditor.ChangeProperty([
                "NAME:AllTabs",
                ["NAME:Geometry3DAttributeTab",
                 ["NAME:PropServers", name],
                 ["NAME:ChangedProps",
                  ["NAME:Material", "Value:=", '"copper"'],
                  ["NAME:Solve Inside", "Value:=", True]]]
            ])

        for tname, tcenter in [("Torus2", TORUS2_CENTER[0]),
                                ("Torus3", TORUS3_CENTER[0])]:
            if tname in existing_solids:
                log(f, "  %s exists, repairing..." % tname)
                safe(f, "  repair %s" % tname, lambda n=tname, c=tcenter: _repair_torus(n, c))
            else:
                log(f, "  %s not found, creating..." % tname)
                safe(f, "  create %s" % tname, lambda n=tname, c=tcenter: _create_torus(n, c))

        # ---- 7. create sections (current terminals) ----
        log(f, "")
        log(f, "=== Section for current terminals ===")

        # Remove old sections first
        for sec_name in ["Torus2_Section1", "Torus3_Section1"]:
            try:
                oEditor.Delete(["NAME:Selections", "Selections:=", sec_name])
                log(f, "  removed old section: %s" % sec_name)
            except Exception:
                pass

        def _section_torus(torus_name):
            return oEditor.Section(
                ["NAME:Selections", "Selections:=", torus_name, "NewPartsModelFlag:=", "Model"],
                ["NAME:SectionToParameters",
                 "CreateNewObjects:=", True,
                 "SectionPlane:=", "ZX"],
            )

        safe(f, "  section Torus2", lambda: _section_torus("Torus2"))
        safe(f, "  section Torus3", lambda: _section_torus("Torus3"))

        # ---- 7b. separate multi-lump sections ----
        # The XZ section plane cuts each torus at TWO places (e.g. Z=+-300mm),
        # creating a multi-lump sheet.  AssignCurrent rejects multi-lump objects.
        # SeparateBody splits off one lump so the original becomes single-lump.
        log(f, "")
        log(f, "=== Separate multi-lump sections ===")

        def _separate_section(section_name):
            return oEditor.SeparateBody(
                ["NAME:Selections", "Selections:=", section_name,
                 "NewPartsModelFlag:=", "Model"])

        safe(f, "  separate Torus2_Section1", lambda: _separate_section("Torus2_Section1"))
        safe(f, "  separate Torus3_Section1", lambda: _separate_section("Torus3_Section1"))

        # Clean up the separated-off lumps
        for sep_name in ["Torus2_Section1_Separate1", "Torus3_Section1_Separate1"]:
            try:
                oEditor.Delete(["NAME:Selections", "Selections:=", sep_name])
                log(f, "  deleted %s" % sep_name)
            except Exception:
                pass

        # ---- 8. assign current excitations ----
        log(f, "")
        log(f, "=== Current excitation ===")

        # Remove old excitations if any
        for bnd in ["Iext_plus", "Iext_minus"]:
            try:
                oBoundary.DeleteBoundaries([bnd])
            except Exception:
                pass

        def _assign_current(bnd_name, section_name, point_out):
            return oBoundary.AssignCurrent(
                [
                    "NAME:" + bnd_name,
                    "Objects:=", [section_name],
                    "Current:=", "1A",
                    "IsSolid:=", True,
                    "Point out of terminal:=", point_out,
                ]
            )

        safe(f, "  assign Iext_plus", lambda: _assign_current("Iext_plus", "Torus2_Section1", False))
        safe(f, "  assign Iext_minus", lambda: _assign_current("Iext_minus", "Torus3_Section1", True))

        # ---- 9. create Bcenter point at origin ----
        log(f, "")
        log(f, "=== Bcenter point ===")
        try:
            # Check if point already exists
            oEditor.GetObjectByName("BcenterPoint_0_0_0")
            log(f, "  BcenterPoint_0_0_0 already exists")
        except Exception:
            safe(f, "  create BcenterPoint_0_0_0", lambda: oEditor.CreatePoint(
                ["NAME:PointParameters",
                 "X:=", "0mm",
                 "Y:=", "0mm",
                 "Z:=", "0mm",
                 "PointType:=", "NonModel"],
                ["NAME:Attributes",
                 "Name:=", "BcenterPoint_0_0_0",
                 "Color:=", "(255 255 0)",
                 "PartCoordinateSystem:=", "Global"]
            ))

        # ---- 10. validate ----
        log(f, "")
        log(f, "=== Validation ===")
        result = safe(f, "  ValidateDesign", lambda: oDesign.ValidateDesign())
        log(f, "  Validation result: %s" % str(result))

        # ---- 11. save ----
        log(f, "")
        safe(f, "save project", lambda: oProject.Save())
        log(f, "Project saved to: %s" % PROJECT_DST)

        # ---- 12. optionally analyze ----
        if ANALYZE:
            log(f, "")
            log(f, "=== Analysis ===")
            safe(f, "  AnalyzeAll", lambda: oDesign.AnalyzeAll())

        log(f, "")
        log(f, "Done.  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))


run()
