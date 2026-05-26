import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
OUT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\solids_Project100_4ceng_fixedT10_g02.txt"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
oEditor = oDesign.SetActiveEditor("3D Modeler")

with open(OUT_PATH, "w") as f:
    f.write("Solid objects in Project100_4ceng_fixedT10_g02\n")
    for group in ["Solids", "Sheets", "Lines", "Unclassified"]:
        try:
            objs = oEditor.GetObjectsInGroup(group)
            f.write("{}: {}\n".format(group, objs))
        except Exception as exc:
            f.write("{}: FAILED: {}\n".format(group, exc))

print("Wrote {}".format(OUT_PATH))
