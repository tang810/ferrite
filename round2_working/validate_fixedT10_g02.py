import traceback

import ScriptEnv


PROJECT_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\Project100_4ceng_fixedT10_g02.aedt"
LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\validate_fixedT10_g02.log"


def main():
    with open(LOG_PATH, "w") as f:
        try:
            ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
            oDesktop.RestoreWindow()
            try:
                oDesktop.OpenProject(PROJECT_PATH)
                f.write("OpenProject: OK\n")
            except Exception:
                f.write("OpenProject skipped/failed, trying existing open project.\n")
            oProject = oDesktop.SetActiveProject("Project100_4ceng_fixedT10_g02")
            oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
            result = oDesign.ValidateDesign()
            f.write("ValidateDesign result: %s\n" % str(result))
        except Exception:
            f.write(traceback.format_exc())


main()
