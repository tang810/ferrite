import os
import traceback

import ScriptEnv

PROJECT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\Project100_4ceng_next.aedt"
OUT_PATH = r"D:\tangyumengnew\aaaaaaaaximukeji\round2_working\inspect_Project100_4ceng_next.txt"


def write_line(f, text):
    f.write(str(text) + "\n")


def safe_call(label, func, f):
    try:
        value = func()
        write_line(f, "{}: {}".format(label, value))
        return value
    except Exception:
        write_line(f, "{}: FAILED".format(label))
        write_line(f, traceback.format_exc())
        return None


ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
oDesktop.RestoreWindow()
oDesktop.OpenProject(PROJECT_PATH)
oProject = oDesktop.GetActiveProject()

with open(OUT_PATH, "w") as f:
    write_line(f, "AEDT project inspection")
    write_line(f, "Project path: {}".format(PROJECT_PATH))
    safe_call("AEDT version", lambda: oDesktop.GetVersion(), f)
    safe_call("Active project", lambda: oProject.GetName(), f)
    safe_call("Top design list", lambda: oProject.GetTopDesignList(), f)
    safe_call("Project variables", lambda: oProject.GetVariables(), f)

    design_names = safe_call("Design list", lambda: oProject.GetTopDesignList(), f)

    if design_names:
        for raw_name in design_names:
            design_name = raw_name
            if ";" in design_name:
                design_name = design_name.split(";")[-1]
            write_line(f, "")
            write_line(f, "Design: {}".format(design_name))
            try:
                oDesign = oProject.SetActiveDesign(design_name)
            except Exception:
                write_line(f, "SetActiveDesign failed:")
                write_line(f, traceback.format_exc())
                continue
            safe_call("Design type", lambda: oDesign.GetDesignType(), f)
            safe_call("Design variables", lambda: oDesign.GetVariables(), f)

            for module_name in ["Optimetrics", "ReportSetup", "FieldsReporter", "BoundarySetup", "AnalysisSetup"]:
                try:
                    module = oDesign.GetModule(module_name)
                    write_line(f, "Module available: {}".format(module_name))
                    if module_name == "Optimetrics":
                        safe_call("Optimetrics setups", lambda module=module: module.GetSetupNames(), f)
                    if module_name == "ReportSetup":
                        safe_call("Reports", lambda module=module: module.GetAllReportNames(), f)
                except Exception:
                    write_line(f, "Module unavailable: {}".format(module_name))

write_line(open(OUT_PATH, "a"), "Done.")
print("Wrote {}".format(OUT_PATH))
