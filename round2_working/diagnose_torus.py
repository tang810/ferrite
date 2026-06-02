"""
Diagnose Torus2/Torus3 geometry and explore the right approach for current excitation.
Run in AEDT to understand the multi-lump section issue and find a fix.
"""
import traceback

LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\diagnose_torus.log"
PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_external.aedt"


def log(fp, msg):
    fp.write(str(msg) + "\n")
    fp.flush()


def safe(fp, label, fn):
    try:
        out = fn()
        fp.write("%s: OK -> %s\n" % (label, str(out)))
        return out
    except Exception:
        fp.write("%s: FAILED\n" % label)
        fp.write(traceback.format_exc())
        return None


def run():
    with open(LOG_PATH, "w") as f:
        import ScriptEnv
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        oDesktop.RestoreWindow()

        safe(f, "open project", lambda: oDesktop.OpenProject(PROJECT_PATH))
        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        oEditor = oDesign.SetActiveEditor("3D Modeler")
        oBoundary = oDesign.GetModule("BoundarySetup")

        # List all objects in all groups
        f.write("\n=== All objects ===\n")
        for grp in ["Solids", "Sheets", "Lines", "Unclassified"]:
            objs = oEditor.GetObjectsInGroup(grp)
            f.write("%s: %s\n" % (grp, objs))

        # Check Torus2 geometry
        f.write("\n=== Torus2 properties ===\n")
        for tab in ["Geometry3DAttributeTab", "Geometry3DCmdTab"]:
            for prop in ["Material", "Solve Inside", "Name", "Major Radius", "Minor Radius",
                         "Center Position", "Axis", "XCenter", "YCenter", "ZCenter"]:
                try:
                    val = oEditor.GetPropertyValue(tab, "Torus2", prop)
                    f.write("  %s/%s = %s\n" % (tab, prop, val))
                except Exception:
                    pass

        # Check Torus2_Section1
        f.write("\n=== Torus2_Section1 details ===\n")
        for grp in ["Sheets"]:
            objs = oEditor.GetObjectsInGroup(grp)
            f.write("Sheets: %s\n" % objs)
            for obj_name in objs:
                if "Section" in str(obj_name) or "Torus2" in str(obj_name):
                    f.write("  Object: %s\n" % obj_name)
                    # Try to get faces/edges
                    try:
                        faces = oEditor.GetFaceIDs(obj_name)
                        f.write("    Faces: %s\n" % str(faces))
                    except Exception:
                        f.write("    Faces: could not get\n")
                    try:
                        edges = oEditor.GetEdgeIDs(obj_name)
                        f.write("    Edges: %s\n" % str(edges))
                    except Exception:
                        f.write("    Edges: could not get\n")

        # Try to separate the multi-lump section
        f.write("\n=== Attempting to separate Torus2_Section1 ===\n")
        if "Torus2_Section1" in str(oEditor.GetObjectsInGroup("Sheets")):
            safe(f, "separate Torus2_Section1",
                 lambda: oEditor.SeparateBody(
                     ["NAME:Selections", "Selections:=", "Torus2_Section1",
                      "NewPartsModelFlag:=", "Model"]))

        f.write("\n=== Objects after separation ===\n")
        for grp in ["Solids", "Sheets", "Lines", "Unclassified"]:
            objs = oEditor.GetObjectsInGroup(grp)
            f.write("%s: %s\n" % (grp, objs))

        # Now try to assign current to one of the separated parts
        f.write("\n=== Attempting current assignment on separated part ===\n")
        sheets = oEditor.GetObjectsInGroup("Sheets")
        for obj in sheets:
            if "Torus2" in str(obj):
                f.write("Trying to assign current on: %s\n" % obj)
                safe(f, "assign Iext_plus on %s" % obj,
                     lambda n=obj: oBoundary.AssignCurrent(
                         ["NAME:Iext_plus",
                          "Objects:=", [n],
                          "Current:=", "1A",
                          "IsSolid:=", True,
                          "Point out of terminal:=", False]))

        # Also try the Torus3 side
        f.write("\n=== Attempting Torus3 section handling ===\n")
        if "Torus3_Section1" in str(oEditor.GetObjectsInGroup("Sheets")):
            safe(f, "separate Torus3_Section1",
                 lambda: oEditor.SeparateBody(
                     ["NAME:Selections", "Selections:=", "Torus3_Section1",
                      "NewPartsModelFlag:=", "Model"]))

        f.write("\n=== Objects after Torus3 separation ===\n")
        for grp in ["Solids", "Sheets", "Lines", "Unclassified"]:
            objs = oEditor.GetObjectsInGroup(grp)
            f.write("%s: %s\n" % (grp, objs))

        sheets = oEditor.GetObjectsInGroup("Sheets")
        for obj in sheets:
            if "Torus3" in str(obj):
                f.write("Trying to assign current on: %s\n" % obj)
                safe(f, "assign Iext_minus on %s" % obj,
                     lambda n=obj: oBoundary.AssignCurrent(
                         ["NAME:Iext_minus",
                          "Objects:=", [n],
                          "Current:=", "1A",
                          "IsSolid:=", True,
                          "Point out of terminal:=", True]))

        # Check if there's an alternative: assign current directly to a torus face
        f.write("\n=== Alternative: Check Torus2 faces ===\n")
        try:
            faces = oEditor.GetFaceIDs("Torus2")
            f.write("Torus2 faces: %s\n" % str(faces))
            if faces:
                # Try to create a face list and assign current to a face
                for fid in faces[:1]:  # try first face only
                    f.write("  Face %s: trying to query\n" % str(fid))
        except Exception:
            f.write("Could not get Torus2 faces\n")

        # Validate
        f.write("\n=== Validation ===\n")
        safe(f, "validate", lambda: oDesign.ValidateDesign())

        safe(f, "save", lambda: oProject.Save())
        f.write("Done\n")


run()
