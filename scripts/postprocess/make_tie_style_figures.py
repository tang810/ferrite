from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "figures_tie"
DATA = ROOT / "analysis_ready" / "matlab_B_results"


COLORS = {
    "ferrite": "#2f2f2f",
    "amorphous": "#1f77b4",
    "nanocrystalline": "#d62728",
    "p0": "#2ca02c",
    "cap": "#9467bd",
    "gray": "#7f7f7f",
}


def setup_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.3,
            "savefig.dpi": 600,
            "figure.dpi": 160,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def savefig(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.13,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def clean_axes(ax: plt.Axes, grid: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(True, axis="y", color="#d9d9d9", linewidth=0.6, alpha=0.8)
        ax.set_axisbelow(True)


def fig01_concept() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.55), constrained_layout=True)

    # (a) multilayer ferrite base, radial cross-section
    ax = axes[0]
    ax.set_aspect("equal")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    radii = [0.62, 0.73, 0.84, 0.95]
    for i, r in enumerate(radii):
        ax.add_patch(Circle((0, 0), r, fill=False, lw=2.0, ec=COLORS["ferrite"]))
        ax.add_patch(Circle((0, 0), r - 0.045, fill=False, lw=1.2, ec="#b0b0b0"))
    ax.add_patch(Circle((0, 0), 0.45, fill=False, lw=1.2, ls="--", ec="#555555"))
    ax.text(0, 0, "Sensor\nregion", ha="center", va="center")
    ax.annotate("4 ferrite layers", xy=(0.9, 0.2), xytext=(0.25, 1.12),
                arrowprops=dict(arrowstyle="->", lw=0.8), ha="center")
    ax.axis("off")
    panel_label(ax, "(a)")

    # (b) outer high-permeability layer
    ax = axes[1]
    ax.set_aspect("equal")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    for r in radii:
        ax.add_patch(Circle((0, 0), r, fill=False, lw=1.4, ec=COLORS["ferrite"]))
    ax.add_patch(Circle((0, 0), 1.08, fill=False, lw=2.6, ec=COLORS["nanocrystalline"]))
    ax.text(0, 1.20, "outer high-$\\mu$ layer", ha="center", va="top")
    ax.add_patch(FancyArrowPatch((-1.25, 0), (-1.0, 0), arrowstyle="->", mutation_scale=10, lw=1.0))
    ax.text(-1.20, 0.12, "$B_x$", ha="left")
    ax.axis("off")
    panel_label(ax, "(b)")

    # (c) axial cap and residual field direction
    ax = axes[2]
    ax.set_xlim(-0.2, 3.0)
    ax.set_ylim(-1.2, 1.2)
    ax.add_patch(Rectangle((0.45, -0.62), 1.85, 1.24, fill=False, lw=2.0, ec=COLORS["ferrite"]))
    for x in [0.58, 0.72, 0.86, 1.0]:
        ax.plot([x, x], [-0.62, 0.62], color="#666666", lw=0.8)
    ax.add_patch(Rectangle((2.37, -0.72), 0.12, 1.44, color=COLORS["nanocrystalline"], alpha=0.95))
    ax.add_patch(Circle((1.38, 0), 0.08, color="#111111"))
    ax.text(1.38, -0.22, "magnetometer", ha="center")
    ax.add_patch(FancyArrowPatch((1.45, 1.03), (1.45, 0.72), arrowstyle="->", mutation_scale=10, lw=1.0))
    ax.text(1.55, 1.0, "$B_z$", va="center")
    ax.text(2.43, 0.88, "single\ncap", ha="center")
    ax.axis("off")
    panel_label(ax, "(c)")

    savefig(fig, "Fig01_concept_hybrid_multilayer_shield")


def fig02_structure_basis() -> None:
    basis = pd.read_csv(DATA / "current_paper_structure_basis.csv").iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.35), constrained_layout=True)

    ax = axes[0]
    params = ["Rin", "L", "N", "t", "g", "Tspace"]
    values = [
        f"{basis.Rin_mm:.0f} mm",
        f"{basis.L_mm:.0f} mm",
        f"{int(basis.N)}",
        f"{basis.layer_t_mm:.2f} mm",
        f"{basis.gap_mm:.2f} mm",
        f"{basis.radial_Tspace_mm:.2f} mm",
    ]
    ax.axis("off")
    y = 0.88
    ax.text(0.02, 0.98, "Four-layer ferrite validation base", fontsize=9, fontweight="bold", va="top")
    for p, v in zip(params, values):
        ax.text(0.05, y, p, ha="left", va="center", color="#333333")
        ax.text(0.42, y, v, ha="left", va="center", fontweight="bold")
        y -= 0.13
    ax.text(
        0.02,
        0.08,
        "Selected as a manufacturable validation candidate,\nnot claimed as a global optimum.",
        ha="left",
        va="bottom",
        fontsize=7,
        color="#555555",
    )
    panel_label(ax, "(a)")

    ax = axes[1]
    metrics = ["SFx", "IntH2"]
    vals = [basis.SFx, basis.IntH2_total]
    x = np.arange(2)
    bars = ax.bar(x, vals, color=[COLORS["ferrite"], "#9e9e9e"], width=0.55)
    ax.set_xticks(x, metrics)
    ax.set_yscale("log")
    ax.set_ylabel("Metric value")
    ax.set_title("Baseline performance")
    clean_axes(ax)
    for b, txt in zip(bars, [f"{basis.SFx:.2f}", f"{basis.IntH2_total:.2e}"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.12, txt, ha="center", va="bottom", fontsize=7)
    panel_label(ax, "(b)")

    savefig(fig, "Fig02_ferrite_base_selection")


def fig03_hybrid() -> None:
    df = pd.read_csv(DATA / "current_paper_hybrid_enhancement.csv")
    labels = ["Ferrite", "+AM", "+NC"]
    colors = [COLORS["ferrite"], COLORS["amorphous"], COLORS["nanocrystalline"]]
    x = np.arange(len(df))

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.55), constrained_layout=True)

    ax = axes[0]
    bars = ax.bar(x, df["SFx"], color=colors, width=0.58)
    ax.set_xticks(x, labels)
    ax.set_ylabel("SFx")
    ax.set_title("Transverse shielding factor")
    clean_axes(ax)
    for b, v in zip(bars, df["SFx"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.55, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    panel_label(ax, "(a)")

    ax = axes[1]
    bars = ax.bar(x, df["IntH2_total"], color=colors, width=0.58)
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel("IntH2 total")
    ax.set_title("Noise-related integral")
    clean_axes(ax)
    for b, v in zip(bars, df["IntH2_total"]):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.35, f"{v:.1e}", ha="center", va="bottom", fontsize=7)
    panel_label(ax, "(b)")

    savefig(fig, "Fig03_hybrid_outer_layer_enhancement")


def fig04_axial_cap() -> None:
    df = pd.read_csv(DATA / "current_paper_axial_cap_tradeoff.csv")
    labels = ["Open", "P0", "+NC cap"]
    colors = [COLORS["ferrite"], COLORS["p0"], COLORS["cap"]]
    x = np.arange(len(df))

    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.55), constrained_layout=True)

    ax = axes[0]
    bars = ax.bar(x, df["SFz"], color=colors, width=0.58)
    ax.set_xticks(x, labels)
    ax.set_ylabel("SFz")
    ax.set_title("Axial shielding")
    clean_axes(ax)
    for b, v in zip(bars, df["SFz"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.04, f"{v:.2f}", ha="center", fontsize=7)
    panel_label(ax, "(a)")

    ax = axes[1]
    bars = ax.bar(x, df["IntH2_total"], color=colors, width=0.58)
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel("IntH2 total")
    ax.set_title("Noise proxy")
    clean_axes(ax)
    for b, v in zip(bars, df["IntH2_total"]):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.35, f"{v:.1e}", ha="center", fontsize=7)
    panel_label(ax, "(b)")

    ax = axes[2]
    bars = ax.bar(x, df["LeakageRatioz"], color=colors, width=0.58)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Leakage ratio")
    ax.set_title("$B_{center}/B_0$")
    clean_axes(ax)
    for b, v in zip(bars, df["LeakageRatioz"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.3f}", ha="center", fontsize=7)
    panel_label(ax, "(c)")

    savefig(fig, "Fig04_axial_cap_tradeoff")


def fig05_geomag() -> None:
    df = pd.read_csv(DATA / "current_paper_geomagnetic_residual_estimates.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.45), sharey=True, constrained_layout=True)

    for ax, direction, title in zip(axes, ["x", "z"], ["Transverse field", "Axial field"]):
        sub = df[df["field_dir"] == direction].copy()
        if direction == "x":
            labels = ["Ferrite", "+AM", "+NC"]
            colors = [COLORS["ferrite"], COLORS["amorphous"], COLORS["nanocrystalline"]]
        else:
            labels = ["Open", "P0", "+NC cap"]
            colors = [COLORS["ferrite"], COLORS["p0"], COLORS["cap"]]
        x = np.arange(len(sub))
        bars = ax.bar(x, sub["Bcenter_geo_uT"], color=colors, width=0.58)
        ax.set_xticks(x, labels)
        ax.set_title(title)
        ax.set_ylabel("Residual field under 50 uT (uT)")
        clean_axes(ax)
        for b, v in zip(bars, sub["Bcenter_geo_uT"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.35, f"{v:.2f}", ha="center", fontsize=7)
    panel_label(axes[0], "(a)")
    panel_label(axes[1], "(b)")
    savefig(fig, "Fig05_geomagnetic_residual_estimate")


def fig06_loss_sensitivity() -> None:
    df = pd.read_csv(DATA / "current_paper_material_loss_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(3.5, 2.6), constrained_layout=True)
    order = [
        ("x_amorphous", "+AM outer", COLORS["amorphous"], "s"),
        ("x_nanocrystalline", "+NC outer", COLORS["nanocrystalline"], "o"),
        ("z_p0_amorphous_shell_cap", "P0 AM cap", COLORS["p0"], "^"),
        ("z_single_nanocrystalline_cap", "NC cap", COLORS["cap"], "d"),
    ]
    for key, label, color, marker in order:
        sub = df[df["case_label"] == key]
        if sub.empty:
            continue
        ax.plot(
            sub["mu_pp_non_ferrite_over_ferrite"],
            sub["noise_amp_ratio_vs_reference"],
            color=color,
            marker=marker,
            ms=3.8,
            label=label,
        )
    ax.axhline(1, color="#555555", lw=0.9, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\mu''_{metal}/\mu''_{ferrite}$")
    ax.set_ylabel("Noise amplitude ratio")
    ax.set_title("Material-loss sensitivity")
    clean_axes(ax)
    ax.legend(frameon=False, loc="best")
    savefig(fig, "Fig06_material_loss_sensitivity")


def write_caption_manifest() -> None:
    captions = [
        ("Fig. 1", "Concept of the hybrid multilayer ferrite shield for magnetometer applications. (a) Four-layer ferrite base. (b) Outer amorphous or nanocrystalline high-permeability layer. (c) Single-ended cap and magnetometer placement."),
        ("Fig. 2", "Four-layer ferrite validation base. (a) Geometrical parameters of the selected manufacturable candidate. (b) Baseline shielding factor and IntH2 metric summary."),
        ("Fig. 3", "Hybrid outer-layer enhancement in the transverse field direction. AM: amorphous; NC: nanocrystalline. (a) Shielding factor SFx. (b) Noise-related integral IntH2 total."),
        ("Fig. 4", "Axial cap tradeoff. NC: nanocrystalline. (a) Axial shielding factor SFz. (b) IntH2 total. (c) Leakage ratio."),
        ("Fig. 5", "Estimated residual field under a 50 uT geomagnetic field using linear SF scaling. AM: amorphous; NC: nanocrystalline. (a) Transverse field. (b) Axial field."),
        ("Fig. 6", "Sensitivity of the noise-amplitude proxy to the assumed magnetic loss of amorphous or nanocrystalline materials."),
    ]
    lines = ["# TIE-style figure manifest", ""]
    for fig, cap in captions:
        stem = {
            "Fig. 1": "Fig01_concept_hybrid_multilayer_shield",
            "Fig. 2": "Fig02_ferrite_base_selection",
            "Fig. 3": "Fig03_hybrid_outer_layer_enhancement",
            "Fig. 4": "Fig04_axial_cap_tradeoff",
            "Fig. 5": "Fig05_geomagnetic_residual_estimate",
            "Fig. 6": "Fig06_material_loss_sensitivity",
        }[fig]
        lines.append(f"## {fig}")
        lines.append("")
        lines.append(f"- PNG: `paper/figures_tie/{stem}.png`")
        lines.append(f"- Caption: {cap}")
        lines.append("")
    (OUT / "figure_manifest.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    setup_style()
    print("making Fig01")
    fig01_concept()
    print("making Fig02")
    fig02_structure_basis()
    print("making Fig03")
    fig03_hybrid()
    print("making Fig04")
    fig04_axial_cap()
    print("making Fig05")
    fig05_geomag()
    print("making Fig06")
    fig06_loss_sensitivity()
    write_caption_manifest()
    print(f"Wrote figures to {OUT}")


if __name__ == "__main__":
    main()
