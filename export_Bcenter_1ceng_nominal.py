import csv
import os
import traceback

import ScriptEnv


BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"
PROJECT_PATH = os.path.join(BASE_DIR, "Project100_1ceng.aedt")
OUT_CSV = os.path.join(BASE_DIR, "analysis_ready", "Bcenter_1ceng_nominal.csv")
OUT_LOG = os.path.join(BASE_DIR, "analysis_ready", "Bcenter_1ceng_nominal_log.txt")
POINT_NAME = "BcenterPoint_0_0_0"


def ensure_center_point(oDesign):
    editor = oDesign.SetActiveEditor("3D Modeler")
    try:
        names = list(editor.GetObjectsInGroup("Points"))
        if POINT_NAME in names:
            return
    except Exception:
        pass

    try:
        editor.CreatePoint(
            [
                "NAME:PointParameters",
                "PointX:=", "0mm",
                "PointY:=", "0mm",
                "PointZ:=", "0mm",
            ],
            [
                "NAME:Attributes",
                "Name:=", POINT_NAME,
                "Color:=", "(143 175 143)",
            ],
        )
    except Exception:
        # If the point already exists but could not be enumerated, continue.
        pass


def eval_magB_center(fields, soln_name):
    errors = []

    # AEDT versions differ here. Try several valid stack orders and avoid
    # CalcOp("Value"), which is not available in this AEDT 2025 R1 install.
    attempts = [
        ("point_then_Mag_B", lambda: (
            fields.EnterPoint(POINT_NAME),
            fields.CopyNamedExprToStack("Mag_B"),
        )),
        ("Mag_B_then_point", lambda: (
            fields.CopyNamedExprToStack("Mag_B"),
            fields.EnterPoint(POINT_NAME),
        )),
        ("point_then_B_mag", lambda: (
            fields.EnterPoint(POINT_NAME),
            fields.EnterQty("B"),
            fields.CalcOp("Mag"),
        )),
        ("B_mag_then_point", lambda: (
            fields.EnterQty("B"),
            fields.CalcOp("Mag"),
            fields.EnterPoint(POINT_NAME),
        )),
    ]

    for label, build_stack in attempts:
        try:
            fields.CalcStack("clear")
            build_stack()
            fields.ClcEval(soln_name, [])
            return fields.GetTopEntryValue(soln_name, [])
        except Exception as exc:
            errors.append("{}: {}".format(label, exc))

    raise RuntimeError("Could not evaluate Mag_B at center point. " + " | ".join(errors))


def main():
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    oDesktop.RestoreWindow()

    try:
        oProject = oDesktop.SetActiveProject("Project100_1ceng")
    except Exception:
        oDesktop.OpenProject(PROJECT_PATH)
    oProject = oDesktop.GetActiveProject()

    oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
    ensure_center_point(oDesign)
    fields = oDesign.GetModule("FieldsReporter")

    soln_name = "Setup1 : LastAdaptive"
    try:
        bcenter = eval_magB_center(fields, soln_name)
        with open(OUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["project", "solution", "x_mm", "y_mm", "z_mm", "Bcenter_T"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "project": "Project100_1ceng",
                    "solution": soln_name,
                    "x_mm": 0,
                    "y_mm": 0,
                    "z_mm": 0,
                    "Bcenter_T": bcenter,
                }
            )
        with open(OUT_LOG, "w") as f:
            f.write("OK\n")
            f.write("Project: {}\n".format(PROJECT_PATH))
            f.write("Solution: {}\n".format(soln_name))
            f.write("Bcenter_T: {}\n".format(bcenter))
            for name in ["Rin", "H", "Iexc", "a", "g", "T"]:
                try:
                    f.write("{} = {}\n".format(name, oDesign.GetVariableValue(name)))
                except Exception:
                    pass
        print("Wrote {}".format(OUT_CSV))
    except Exception:
        with open(OUT_LOG, "w") as f:
            f.write(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
