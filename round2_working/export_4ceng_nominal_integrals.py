import csv
import traceback

import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02_nominal.aedt"
OUT_TXT = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\export_4ceng_nominal_integrals.txt"
OUT_CSV = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\round2_4ceng_fixedT10_g02_nominal.csv"

EXPRESSIONS = [
    ("IntH2_L1", "IntH2_s1"),
    ("IntH2_L2", "IntH2_s2"),
    ("IntH2_L3", "IntH2_s3"),
    ("IntH2_L4", "InH2_s4"),
    ("IntH2_total", "IntH2_total"),
]


def eval_expr(fields, expr_name, soln_name):
    fields.CalcStack("clear")
    fields.CopyNamedExprToStack(expr_name)
    fields.ClcEval(soln_name, [])
    return fields.GetTopEntryValue(soln_name, [])


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()
oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
fields = oDesign.GetModule("FieldsReporter")

soln_name = "Setup1 : LastAdaptive"
values = {}
errors = {}

for out_name, expr_name in EXPRESSIONS:
    try:
        values[out_name] = eval_expr(fields, expr_name, soln_name)
    except Exception:
        errors[out_name] = traceback.format_exc()

with open(OUT_TXT, "w") as f:
    f.write("Export nominal integrals\n")
    f.write("Project: {}\n".format(PROJECT_PATH))
    f.write("Solution: {}\n".format(soln_name))
    f.write("Variables:\n")
    for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
        f.write("  {} = {}\n".format(name, oDesign.GetVariableValue(name)))
    f.write("Values:\n")
    for name, _ in EXPRESSIONS:
        f.write("  {} = {}\n".format(name, values.get(name, "FAILED")))
    if errors:
        f.write("Errors:\n")
        for name, err in errors.items():
            f.write("---- {} ----\n{}\n".format(name, err))

with open(OUT_CSV, "w") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "experiment",
            "layer",
            "T_mm",
            "a_mm",
            "g_mm",
            "IntH2_total",
            "IntH2_L1",
            "IntH2_L2",
            "IntH2_L3",
            "IntH2_L4",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "experiment": "fixedT10_g02",
            "layer": 4,
            "T_mm": 10.0,
            "a_mm": 2.35,
            "g_mm": 0.2,
            "IntH2_total": values.get("IntH2_total", ""),
            "IntH2_L1": values.get("IntH2_L1", ""),
            "IntH2_L2": values.get("IntH2_L2", ""),
            "IntH2_L3": values.get("IntH2_L3", ""),
            "IntH2_L4": values.get("IntH2_L4", ""),
        }
    )

print("Wrote {} and {}".format(OUT_TXT, OUT_CSV))
