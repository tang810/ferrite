import os
import traceback
import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
LOG_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\fix_external_field_model.log"


def log(f, msg):
    f.write(str(msg) + "\n")
    f.flush()


def safe(label, fn, f):
    try:
        out = fn()
        log(f, label + ": OK" + (" -> " + str(out) if out is not None else ""))
        return out
    except Exception:
        log(f, label + ": FAILED")
        log(f, traceback.format_exc())
        return None


def delete_editor_objects(oEditor, names, f):
    for name in names:
        safe("delete object " + name, lambda n=name: oEditor.Delete(["NAME:Selections", "Selections:=", n]), f)


def delete_boundaries(oModule, names, f):
    for name in names:
        safe("delete boundary " + name, lambda n=name: oModule.DeleteBoundaries([n]), f)


def create_circle(oEditor, name, x, y, z, radius, axis):
    oEditor.CreateCircle(
        [
            "NAME:CircleParameters",
            "IsCovered:=", True,
            "XCenter:=", x,
            "YCenter:=", y,
            "ZCenter:=", z,
            "Radius:=", radius,
            "WhichAxis:=", axis,
            "NumSegments:=", "0",
        ],
        [
            "NAME:Attributes",
            "Name:=", name,
            "Flags:=", "",
            "Color:=", "(255 0 255)",
            "Transparency:=", 0,
            "PartCoordinateSystem:=", "Global",
            "UDMId:=", "",
            "MaterialValue:=", '"vacuum"',
            "SurfaceMaterialValue:=", '""',
            "SolveInside:=", True,
            "ShellElement:=", False,
            "ShellElementThickness:=", "0mm",
            "IsMaterialEditable:=", True,
            "UseMaterialAppearance:=", False,
            "IsLightweight:=", False,
        ],
    )


def main():
    with open(LOG_PATH, "w") as f:
        log(f, "Starting external field model repair")
        log(f, "Project: " + PROJECT_PATH)
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()
        oDesktop.OpenProject(PROJECT_PATH)
        oProject = oDesktop.SetActiveProject("Project100_4ceng_fixedT10_g02")
        if oProject is None:
            oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        oEditor = oDesign.SetActiveEditor("3D Modeler")
        oBoundary = oDesign.GetModule("BoundarySetup")

        safe("delete stale excitations", lambda: oBoundary.DeleteBoundaries(["Iext_minus", "Iext_plus", "Current1", "Current2"]), f)
        delete_editor_objects(oEditor, [
            "Torus2_Section1", "Torus3_Section1", "Torus2_Section1_Separate1", "Torus3_Section1_Separate1",
            "Iext_plus_sheet", "Iext_minus_sheet", "Iext_plus_sheet_1", "Iext_minus_sheet_1"
        ], f)

        # Force the external torus pair to the intended dimensions and positions.
        # This edits the existing history command under each object.
        safe("set Torus2 parameters", lambda: oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DCmdTab",
             ["NAME:PropServers", "Torus2:CreateTorus:1"],
             ["NAME:ChangedProps",
              ["NAME:Center Position", "X:=", "150mm", "Y:=", "0mm", "Z:=", "0mm"],
              ["NAME:Axis", "Value:=", "X"],
              ["NAME:Minor Radius", "Value:=", "2mm"],
              ["NAME:Major Radius", "Value:=", "300mm"]]]
        ]), f)
        safe("set Torus3 parameters", lambda: oEditor.ChangeProperty([
            "NAME:AllTabs",
            ["NAME:Geometry3DCmdTab",
             ["NAME:PropServers", "Torus3:CreateTorus:1"],
             ["NAME:ChangedProps",
              ["NAME:Center Position", "X:=", "-150mm", "Y:=", "0mm", "Z:=", "0mm"],
              ["NAME:Axis", "Value:=", "X"],
              ["NAME:Minor Radius", "Value:=", "2mm"],
              ["NAME:Major Radius", "Value:=", "300mm"]]]
        ]), f)

        safe("create Iext_plus_sheet", lambda: create_circle(oEditor, "Iext_plus_sheet", "450mm", "0mm", "0mm", "2mm", "X"), f)
        safe("create Iext_minus_sheet", lambda: create_circle(oEditor, "Iext_minus_sheet", "-450mm", "0mm", "0mm", "2mm", "X"), f)

        # Assign sheet currents. If AEDT rejects this in validation, the next fallback is a coil terminal workflow.
        safe("assign Iext_plus", lambda: oBoundary.AssignCurrent([
            "NAME:Iext_plus",
            "Objects:=", ["Iext_plus_sheet"],
            "Current:=", "1A",
            "IsSolid:=", False,
            "Point out of terminal:=", False,
        ]), f)
        safe("assign Iext_minus", lambda: oBoundary.AssignCurrent([
            "NAME:Iext_minus",
            "Objects:=", ["Iext_minus_sheet"],
            "Current:=", "1A",
            "IsSolid:=", False,
            "Point out of terminal:=", True,
        ]), f)

        safe("save project", lambda: oProject.Save(), f)
        log(f, "Done")

main()
