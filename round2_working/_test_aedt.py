"""Simple test to verify AEDT script execution."""
import sys
import os

LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\_test_aedt.log"

with open(LOG_PATH, "w") as f:
    f.write("AEDT test script started\n")
    f.write("Python: %s\n" % sys.version)
    f.write("cwd: %s\n" % os.getcwd())
    try:
        import ScriptEnv
        f.write("ScriptEnv imported OK\n")
        ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
        f.write("Initialize OK\n")
        # oDesktop is a global after Initialize
        ver = oDesktop.GetVersion()
        f.write("Version: %s\n" % ver)
        oProject = oDesktop.GetActiveProject()
        if oProject:
            f.write("Active project: %s\n" % oProject.GetName())
        else:
            f.write("No active project\n")
    except Exception as e:
        f.write("FAILED: %s\n" % e)
        import traceback
        f.write(traceback.format_exc())
    f.write("Done\n")
