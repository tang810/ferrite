"""中文说明：
本脚本用于从 AEDT 工程导出虚拟拾取线圈工况下的 IntH2_total 和各层
IntH2_Li。新工程必须统一使用 IntH2_L1/IntH2_L2/.../IntH2_total 命名；
如果检测到旧命名体系，只记录 legacy-compatible warning，不把缺失值当成 0。
输出目标：data/raw/intH2_layerwise_raw.csv。
"""

import argparse
import csv
import logging
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data" / "raw" / "intH2_layerwise_raw.csv"
LOG_PATH = ROOT / "logs" / "aedt_export.log"

LEGACY_ALIASES = {
    "IntH2_L1": ["IntH2_s1", "IntH2_cyl1", "InH2_s1"],
    "IntH2_L2": ["IntH2_s2", "IntH2_cyl2", "InH2_s2"],
    "IntH2_L3": ["IntH2_s3", "IntH2_cyl3", "InH2_s3"],
    "IntH2_L4": ["IntH2_s4", "IntH2_cyl4", "InH2_s4"],
}


def setup_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def fieldnames(max_layers):
    return ["case_id", "coil_dir", "source_project", "status", "IntH2_total"] + [
        f"IntH2_L{i}" for i in range(1, max_layers + 1)
    ] + ["notes"]


def append_row(path, row, max_layers):
    names = fieldnames(max_layers)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        if not exists:
            writer.writeheader()
        writer.writerow({name: row.get(name, "") for name in names})


def export_with_pyaedt(args):
    try:
        from pyaedt import Maxwell3d  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"pyAEDT is not available: {exc}") from exc

    app = Maxwell3d(project=str(args.project), non_graphical=True, new_desktop=False)
    try:
        raise RuntimeError(
            "Automatic named-expression extraction is project-specific. "
            "Ensure IntH2_total and IntH2_Li expressions exist, then extend "
            "export_with_pyaedt() with verified calculator/report calls."
        )
    finally:
        app.release_desktop(close_projects=False, close_desktop=False)


def legacy_warning(layer_count):
    warnings = []
    for i in range(1, layer_count + 1):
        key = f"IntH2_L{i}"
        aliases = LEGACY_ALIASES.get(key, [])
        if aliases:
            warnings.append(f"{key} legacy aliases: {', '.join(aliases)}")
    return "; ".join(warnings)


def main():
    parser = argparse.ArgumentParser(description="Export layerwise IntH2 named expressions from AEDT.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--coil-dir", choices=["x", "y", "z"], required=True)
    parser.add_argument("--layers", type=int, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    setup_logging()
    logging.info("IntH2 export requested case=%s project=%s dry_run=%s", args.case_id, args.project, args.dry_run)

    if args.layers < 1 or args.layers > 6:
        raise SystemExit("--layers must be between 1 and 6")

    if args.dry_run:
        msg = legacy_warning(args.layers)
        logging.warning("DRY RUN IntH2 %s. Legacy-compatible warning: %s", args.case_id, msg)
        print(f"DRY RUN: would export IntH2_total and IntH2_L1..L{args.layers} for {args.case_id}")
        print(f"WARNING legacy-compatible aliases, if seen, must be renamed or logged: {msg}")
        return

    row = {
        "case_id": args.case_id,
        "coil_dir": args.coil_dir,
        "source_project": str(args.project),
    }
    try:
        values = export_with_pyaedt(args)
        row.update(values or {})
        row["status"] = "exported"
        row["notes"] = "exported by pyAEDT"
    except Exception as exc:
        row["status"] = "missing"
        row["notes"] = f"{exc}; legacy-compatible aliases checked: {legacy_warning(args.layers)}"
        logging.warning("IntH2 export missing for %s: %s", args.case_id, row["notes"])
    append_row(args.out, row, max(6, args.layers))
    print(f"Wrote/updated {args.out} with status={row['status']}")


if __name__ == "__main__":
    main()
