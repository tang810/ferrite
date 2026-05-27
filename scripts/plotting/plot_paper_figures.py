import argparse
import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / "data" / "processed" / "metrics_table.csv"
VALIDATION = ROOT / "data" / "validation" / "layerwise_intH2_validation.csv"
OUTDIR = ROOT / "figures"


def f(value):
    try:
        text = str(value).strip()
        return float(text) if text else math.nan
    except ValueError:
        return math.nan


def finite(value):
    return math.isfinite(value)


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def save_placeholder(path, title, message):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis("off")
    ax.text(0.5, 0.62, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10, wrap=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"Wrote placeholder {path}")


def scatter(path, rows, x_key, y_key, title, xlabel, ylabel, group_key=None):
    import matplotlib.pyplot as plt

    points = []
    for row in rows:
        x = f(row.get(x_key, ""))
        y = f(row.get(y_key, ""))
        if finite(x) and finite(y):
            points.append((x, y, row))
    if not points:
        save_placeholder(path, title, f"Pending: no complete data for {x_key} versus {y_key}.")
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    groups = sorted(set(row.get(group_key, "") for _, _, row in points)) if group_key else [""]
    for group in groups:
        subset = [(x, y, row) for x, y, row in points if not group_key or row.get(group_key, "") == group]
        ax.scatter([p[0] for p in subset], [p[1] for p in subset], label=group or None)
        for x, y, row in subset:
            ax.annotate(row.get("case_id", ""), (x, y), fontsize=6)
    if group_key:
        ax.legend(fontsize=8)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"Wrote {path}")


def bar_metrics(path, rows):
    import matplotlib.pyplot as plt

    keys = ["etaS_star", "rhoH", "chiH"]
    complete = [row for row in rows if any(f(row.get(k, "")) == f(row.get(k, "")) for k in keys)]
    if not complete:
        save_placeholder(path, "Fig. 5 etaS*, rhoH, chiH comparison", "Pending: no complete metric rows available.")
        return
    labels = [row["case_id"] for row in complete]
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    for ax, key in zip(axes, keys):
        values = [f(row.get(key, "")) for row in complete]
        values = [0 if not finite(v) else v for v in values]
        ax.bar(labels, values)
        ax.set_ylabel(key)
        ax.grid(True, axis="y", alpha=0.3)
    axes[-1].tick_params(axis="x", rotation=45, labelsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"Wrote {path}")


def layer_fraction(path, rows):
    import matplotlib.pyplot as plt

    complete = []
    for row in rows:
        total = f(row.get("IntH2_total", ""))
        vals = [f(row.get(f"IntH2_L{i}", "")) for i in range(1, 7)]
        vals = [v for v in vals if finite(v)]
        if finite(total) and abs(total) > 0 and vals:
            complete.append((row["case_id"], [v / total for v in vals]))
    if not complete:
        save_placeholder(path, "Fig. 6 layerwise IntH2 fraction", "Pending: no complete layerwise IntH2 exports.")
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bottoms = [0] * len(complete)
    labels = [case for case, _ in complete]
    max_layers = max(len(vals) for _, vals in complete)
    for i in range(max_layers):
        vals = [layers[i] if i < len(layers) else 0 for _, layers in complete]
        ax.bar(labels, vals, bottom=bottoms, label=f"L{i+1}")
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_ylabel("IntH2_Li / IntH2_total")
    ax.legend()
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate paper figures or pending-data placeholders.")
    parser.add_argument("--metrics", type=Path, default=METRICS)
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()

    rows = read_csv(args.metrics)
    args.outdir.mkdir(parents=True, exist_ok=True)

    scatter(args.outdir / "Fig3_SFx_vs_Vf.png", rows, "Vf_mm3", "SFx", "Fig. 3 SFx versus Vf", "Vf (mm^3)", "SFx", "model_type")
    scatter(args.outdir / "Fig4_IntH2_vs_Vf.png", rows, "Vf_mm3", "IntH2_total", "Fig. 4 IntH2_total,x versus Vf", "Vf (mm^3)", "IntH2_total,x")
    bar_metrics(args.outdir / "Fig5_eta_chi_comparison.png", rows)
    layer_fraction(args.outdir / "Fig6_layerwise_IntH2_fraction.png", rows)
    scatter(args.outdir / "Fig7_SFx_vs_Tspace.png", rows, "T_space_mm", "SFx", "Fig. 7 SFx versus total radial occupation", "T_space (mm)", "SFx", "N_layers")
    scatter(args.outdir / "Fig8_axial_vs_transverse_selected.png", rows, "SFx", "SFz", "Fig. 8 axial versus transverse selected candidates", "SFx", "SFz")
    scatter(args.outdir / "Fig9_segmented_penalty.png", rows, "slot_pattern", "SFx", "Fig. 9 segmented penalty", "slot pattern", "SFx")


if __name__ == "__main__":
    main()
