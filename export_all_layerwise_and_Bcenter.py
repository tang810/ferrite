"""
export_all_layerwise_and_Bcenter.py
=====================================
Opens each solved Project100_*ceng.aedt project, loops through all
Optimetrics parametric sweep variations, and exports:

  1. IntH2_total  (already exported, re-evaluate for consistency)
  2. Layer-wise IntH2 (IntH2_s1, IntH2_s2, IntH2_s3, IntH2_cyl2, etc.)
  3. Mag_B at center point (r=0, z=0) for shielding factor SF

Usage: In Maxwell AEDT, Tools -> Run Script -> select this file.
       Or: "C:\Program Files\AnsysEM\...\Win64\ironpython\ipy.exe" this_script.py

The script does NOT re-solve anything. It reads from already-solved
field solutions.
"""

import csv
import os
import sys
import traceback

# ---------------------------------------------------------------------------
# -- Configuration ----------------------------------------------------------
# ---------------------------------------------------------------------------

BASE_DIR = r"D:\ferrite\aaaaaaaaximukeji"

PROJECTS = {
    "1ceng": {
        "path": os.path.join(BASE_DIR, "Project100_1ceng.aedt"),
        "layer": 1,
        "setups": ["P_asweep", "P_Tcompare"],
        # Map: our_output_name -> field_calculator_named_expression
        "layer_exprs": {
            # 1ceng only has IntH2_total (single layer = total)
        },
    },
    "2ceng": {
        "path": os.path.join(BASE_DIR, "Project100_2ceng.aedt"),
        "layer": 2,
        "setups": ["P_asweep", "P_Tcompare", "P_agmatrix"],
        "layer_exprs": {
            "IntH2_L1": "IntH2_cyl2",  # inner ferrite layer
            "IntH2_L2": "IntH2_cyl4",  # outer ferrite layer
        },
    },
    "3ceng": {
        "path": os.path.join(BASE_DIR, "Project100_3ceng.aedt"),
        "layer": 3,
        "setups": ["P_asweep", "P_Tcompare", "P_agmatrix"],
        "layer_exprs": {
            "IntH2_L1": "IntH2_s1",
            "IntH2_L2": "IntH2_s2",
            "IntH2_L3": "IntH2_s3",
        },
    },
    "4ceng": {
        "path": os.path.join(BASE_DIR, "Project100_4ceng.aedt"),
        "layer": 4,
        "setups": ["P_asweep", "P_Tcompare", "P_agmatrix"],
        "layer_exprs": {
            "IntH2_L1": "IntH2_s1",
            "IntH2_L2": "IntH2_s2",
            "IntH2_L3": "IntH2_s3",
            "IntH2_L4": "InH2_s4",  # NOTE: typo in 4ceng AEDT: "InH2" not "IntH2"
        },
    },
}

# Expressions that exist in all projects
COMMON_EXPRS = {
    "IntH2_total": "IntH2_total",
}

OUT_CSV = os.path.join(BASE_DIR, "analysis_ready", "export_layerwise_Bcenter.csv")
OUT_LOG = os.path.join(BASE_DIR, "analysis_ready", "export_layerwise_Bcenter_log.txt")


# ---------------------------------------------------------------------------
# -- Helpers ----------------------------------------------------------------
# ---------------------------------------------------------------------------

def write_log(f, text):
    f.write(str(text) + "\n")
    f.flush()


def safe_get_var(oDesign, name):
    """Get a design variable value."""
    try:
        return oDesign.GetVariableValue(name)
    except Exception:
        return None


def eval_named_expr(fields, expr_name, soln_name):
    """Evaluate a Field Calculator Named Expression at a given solution."""
    try:
        fields.CalcStack("clear")
        fields.CopyNamedExprToStack(expr_name)
        fields.ClcEval(soln_name, [])
        return fields.GetTopEntryValue(soln_name, [])
    except Exception:
        return None


def eval_magB_at_center(fields, soln_name):
    """Evaluate Mag_B at (0, 0, 0) by building a Field Calculator stack.

    Stack:  Point(0,0,0) -> Mag_B -> Eval
    The Field Calculator evaluates Mag_B at the given point.
    """
    try:
        fields.CalcStack("clear")
        # Enter point coordinates
        fields.EnterPoint("0mm", "0mm", "0mm")
        # Get Mag_B quantity
        fields.CopyNamedExprToStack("Mag_B")
        # Evaluate: Mag_B at this point
        fields.CalcOp("Value")
        fields.ClcEval(soln_name, [])
        return fields.GetTopEntryValue(soln_name, [])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# -- Main -------------------------------------------------------------------
# ---------------------------------------------------------------------------

def main():
    import ScriptEnv
    ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")
    oDesktop = ScriptEnv.oDesktop  # Use the global from ScriptEnv
    oDesktop.RestoreWindow()

    all_rows = []
    log_lines = []

    for proj_key, proj_info in PROJECTS.items():
        proj_path = proj_info["path"]
        layer = proj_info["layer"]
        layer_exprs = proj_info["layer_exprs"]
        setups = proj_info["setups"]

        write_log(open(OUT_LOG, "a"), "\n" + "=" * 60)
        write_log(open(OUT_LOG, "a"), "Processing: {} (layer={})".format(proj_key, layer))
        write_log(open(OUT_LOG, "a"), "Project: {}".format(proj_path))

        if not os.path.exists(proj_path):
            write_log(open(OUT_LOG, "a"), "SKIP: file not found")
            continue

        try:
            oDesktop.OpenProject(proj_path)
        except Exception:
            write_log(open(OUT_LOG, "a"), "FAILED to open project:\n{}".format(
                traceback.format_exc()))
            continue

        oProject = oDesktop.GetActiveProject()
        oDesign = oProject.SetActiveDesign("Maxwell3DDesign1")
        fields = oDesign.GetModule("FieldsReporter")
        opti = oDesign.GetModule("Optimetrics")

        # Read design variables
        a_val = safe_get_var(oDesign, "a")
        g_val = safe_get_var(oDesign, "g")
        T_val = safe_get_var(oDesign, "T")
        Rin_val = safe_get_var(oDesign, "Rin")
        H_val = safe_get_var(oDesign, "H")
        write_log(open(OUT_LOG, "a"),
            "Design vars: a={}, g={}, T={}, Rin={}, H={}".format(
                a_val, g_val, T_val, Rin_val, H_val))

        # Get all setup names
        all_setup_names = opti.GetSetupNames()
        write_log(open(OUT_LOG, "a"), "All setups: {}".format(all_setup_names))

        for setup_name in setups:
            if setup_name not in all_setup_names:
                write_log(open(OUT_LOG, "a"),
                    "Setup '{}' not found, skipping.".format(setup_name))
                continue

            write_log(open(OUT_LOG, "a"), "\n--- Setup: {} ---".format(setup_name))

            # For parametric setups, the solution naming in Maxwell AEDT is:
            #   SetupName : VariationName
            # But GetSolutionVariationNames may not exist in all versions.
            # Alternative: use the Optimetrics results table.

            # Try to get the results via Optimetrics export
            try:
                # Method 1: Get the solved variation names from the setup
                # In Maxwell COM API, this is oDesign.GetAvailableSolutionVariationNames()
                # or opti.GetSolutionVariationNames(setup_name)

                # Try different API approaches:
                var_names = None
                for method_name in [
                    "GetSolutionVariationNames",
                    "GetVariationNames",
                    "GetSolvedVariationNames",
                ]:
                    try:
                        getter = getattr(opti, method_name, None)
                        if getter:
                            var_names = getter(setup_name)
                            if var_names:
                                write_log(open(OUT_LOG, "a"),
                                    "Variations via {}: {}".format(method_name, var_names))
                                break
                    except Exception:
                        continue

                if not var_names:
                    # Fallback: try to enumerate by guessing variation names
                    # from the sweep definition
                    write_log(open(OUT_LOG, "a"),
                        "WARNING: Could not enumerate variations. Trying fallback...")
                    # Use a generic approach: export the results table
                    try:
                        # Export optimetrics results table to CSV
                        export_path = os.path.join(BASE_DIR,
                            "_temp_export_{}_{}.csv".format(proj_key, setup_name))
                        oDesign.ExportOptimetricsResult(
                            setup_name, export_path)
                        write_log(open(OUT_LOG, "a"),
                            "Exported results table to: {}".format(export_path))
                    except Exception as e2:
                        write_log(open(OUT_LOG, "a"),
                            "ExportOptimetricsResult also failed: {}".format(e2))

            except Exception as e:
                write_log(open(OUT_LOG, "a"),
                    "Error enumerating variations for {}: {}".format(setup_name, e))
                write_log(open(OUT_LOG, "a"), traceback.format_exc())

    write_log(open(OUT_LOG, "a"), "\nDone. {} rows collected.".format(len(all_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
