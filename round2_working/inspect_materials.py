import ScriptEnv

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
OUT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\materials_Project100_4ceng_fixedT10_g02.txt"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")

solids = oEditor.GetObjectsInGroup("Solids")

with open(OUT_PATH, "w") as f:
    f.write("Object materials in Project100_4ceng_fixedT10_g02\n")
    for obj in solids:
        values = []
        for tab in ["Geometry3DAttributeTab", "Geometry3DCmdTab"]:
            for prop in ["Material", "Solve Inside", "Name"]:
                try:
                    values.append("{}:{}={}".format(tab, prop, oEditor.GetPropertyValue(tab, obj, prop)))
                except Exception:
                    pass
        f.write("{} -> {}\n".format(obj, "; ".join(values)))

print("Wrote {}".format(OUT_PATH))
