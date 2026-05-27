"""中文说明：
本脚本用于从指定 AEDT 工程导出中心点磁感应强度 Bx/By/Bz/Mag_B。
它不会伪造结果；如果当前环境没有 pyAEDT 或工程内没有可复用报表，
脚本会把该 case 记录为 missing，并在 logs/aedt_export.log 中写明原因。
输出目标：data/raw/center_field_raw.csv。
"""

import argparse
import csv
import logging
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data" / "raw" / "center_field_raw.csv"
LOG_PATH = ROOT / "logs" / "aedt_export.log"


FIELDNAMES = [
    "case_id",
    "model_type",
    "field_dir",
    "source_project",
    "status",
    "B0_Bx_T",
    "B0_By_T",
    "B0_Bz_T",
    "B0_Mag_T",
    "Bcenter_Bx_T",
    "Bcenter_By_T",
    "Bcenter_Bz_T",
    "Bcenter_Mag_T",
    "notes",
]


def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def append_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerow({name: row.get(name, "") for name in FIELDNAMES})


def export_with_pyaedt(args):
    try:
        from pyaedt import Maxwell3d  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"pyAEDT is not available: {exc}") from exc

    # The exact field-export calls are intentionally conservative because
    # AEDT report names differ across projects. Use the manual checklist to
    # create named reports/expressions, then extend this function with the
    # project-specific report extraction call if needed.
    app = Maxwell3d(project=str(args.project), non_graphical=True, new_desktop=False)
    try:
        raise RuntimeError(
            "Automatic center-field extraction is project-specific. "
            "Create/export Bx, By, Bz, and Mag_B reports in AEDT or extend "
            "export_with_pyaedt() with verified report names."
        )
    finally:
        app.release_desktop(close_projects=False, close_desktop=False)


def main():
    parser = argparse.ArgumentParser(description="Export center B field from an AEDT project.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--field-dir", choices=["x", "y", "z"], required=True)
    parser.add_argument("--model-type", choices=["no_shield", "continuous_shell", "segmented_shell_3d"], required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    setup_logging()
    logging.info("center-field export requested case=%s project=%s dry_run=%s", args.case_id, args.project, args.dry_run)

    if args.dry_run:
        logging.info("DRY RUN center field: would export %s", args.case_id)
        print(f"DRY RUN: would export center field for {args.case_id} from {args.project}")
        return

    row = {
        "case_id": args.case_id,
        "model_type": args.model_type,
        "field_dir": args.field_dir,
        "source_project": str(args.project),
    }
    try:
        values = export_with_pyaedt(args)
        row.update(values or {})
        row["status"] = "exported"
        row["notes"] = "exported by pyAEDT"
    except Exception as exc:
        row["status"] = "missing"
        row["notes"] = str(exc)
        logging.warning("center-field export missing for %s: %s", args.case_id, exc)
    append_row(args.out, row)
    print(f"Wrote/updated {args.out} with status={row['status']}")


if __name__ == "__main__":
    main()
