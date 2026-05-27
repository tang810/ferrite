"""Process validation-study CSV exports without fabricating missing data.

中文说明：
本脚本读取 data/raw 下的网格收敛、边界域收敛、轴向屏蔽、分段壳、
磁导率灵敏度和可选实验测量模板。已有真实数值则计算指标；缺失数值
保持为空并标记为 pending。脚本不会把 planned/TODO 行伪装成结果。
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, stdev


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
VALIDATION = ROOT / "data" / "validation"

B0_X = 1.25663682659e-06
B0_Z = 1.25663644033e-06


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"Wrote {path}")


def fval(row: dict[str, str], key: str) -> float | None:
    value = (row.get(key) or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def rel_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or abs(current) < 1e-300:
        return None
    return abs(current - previous) / abs(current)


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.10g}"


def process_mesh() -> None:
    rows = read_csv(RAW / "mesh_convergence_exports.csv")
    order = {"coarse": 0, "medium": 1, "fine": 2}
    out: list[dict[str, object]] = []
    validation_rows: list[dict[str, object]] = []

    for case_id in sorted({r["case_id"] for r in rows}):
        case_rows = sorted([r for r in rows if r["case_id"] == case_id], key=lambda r: order.get(r["mesh_level"], 99))
        previous = None
        processed_case_rows = []
        for row in case_rows:
            b = fval(row, "Bcenter_Bx_T")
            sfx = fval(row, "SFx")
            h2 = fval(row, "IntH2_total")
            if sfx is None and b is not None:
                sfx = abs(B0_X) / abs(b)
            d_b = rel_change(b, fval(previous, "Bcenter_Bx_T") if previous else None)
            d_sfx = rel_change(sfx, fval(previous, "SFx") if previous else None)
            d_h2 = rel_change(h2, fval(previous, "IntH2_total") if previous else None)
            meta_missing = any((row.get(k) or "").strip() == "" for k in ("total_elements", "air_domain_size"))
            status = "processed" if b is not None and sfx is not None and h2 is not None else "pending"
            processed = {
                "case_id": case_id,
                "mesh_level": row.get("mesh_level", ""),
                "total_elements": row.get("total_elements", ""),
                "elements_across_ferrite_thickness": row.get("elements_across_ferrite_thickness", ""),
                "air_domain_size": row.get("air_domain_size", ""),
                "Bcenter_Bx_T": fmt(b),
                "SFx": fmt(sfx),
                "IntH2_total": fmt(h2),
                "relative_change_Bcenter_Bx_T": fmt(d_b),
                "relative_change_SFx": fmt(d_sfx),
                "relative_change_IntH2_total": fmt(d_h2),
                "status": status,
                "notes": "mesh metadata incomplete" if meta_missing else row.get("notes", ""),
            }
            out.append(processed)
            processed_case_rows.append(processed)
            previous = {"Bcenter_Bx_T": fmt(b), "SFx": fmt(sfx), "IntH2_total": fmt(h2)}

        medium = next((r for r in processed_case_rows if r["mesh_level"] == "medium"), None)
        fine = next((r for r in processed_case_rows if r["mesh_level"] == "fine"), None)
        d_b_mf = rel_change(float(fine["Bcenter_Bx_T"]) if fine and fine["Bcenter_Bx_T"] else None,
                            float(medium["Bcenter_Bx_T"]) if medium and medium["Bcenter_Bx_T"] else None)
        d_sfx_mf = rel_change(float(fine["SFx"]) if fine and fine["SFx"] else None,
                              float(medium["SFx"]) if medium and medium["SFx"] else None)
        d_h2_mf = rel_change(float(fine["IntH2_total"]) if fine and fine["IntH2_total"] else None,
                             float(medium["IntH2_total"]) if medium and medium["IntH2_total"] else None)
        passed = (
            d_b_mf is not None and d_b_mf < 0.01 and
            d_sfx_mf is not None and d_sfx_mf < 0.01 and
            d_h2_mf is not None and d_h2_mf < 0.02
        )
        metadata_complete = all(r["total_elements"] and r["air_domain_size"] for r in processed_case_rows)
        validation_rows.append({
            "case_id": case_id,
            "medium_to_fine_relative_change_Bcenter_Bx_T": fmt(d_b_mf),
            "medium_to_fine_relative_change_SFx": fmt(d_sfx_mf),
            "medium_to_fine_relative_change_IntH2_total": fmt(d_h2_mf),
            "validation_status": "passed" if passed else "pending_or_failed",
            "metadata_status": "complete" if metadata_complete else "missing_total_elements_or_air_domain_size",
            "criterion": "dBcenter<1%, dSFx<1%, dIntH2<2%",
        })

    fields = [
        "case_id", "mesh_level", "total_elements", "elements_across_ferrite_thickness", "air_domain_size",
        "Bcenter_Bx_T", "SFx", "IntH2_total", "relative_change_Bcenter_Bx_T",
        "relative_change_SFx", "relative_change_IntH2_total", "status", "notes",
    ]
    write_csv(PROCESSED / "mesh_convergence_metrics.csv", out, fields)
    write_csv(VALIDATION / "mesh_convergence_validation.csv", validation_rows, [
        "case_id", "medium_to_fine_relative_change_Bcenter_Bx_T",
        "medium_to_fine_relative_change_SFx", "medium_to_fine_relative_change_IntH2_total",
        "validation_status", "metadata_status", "criterion",
    ])


def process_boundary() -> None:
    rows = read_csv(RAW / "boundary_convergence_exports.csv")
    out = []
    previous = None
    for row in rows:
        b = fval(row, "Bcenter_Bx_T")
        sfx = fval(row, "SFx")
        h2 = fval(row, "IntH2_total")
        if sfx is None and b is not None:
            sfx = abs(B0_X) / abs(b)
        out.append({
            "case_id": row.get("case_id", ""),
            "air_domain_scale": row.get("air_domain_scale", ""),
            "Bcenter_Bx_T": fmt(b),
            "SFx": fmt(sfx),
            "IntH2_total": fmt(h2),
            "relative_change_SFx": fmt(rel_change(sfx, previous[0]) if previous else None),
            "relative_change_IntH2_total": fmt(rel_change(h2, previous[1]) if previous else None),
            "status": "processed" if b is not None and sfx is not None and h2 is not None else "pending",
            "notes": row.get("notes", ""),
        })
        previous = (sfx, h2)
    write_csv(PROCESSED / "boundary_convergence_metrics.csv", out, [
        "case_id", "air_domain_scale", "Bcenter_Bx_T", "SFx", "IntH2_total",
        "relative_change_SFx", "relative_change_IntH2_total", "status", "notes",
    ])


def process_axial() -> None:
    rows = read_csv(RAW / "axial_shielding_exports.csv")
    transverse = {r["case_id"]: r for r in read_csv(PROCESSED / "metrics_table.csv")}
    out = []
    for row in rows:
        bz = fval(row, "Bcenter_Bz_T")
        sfz = abs(B0_Z) / abs(bz) if bz is not None and abs(bz) > 1e-300 else None
        leak = 1 / sfz if sfz else None
        base_x_id = row.get("case_id", "").replace("_z", "_x")
        sfx = fval(transverse.get(base_x_id, {}), "SFx")
        out.append({
            "case_id": row.get("case_id", ""),
            "N_layers": row.get("N_layers", ""),
            "t_ferrite_mm": row.get("t_ferrite_mm", ""),
            "g_radial_mm": row.get("g_radial_mm", ""),
            "Vf_mm3": row.get("Vf_mm3", ""),
            "Bcenter_Bz_T": fmt(bz),
            "SFz": fmt(sfz),
            "LeakageRatioz": fmt(leak),
            "SFz_over_SFx": fmt(sfz / sfx if sfz is not None and sfx else None),
            "status": "processed" if sfz is not None else "pending",
            "notes": row.get("notes", ""),
        })
    write_csv(PROCESSED / "axial_shielding_metrics.csv", out, [
        "case_id", "N_layers", "t_ferrite_mm", "g_radial_mm", "Vf_mm3",
        "Bcenter_Bz_T", "SFz", "LeakageRatioz", "SFz_over_SFx", "status", "notes",
    ])


def process_segmented() -> None:
    rows = read_csv(RAW / "segmented_shell_exports.csv")
    baseline = next((r for r in rows if r.get("segment_pattern") == "continuous"), {})
    sfx_cont = fval(baseline, "SFx")
    h2_cont = fval(baseline, "IntH2_total")
    out = []
    for row in rows:
        sfx = fval(row, "SFx")
        h2 = fval(row, "IntH2_total")
        out.append({
            "case_id": row.get("case_id", ""),
            "segment_pattern": row.get("segment_pattern", ""),
            "coverage_phi": row.get("coverage_phi", ""),
            "Bcenter_Bx_T": row.get("Bcenter_Bx_T", ""),
            "SFx": fmt(sfx),
            "SFx_seg_over_SFx_cont": fmt(sfx / sfx_cont if sfx is not None and sfx_cont else None),
            "LeakageRatiox": row.get("LeakageRatiox", ""),
            "IntH2_total": fmt(h2),
            "IntH2_seg_over_IntH2_cont": fmt(h2 / h2_cont if h2 is not None and h2_cont else None),
            "status": "processed" if sfx is not None and h2 is not None else "pending",
            "interpretation": "continuous baseline" if row.get("segment_pattern") == "continuous" else "TODO export segmented result",
        })
    write_csv(PROCESSED / "segmented_shell_metrics.csv", out, [
        "case_id", "segment_pattern", "coverage_phi", "Bcenter_Bx_T", "SFx",
        "SFx_seg_over_SFx_cont", "LeakageRatiox", "IntH2_total",
        "IntH2_seg_over_IntH2_cont", "status", "interpretation",
    ])


def process_permeability() -> None:
    rows = read_csv(RAW / "permeability_sweep_exports.csv")
    out = []
    for row in rows:
        out.append({
            "case_id": row.get("case_id", ""),
            "base_case": row.get("base_case", ""),
            "mu_r": row.get("mu_r", ""),
            "Bcenter_Bx_T": row.get("Bcenter_Bx_T", ""),
            "SFx": row.get("SFx", ""),
            "LeakageRatiox": row.get("LeakageRatiox", ""),
            "IntH2_total": row.get("IntH2_total", ""),
            "etaS_star": row.get("etaS_star", ""),
            "rhoH": row.get("rhoH", ""),
            "chiH": row.get("chiH", ""),
            "status": "processed" if row.get("status") == "exported" else "pending",
            "notes": row.get("notes", ""),
        })
    write_csv(PROCESSED / "permeability_sensitivity_metrics.csv", out, [
        "case_id", "base_case", "mu_r", "Bcenter_Bx_T", "SFx", "LeakageRatiox",
        "IntH2_total", "etaS_star", "rhoH", "chiH", "status", "notes",
    ])


def process_experimental() -> None:
    rows = read_csv(RAW / "experimental_sfx_measurement.csv")
    metrics = []
    groups: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        b0 = fval(row, "Bapp_T")
        bc = fval(row, "Bcenter_T")
        sf = abs(b0) / abs(bc) if b0 is not None and bc is not None and abs(bc) > 1e-300 else None
        if sf is not None:
            groups.setdefault((row.get("case_id", ""), row.get("field_dir", "")), []).append(sf)
        metrics.append({
            "run_id": row.get("run_id", ""),
            "case_id": row.get("case_id", ""),
            "field_dir": row.get("field_dir", ""),
            "repeat_index": row.get("repeat_index", ""),
            "SFq_exp": fmt(sf),
            "status": "processed" if sf is not None else "pending",
            "notes": row.get("notes", ""),
        })
    write_csv(PROCESSED / "experimental_sfx_metrics.csv", metrics, [
        "run_id", "case_id", "field_dir", "repeat_index", "SFq_exp", "status", "notes",
    ])
    budget = []
    for (case_id, field_dir), values in groups.items():
        budget.append({
            "case_id": case_id,
            "field_dir": field_dir,
            "n": len(values),
            "mean_SFq_exp": fmt(mean(values)),
            "std_SFq_exp": fmt(stdev(values) if len(values) > 1 else 0.0),
            "notes": "computed only from rows with Bapp_T and Bcenter_T",
        })
    if not budget:
        budget.append({
            "case_id": "TODO",
            "field_dir": "",
            "n": 0,
            "mean_SFq_exp": "",
            "std_SFq_exp": "",
            "notes": "no experimental data available",
        })
    write_csv(PROCESSED / "uncertainty_budget.csv", budget, [
        "case_id", "field_dir", "n", "mean_SFq_exp", "std_SFq_exp", "notes",
    ])


def main() -> None:
    process_mesh()
    process_boundary()
    process_axial()
    process_segmented()
    process_permeability()
    process_experimental()


if __name__ == "__main__":
    main()
