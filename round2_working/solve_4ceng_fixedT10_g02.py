import time
import traceback

import ScriptEnv

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
OUT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\solve_4ceng_fixedT10_g02.txt"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")

with open(OUT_PATH, "w") as f:
    f.write("Solving Project100_4ceng_fixedT10_g02\n")
    f.write("Start: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
        f.write("{} = {}\n".format(name, oDesign.GetVariableValue(name)))
    try:
        oDesign.AnalyzeAll()
        f.write("AnalyzeAll: OK\n")
    except Exception:
        f.write("AnalyzeAll: FAILED\n")
        f.write(traceback.format_exc())
    f.write("End: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))

oProject.Save()
print("Wrote {}".format(OUT_PATH))
