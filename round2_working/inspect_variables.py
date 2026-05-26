import traceback

import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_next.aedt"
OUT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\variables_Project100_4ceng_next.txt"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")

with open(OUT_PATH, "w") as f:
    f.write("Design variables for Project100_4ceng_next / Maxwell3DDesign1\n")
    for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
        try:
            f.write("{} = {}\n".format(name, oDesign.GetVariableValue(name)))
        except Exception:
            f.write("{} = FAILED\n{}\n".format(name, traceback.format_exc()))

print("Wrote {}".format(OUT_PATH))
