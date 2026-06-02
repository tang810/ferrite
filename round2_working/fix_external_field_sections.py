import os
import traceback

import ScriptEnv


PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\fix_external_field_sections.log"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def safe(label, fn, fp):
    try:
        out = fn()
        log(fp, label + ": OK")
        return out
    except Exception:
        log(fp, label + ": FAILED")
        log(fp, traceback.format_exc())
        return None


def main():
    with open(LOG_PATH, "w") as f:
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        safe("open project", lambda: oDesktop.OpenProject(PROJECT_PATH), f)
        oProject = oDesktop.SetActiveProject("Project100_4ceng_fixedT10_g02")
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        oEditor = oDesign.SetActiveEditor("3D Modeler")
        oBoundary = oDesign.GetModule("BoundarySetup")

        # Remove the temporary standalone terminal disks and stale excitations.
        for bnd in ["Iext_plus", "Iext_minus", "Current1", "Current2"]:
            safe("delete boundary " + bnd, lambda n=bnd: oBoundary.DeleteBoundaries([n]), f)

        for obj in [
            "Iext_plus_sheet",
            "Iext_minus_sheet",
            "Torus2_Section1",
            "Torus3_Section1",
            "Torus2_Section1_Separate1",
            "Torus3_Section1_Separate1",
        ]:
            safe("delete object " + obj, lambda n=obj: oEditor.Delete(["NAME:Selections", "Selections:=", n]), f)

        # Keep the external coils as large loops around the shield center.
        def set_torus(name, xcenter):
            return oEditor.ChangeProperty(
                [
                    "NAME:AllTabs",
                    [
                        "NAME:Geometry3DCmdTab",
                        ["NAME:PropServers", name + ":CreateTorus:1"],
                        [
                            "NAME:ChangedProps",
                            ["NAME:Center Position", "X:=", xcenter, "Y:=", "0mm", "Z:=", "0mm"],
                            ["NAME:Axis", "Value:=", "X"],
                            ["NAME:Minor Radius", "Value:=", "2mm"],
                            ["NAME:Major Radius", "Value:=", "300mm"],
                        ],
                    ],
                ]
            )

        safe("set Torus2 parameters", lambda: set_torus("Torus2", "150mm"), f)
        safe("set Torus3 parameters", lambda: set_torus("Torus3", "-150mm"), f)

        # For a torus whose axis is X, cut it with XZ. This creates a valid
        # conductor cross-section object, the same pattern as the original
        # Torus1_Section1 current terminal in the base model.
        def section_object(name):
            return oEditor.Section(
                ["NAME:Selections", "Selections:=", name, "NewPartsModelFlag:=", "Model"],
                ["NAME:SectionToParameters", "CreateNewObjects:=", True, "SectionPlane:=", "ZX"],
            )

        safe("section Torus2", lambda: section_object("Torus2"), f)
        safe("section Torus3", lambda: section_object("Torus3"), f)

        # The original internal coil in Project100 uses a Current excitation
        # assigned to the torus section object, not to a picked face. Keep the
        # same pattern here for the two external-field coils.
        def assign_current_object(name, object_name, point_out):
            return oBoundary.AssignCurrent(
                [
                    "NAME:" + name,
                    "Objects:=", [object_name],
                    "Current:=", "1A",
                    "IsSolid:=", True,
                    "Point out of terminal:=", point_out,
                ]
            )

        safe("assign Iext_plus on Torus2_Section1", lambda: assign_current_object("Iext_plus", "Torus2_Section1", False), f)
        safe("assign Iext_minus on Torus3_Section1", lambda: assign_current_object("Iext_minus", "Torus3_Section1", True), f)

        safe("save project", lambda: oProject.Save(), f)
        log(f, "Done")


main()
