import os
OUT = r"D:\ferrite\aaaaaaaaximukeji\round2_working\aedt_smoke_test.out"
with open(OUT, "w") as f:
    f.write("smoke start\n")
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    f.write("script env ok\n")
