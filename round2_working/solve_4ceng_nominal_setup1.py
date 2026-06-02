import time
import traceback

import ScriptEnv

PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_nominal.aedt"
OUT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\solve_4ceng_nominal_setup1.txt"

ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")

oDesign.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:LocalVariableTab",
            ["NAME:PropServers", "LocalVariables"],
            [
                "NAME:ChangedProps",
                ["NAME:a", "Value:=", "2.35mm"],
                ["NAME:g", "Value:=", "0.2mm"],
                ["NAME:T", "Value:=", "10mm"],
            ],
        ],
    ]
)

with open(OUT_PATH, "w") as f:
    f.write("Solving nominal Setup1 only\n")
    f.write("Project: {}\n".format(PROJECT_PATH))
    f.write("Start: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
        f.write("{} = {}\n".format(name, oDesign.GetVariableValue(name)))
    try:
        oDesign.Analyze("Setup1")
        f.write("Analyze Setup1: OK\n")
    except Exception:
        f.write("Analyze Setup1: FAILED\n")
        f.write(traceback.format_exc())
    f.write("End: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))

oProject.Save()
print("Wrote {}".format(OUT_PATH))
