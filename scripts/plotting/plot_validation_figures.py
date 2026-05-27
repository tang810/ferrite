"""Generate validation figures and explicit TODO placeholders.

中文说明：
本脚本只绘制已有 processed/raw 数据。缺少真实导出时生成带 TODO 说明的
占位 PNG，避免把缺失数据伪装成实验或仿真结果。
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fval(row: dict[str, str], key: str) -> float | None:
    value = (row.get(key) or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def save_placeholder(path: Path, title: str, message: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.62, title, ha="center", va="center", fontsize=14, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10, wrap=True)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print(f"Wrote {path}")


def save_line(path: Path, rows: list[dict[str, str]], x_key: str, y_key: str, group_key: str, title: str, ylabel: str) -> None:
    data = [r for r in rows if fval(r, x_key) is not None and fval(r, y_key) is not None]
    if not data:
        save_placeholder(path, title, f"TODO: no processed data with {x_key} and {y_key}.")
        return
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    groups = sorted({r.get(group_key, "") for r in data})
    for group in groups:
        g = sorted([r for r in data if r.get(group_key, "") == group], key=lambda r: fval(r, x_key) or 0)
        ax.plot([fval(r, x_key) for r in g], [fval(r, y_key) for r in g], marker="o", label=group)
    ax.set_title(title)
    ax.set_xlabel(x_key)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    if groups:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print(f"Wrote {path}")


def plot_transverse_main() -> None:
    rows = [
        r for r in read_csv(PROCESSED / "metrics_table.csv")
        if r.get("metric_status") == "processed" and r.get("model_type") == "continuous_shell" and r.get("external_field_direction") == "x"
    ]
    save_line(FIG / "Fig3_SFx_vs_Vf.png", rows, "Vf_mm3", "SFx", "N_layers",
              "Fig. 3. SFx versus ferrite volume", "SFx")

    equal = [r for r in rows if r.get("case_id") in {"C1_N1_t060_x", "C2_N3_t020_g010_x", "C2_N4_t015_g008_x"}]
    if not equal:
        save_placeholder(FIG / "Fig4_fixed_volume_comparison.png", "Fig. 4. Fixed-volume comparison", "TODO: equal-volume data missing.")
        return
    metrics = ["SFx", "IntH2_total", "etaS_star", "chiH"]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    for ax, metric in zip(axes.ravel(), metrics):
        ax.bar([r["case_id"].replace("_x", "") for r in equal], [fval(r, metric) or 0 for r in equal])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=20, labelsize=7)
        ax.grid(True, axis="y", alpha=0.25)
    fig.suptitle("Fig. 4. Fixed-volume comparison")
    fig.tight_layout()
    fig.savefig(FIG / "Fig4_fixed_volume_comparison.png", dpi=220)
    plt.close(fig)
    print(f"Wrote {FIG / 'Fig4_fixed_volume_comparison.png'}")


def plot_mesh_boundary() -> None:
    mesh = read_csv(PROCESSED / "mesh_convergence_metrics.csv")
    save_line(FIG / "mesh_convergence_sfx.png", mesh, "elements_across_ferrite_thickness", "SFx", "case_id",
              "Fig. 7a. Mesh convergence: SFx", "SFx")
    save_line(FIG / "mesh_convergence_intH2.png", mesh, "elements_across_ferrite_thickness", "IntH2_total", "case_id",
              "Fig. 7b. Mesh convergence: IntH2_total", "IntH2_total (A^2 m)")
    boundary = read_csv(PROCESSED / "boundary_convergence_metrics.csv")
    save_line(FIG / "boundary_convergence.png", boundary, "air_domain_scale", "SFx", "case_id",
              "Fig. 7c. Boundary-domain convergence", "SFx")


def plot_axial() -> None:
    rows = read_csv(PROCESSED / "axial_shielding_metrics.csv")
    data = [r for r in rows if r.get("status") == "processed" and fval(r, "SFz") is not None]
    if not data:
        save_placeholder(FIG / "sfx_sfz_comparison.png", "Fig. 8. SFx/SFz comparison",
                         "TODO: z-directed shielded center-field exports are missing. B0_reference_z is available and validated.")
        return
    transverse = {r["case_id"]: r for r in read_csv(PROCESSED / "metrics_table.csv")}
    labels = [r["case_id"].replace("_z", "") for r in data]
    sfx = [fval(transverse.get(r["case_id"].replace("_z", "_x"), {}), "SFx") or 0 for r in data]
    sfz = [fval(r, "SFz") or 0 for r in data]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], sfx, width=0.36, label="SFx")
    ax.bar([i + 0.18 for i in x], sfz, width=0.36, label="SFz")
    ax.set_xticks(list(x), labels, rotation=20, ha="right")
    ax.set_ylabel("Shielding factor")
    ax.set_title("Fig. 8. SFx versus SFz")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "sfx_sfz_comparison.png", dpi=220)
    plt.close(fig)


def plot_segmented_mu_experimental() -> None:
    segmented = read_csv(PROCESSED / "segmented_shell_metrics.csv")
    seg_data = [r for r in segmented if r.get("status") == "processed" and r.get("segment_pattern") != "continuous"]
    if not seg_data:
        save_placeholder(FIG / "segmented_shell_comparison.png", "Fig. 9. Segmented-shell correction",
                         "TODO: aligned and staggered segmented AEDT exports are missing.")
    else:
        save_line(FIG / "segmented_shell_comparison.png", segmented, "coverage_phi", "SFx", "segment_pattern",
                  "Fig. 9. Segmented-shell correction", "SFx")
    save_placeholder(FIG / "segmented_geometry_aligned.png", "Segmented geometry: aligned slots",
                     "TODO: export/render AEDT geometry image for Nseg=12, g_phi=1.6 mm, aligned slots.")
    save_placeholder(FIG / "segmented_geometry_staggered.png", "Segmented geometry: staggered slots",
                     "TODO: export/render AEDT geometry image for staggered slots, Delta_phi_i=(i-1)pi/Nseg.")

    mu = read_csv(PROCESSED / "permeability_sensitivity_metrics.csv")
    done = [r for r in mu if r.get("status") == "processed"]
    if len(done) < 4:
        save_placeholder(FIG / "permeability_sensitivity_sfx.png", "Fig. 10a. Permeability sensitivity: SFx",
                         "TODO: mu_r'=500/2000/5000 AEDT exports are missing; only baseline mu_r'=1000 rows are available.")
        save_placeholder(FIG / "permeability_sensitivity_intH2.png", "Fig. 10b. Permeability sensitivity: IntH2",
                         "TODO: mu_r' sweep data are missing.")
        save_placeholder(FIG / "permeability_sensitivity_ranking.png", "Fig. 10c. Permeability sensitivity ranking",
                         "TODO: ranking robustness cannot be assessed until the sweep is exported.")
    else:
        save_line(FIG / "permeability_sensitivity_sfx.png", done, "mu_r", "SFx", "base_case",
                  "Fig. 10a. Permeability sensitivity: SFx", "SFx")
        save_line(FIG / "permeability_sensitivity_intH2.png", done, "mu_r", "IntH2_total", "base_case",
                  "Fig. 10b. Permeability sensitivity: IntH2", "IntH2_total")
        save_line(FIG / "permeability_sensitivity_ranking.png", done, "mu_r", "etaS_star", "base_case",
                  "Fig. 10c. Permeability sensitivity ranking", "etaS_star")

    exp = read_csv(PROCESSED / "experimental_sfx_metrics.csv")
    if not any(r.get("status") == "processed" for r in exp):
        save_placeholder(FIG / "experimental_vs_fem_sfx.png", "Experimental versus FEM SFx",
                         "TODO: no prototype SF measurement data are available.")


def plot_field_placeholders() -> None:
    save_placeholder(FIG / "Fig1_measurement_framework.png", "Fig. 1. Measurement-oriented evaluation framework",
                     "External uniform-field model and virtual pickup-coil model. Replace with vector artwork before submission.")
    save_placeholder(FIG / "Fig2_multilayer_cylindrical_geometry.png", "Fig. 2. Multilayer cylindrical shell geometry",
                     "TODO: render geometry with Rin, L, a, g, NL, Tf, and Tspace labels.")
    save_placeholder(FIG / "Fig5_Hvc2_field_map.png", "Fig. 5. Virtual pickup-coil H_vc^2 field map",
                     "TODO: export H_vc magnitude and H_vc^2 contours from AEDT; layerwise fraction bar chart is available from CSV.")
    save_placeholder(FIG / "Fig6_external_B_field_comparison.png", "Fig. 6. External-field B distribution comparison",
                     "TODO: export B-field/flux-line plots for C1_N1_t060_x and C2_N4_t015_g008_x from AEDT.")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    plot_transverse_main()
    plot_mesh_boundary()
    plot_axial()
    plot_segmented_mu_experimental()
    plot_field_placeholders()


if __name__ == "__main__":
    main()
