"""Test which Python modules are available in IronPython."""
LOG_PATH = r"D:\ferrite\aaaaaaaaximukeji\round2_working\_test_modules.log"

with open(LOG_PATH, "w") as f:
    for mod_name in ["shutil", "os", "csv", "time", "traceback", "sys"]:
        try:
            __import__(mod_name)
            f.write("  %s: OK\n" % mod_name)
        except ImportError:
            f.write("  %s: NOT AVAILABLE\n" % mod_name)
    f.write("Done\n")
