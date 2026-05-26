import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
OUT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\set_4ceng_fixedT10_g02.txt"

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

oProject.Save()

with open(OUT_PATH, "w") as f:
    f.write("Set variables for 4-layer fixed T=10mm, g=0.2mm case\n")
    for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
        f.write("{} = {}\n".format(name, oDesign.GetVariableValue(name)))

print("Wrote {}".format(OUT_PATH))
