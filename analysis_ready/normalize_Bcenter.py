import csv
import os


BASE_DIR = r"D:\tangyumengnew\aaaaaaaaximukeji"
IN_CSV = os.path.join(BASE_DIR, "analysis_ready", "Bcenter_1ceng_nominal.csv")
OUT_CSV = os.path.join(BASE_DIR, "analysis_ready", "Bcenter_1ceng_nominal_clean.csv")


def main():
    with open(IN_CSV, "r", newline="") as f:
        row = next(csv.DictReader(f))

    mag_b_ut = float(row["Mag_B [uTesla]"])
    mag_b_t = mag_b_ut * 1e-6

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case",
                "layer",
                "T_mm",
                "a_mm",
                "Rin_mm",
                "Bcenter_uT",
                "Bcenter_T",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "case": "1ceng_nominal_with_shield",
                "layer": 1,
                "T_mm": row["T [mm]"],
                "a_mm": row["a [mm]"],
                "Rin_mm": row["Rin [mm]"],
                "Bcenter_uT": mag_b_ut,
                "Bcenter_T": mag_b_t,
            }
        )

    print("Wrote {}".format(OUT_CSV))
    print("Bcenter_T = {:.12e}".format(mag_b_t))


if __name__ == "__main__":
    main()
