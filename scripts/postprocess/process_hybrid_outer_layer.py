"""Build paper-ready hybrid outer-layer tables and figures.

Inputs:
  data/raw/hybrid_outer_layer_exports.csv
  data/processed/metrics_table.csv

Outputs:
  data/processed/hybrid_outer_layer_metrics.csv
  figures/Fig_hybrid_outer_layer_SFx.png
  figures/Fig_hybrid_outer_layer_IntH2.png
  figures/Fig_hybrid_outer_layer_tradeoff.png
  paper/hybrid_outer_layer_results_snippet.md
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_HYBRID = ROOT / "data" / "raw" / "hybrid_outer_layer_exports.csv"
METRICS = ROOT / "data" / "processed" / "metrics_table.csv"
OUT_CSV = ROOT / "data" / "processed" / "hybrid_outer_layer_metrics.csv"
FIG_DIR = ROOT / "figures"
SNIPPET = ROOT / "paper" / "hybrid_outer_layer_results_snippet.md"

BASE_CASE = "C2_N4_t015_g008_x"
BASE_LABEL = "Ferrite only"
BASE_THICKNESS_MM = 0.0
BASE_GAP_MM = 0.0
BASE_MATERIAL = "ferrite"
BASE_MU = ""


FIELDNAMES = [
    "display_order",
    "case_id",
    "label",
    "base_case",
    "outer_material",
    "outer_total_t_mm",
    "outer_gap_from_ferrite_mm",
    "outer_mu_r_prime",
    "B0_Bx_T",
    "Bcenter_Bx_T",
    "Bcenter_Mag_T",
    "SFx",
    "ResidualRatiox",
    "SFx_gain_vs_ferrite",
    "IntH2_total",
    "IntH2_outer",
    "IntH2_ratio_vs_ferrite",
    "chiH",
    "status",
    "selected_candidate",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def f(value: object, default: float = math.nan) -> float:
    try:
        text = str(value).strip()
        return float(text) if text else default
    except (TypeError, ValueError):
        return default


def fmt(value: float, digits: int = 12) -> str:
    if not math.isfinite(value):
        return ""
    return f"{value:.{digits}g}"


def material_label(material: str) -> str:
    if material == "nanocrystalline":
        return "Ferrite + nanocrystalline"
    if material == "amorphous":
        return "Ferrite + amorphous"
    return BASE_LABEL


def get_base_row() -> dict[str, str]:
    rows = read_csv(METRICS)
    for row in rows:
        if row.get("case_id") == BASE_CASE:
            sfx = f(row.get("SFx"))
            int_h2 = f(row.get("IntH2_total"))
            return {
                "display_order": "1",
                "case_id": BASE_CASE,
                "label": BASE_LABEL,
                "base_case": BASE_CASE,
                "outer_material": BASE_MATERIAL,
                "outer_total_t_mm": fmt(BASE_THICKNESS_MM, 4),
                "outer_gap_from_ferrite_mm": fmt(BASE_GAP_MM, 4),
                "outer_mu_r_prime": BASE_MU,
                "B0_Bx_T": row.get("B0_Bx_T", ""),
                "Bcenter_Bx_T": row.get("Bcenter_Bx_T", ""),
                "Bcenter_Mag_T": row.get("Bcenter_Mag_T", ""),
                "SFx": fmt(sfx),
                "ResidualRatiox": row.get("LeakageRatiox", ""),
                "SFx_gain_vs_ferrite": "1",
                "IntH2_total": fmt(int_h2),
                "IntH2_outer": "",
                "IntH2_ratio_vs_ferrite": "1",
                "chiH": row.get("chiH", ""),
                "status": "processed",
                "selected_candidate": "baseline",
                "notes": "four-layer ferrite-only baseline",
            }
    raise RuntimeError(f"Baseline row not found in {METRICS}")


def build_rows() -> list[dict[str, str]]:
    base = get_base_row()
    base_sfx = f(base["SFx"])
    base_int_h2 = f(base["IntH2_total"])

    out = [base]
    raw_rows = read_csv(RAW_HYBRID)
    exported = [row for row in raw_rows if row.get("status") == "exported"]
    material_order = {"amorphous": 2, "nanocrystalline": 3}
    exported.sort(key=lambda row: material_order.get(row.get("outer_material", ""), 99))

    for row in exported:
        sfx = f(row.get("SFx"))
        int_h2 = f(row.get("IntH2_total"))
        material = row.get("outer_material", "")
        out.append({
            "display_order": str(material_order.get(material, len(out) + 1)),
            "case_id": row.get("case_id", ""),
            "label": material_label(material),
            "base_case": row.get("base_case", BASE_CASE),
            "outer_material": material,
            "outer_total_t_mm": row.get("outer_total_t_mm", ""),
            "outer_gap_from_ferrite_mm": row.get("outer_gap_from_ferrite_mm", ""),
            "outer_mu_r_prime": row.get("outer_mu_r_prime", ""),
            "B0_Bx_T": row.get("B0_Bx_T", ""),
            "Bcenter_Bx_T": row.get("Bcenter_Bx_T", ""),
            "Bcenter_Mag_T": row.get("Bcenter_Mag_T", ""),
            "SFx": fmt(sfx),
            "ResidualRatiox": row.get("ResidualRatiox", ""),
            "SFx_gain_vs_ferrite": fmt(sfx / base_sfx),
            "IntH2_total": fmt(int_h2),
            "IntH2_outer": row.get("IntH2_outer", ""),
            "IntH2_ratio_vs_ferrite": fmt(int_h2 / base_int_h2),
            "chiH": row.get("chiH", ""),
            "status": row.get("status", ""),
            "selected_candidate": "yes" if material == "nanocrystalline" else "no",
            "notes": row.get("notes", ""),
        })
    return out


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def plot_figures(rows: list[dict[str, str]]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    labels = [row["label"] for row in rows]
    sfx = [f(row["SFx"]) for row in rows]
    int_h2 = [f(row["IntH2_total"]) for row in rows]
    colors = ["#666666", "#3f7fba", "#15995b"]

    plt.rcParams.update({
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 10,
    })

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.bar(labels, sfx, color=colors[: len(rows)])
    ax.set_ylabel("SFx")
    ax.set_title("Hybrid outer-layer transverse shielding factor")
    ax.grid(True, axis="y", alpha=0.3)
    for i, value in enumerate(sfx):
        ax.text(i, value, f"{value:.2f}", ha="center", va="bottom")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Fig_hybrid_outer_layer_SFx.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.bar(labels, int_h2, color=colors[: len(rows)])
    ax.set_yscale("log")
    ax.set_ylabel("IntH2_total")
    ax.set_title("Hybrid outer-layer magnetic-noise-related integral")
    ax.grid(True, axis="y", alpha=0.3, which="both")
    for i, value in enumerate(int_h2):
        ax.text(i, value, f"{value:.2e}", ha="center", va="bottom")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Fig_hybrid_outer_layer_IntH2.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    for label, x, y, color in zip(labels, int_h2, sfx, colors):
        ax.scatter(x, y, s=80, color=color, label=label)
    ax.set_xscale("log")
    ax.set_xlabel("IntH2_total")
    ax.set_ylabel("SFx")
    ax.set_title("SFx versus IntH2_total for hybrid outer-layer candidates")
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "Fig_hybrid_outer_layer_tradeoff.png", dpi=300)
    plt.close(fig)


def write_snippet(rows: list[dict[str, str]]) -> None:
    base = rows[0]
    amorphous = next(row for row in rows if row["outer_material"] == "amorphous")
    nano = next(row for row in rows if row["outer_material"] == "nanocrystalline")
    ratio_sfx = f(nano["SFx"]) / f(amorphous["SFx"])
    ratio_int = f(nano["IntH2_total"]) / f(amorphous["IntH2_total"])

    SNIPPET.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# Hybrid Outer-Layer Results Snippet

Under the same outer-layer geometry, with an outer-layer thickness of 0.20 mm
and a 0.40 mm radial assembly gap outside the four-layer ferrite shield, the
nanocrystalline case provides a larger transverse shielding factor and a lower
magnetic-noise-related integral than the amorphous case.

| Configuration | mu_r | SFx | SFx gain | IntH2_total | IntH2 ratio |
|---|---:|---:|---:|---:|---:|
| Four-layer ferrite baseline | 1000 | {f(base['SFx']):.3f} | 1.000 | {f(base['IntH2_total']):.3e} | 1.000 |
| Ferrite + amorphous outer layer | {amorphous['outer_mu_r_prime']} | {f(amorphous['SFx']):.3f} | {f(amorphous['SFx_gain_vs_ferrite']):.3f} | {f(amorphous['IntH2_total']):.3e} | {f(amorphous['IntH2_ratio_vs_ferrite']):.3f} |
| Ferrite + nanocrystalline outer layer | {nano['outer_mu_r_prime']} | {f(nano['SFx']):.3f} | {f(nano['SFx_gain_vs_ferrite']):.3f} | {f(nano['IntH2_total']):.3e} | {f(nano['IntH2_ratio_vs_ferrite']):.4f} |

The nanocrystalline outer layer gives approximately {ratio_sfx:.2f} times the
SFx of the amorphous outer-layer case and approximately {ratio_int:.3f} times
its IntH2_total. Therefore, for the current simulation assumptions, the
nanocrystalline outer layer is selected as the preferred P2 prototype candidate.

These results should be described as simulation-based screening results. The
outer-layer permeabilities, loss parameters, and electrical conductivities must
be replaced or checked against vendor data or measurements before making final
material claims, and magnetometer sensitivity must still be verified by PSD
measurements.
"""
    SNIPPET.write_text(text, encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    plot_figures(rows)
    write_snippet(rows)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {FIG_DIR / 'Fig_hybrid_outer_layer_SFx.png'}")
    print(f"Wrote {FIG_DIR / 'Fig_hybrid_outer_layer_IntH2.png'}")
    print(f"Wrote {FIG_DIR / 'Fig_hybrid_outer_layer_tradeoff.png'}")
    print(f"Wrote {SNIPPET}")


if __name__ == "__main__":
    main()
