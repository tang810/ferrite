"""中文说明：
本脚本读取 data/experiment_matrix_main.csv，批量调用 AEDT 导出脚本。
默认只处理 status 为 built 或 solved 的 case；planned/missing 不会执行。
支持 --dry-run 检查将要执行的命令，适合在没有 AEDT/pyAEDT 环境时验证流程。
日志输出：logs/aedt_export.log。
"""

import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "data" / "experiment_matrix_main.csv"
LOG_PATH = ROOT / "logs" / "aedt_export.log"


PROJECT_HINTS = {
    "C1_N1_t008_x": ROOT / "round2_working" / "manufacturable_thin" / "C1_N1_t008_shield.aedt",
    "C1_N1_t020_x": ROOT / "round2_working" / "manufacturable_thin" / "C1_N1_t020_shield.aedt",
    "C1_N1_t040_x": ROOT / "round2_working" / "manufacturable_thin" / "C1_N1_t040_shield.aedt",
    "C1_N1_t060_x": ROOT / "round2_working" / "manufacturable_thin" / "C1_N1_t060_shield.aedt",
    "C2_N2_t020_g010_x": ROOT / "round2_working" / "manufacturable_thin" / "C2_N2_t020_g010_shield.aedt",
    "C2_N3_t020_g010_x": ROOT / "round2_working" / "manufacturable_thin" / "C2_N3_t020_g010_shield.aedt",
    "C2_N4_t015_g008_x": ROOT / "round2_working" / "manufacturable_thin" / "C2_N4_t015_g008_shield.aedt",
}


def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def read_matrix(path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run_cmd(cmd, dry_run):
    logging.info("command: %s", " ".join(map(str, cmd)))
    print(" ".join(map(str, cmd)))
    if not dry_run:
        subprocess.run(cmd, check=False)


def main():
    parser = argparse.ArgumentParser(description="Batch AEDT export driver for ferrite paper pipeline.")
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    parser.add_argument("--case-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export-only", action="store_true", help="Only run exports; solving is intentionally not automated yet.")
    args = parser.parse_args()

    setup_logging()
    rows = read_matrix(args.matrix)
    allowed_status = {"built", "solved"}
    selected = []
    for row in rows:
        if args.case_id and row["case_id"] != args.case_id:
            continue
        if row["status"] in allowed_status:
            selected.append(row)

    if not selected:
        print("No cases selected. Only status=built or solved cases are eligible.")
        logging.info("No eligible cases selected")
        return

    for row in selected:
        case_id = row["case_id"]
        project = PROJECT_HINTS.get(case_id)
        if not project or not project.exists():
            logging.warning("Missing AEDT project for %s", case_id)
            print(f"MISSING PROJECT: {case_id}")
            continue

        field_dir = row["external_field_direction"]
        coil_dir = row["coil_direction"] or field_dir
        model_type = row["model_type"]
        layers = row["N_layers"]

        center_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "aedt_export" / "export_center_field.py"),
            "--project",
            str(project),
            "--case-id",
            case_id,
            "--field-dir",
            field_dir,
            "--model-type",
            model_type,
        ]
        int_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "aedt_export" / "export_intH2_layerwise.py"),
            "--project",
            str(project),
            "--case-id",
            case_id,
            "--coil-dir",
            coil_dir,
            "--layers",
            layers,
        ]
        if args.dry_run:
            center_cmd.append("--dry-run")
            int_cmd.append("--dry-run")
        run_cmd(center_cmd, args.dry_run)
        if int(layers) > 0:
            run_cmd(int_cmd, args.dry_run)


if __name__ == "__main__":
    main()
