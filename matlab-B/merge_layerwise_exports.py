"""
merge_layerwise_exports.py
==========================
Merges the newly exported layer-wise IntH2 CSV files into the main
all_results_clean.csv, producing an enhanced input for analyze_for_paper.m.

The export files use object-specific Expression names:
  2ceng: IntH2_cyl2=L1, IntH2_cyl4=L2
  3ceng: IntH2_s1=L1, IntH2_s2=L2, IntH2_s3=L3
  4ceng: IntH2_s1=L1, IntH2_s2=L2, IntH2_s3=L3, InH2_s4=L4

Output: all_results_layerwise.csv (same rows, added IntH2_L1..L4 cols)
"""

import csv
import os
import re

BASE = r"D:\ferrite\aaaaaaaaximukeji"
EXPORT_DIR = os.path.join(BASE, "analysis_ready")
INPUT_CSV = os.path.join(EXPORT_DIR, "all_results_clean.csv")
OUTPUT_CSV = os.path.join(EXPORT_DIR, "all_results_layerwise.csv")


def parse_value(raw):
    """Parse a numeric value with optional unit suffix (mm, etc.)"""
    if raw is None or raw == '' or raw == 'nan':
        return None
    raw = str(raw).strip()
    # Remove unit suffix like 'mm'
    m = re.match(r'([-+]?[0-9]+\.?[0-9]*(?:[eE][-+]?[0-9]+)?)', raw)
    if m and m.group(1):
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def read_export(path):
    """Read a Maxwell export CSV. Returns list of dicts with keys:
    variation, T_mm, a_mm, g_mm, IntH2_total, IntH2_L1..L8, B0_T, Bcenter_T
    """
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Clean header: strip unit annotations like ': None'
        clean_header = []
        for h in header:
            h = h.strip()
            # Remove ': None' suffix
            h = re.sub(r':\s*None', '', h).strip()
            clean_header.append(h)

        # Build column index map
        col_idx = {}
        for i, name in enumerate(clean_header):
            col_idx[name.lower().replace(' ', '_')] = i

        for line in reader:
            row = {}
            # Variation number
            if 'variation' in col_idx:
                row['variation'] = int(line[col_idx['variation']])

            # T, a, g
            for key in ['t', 'a', 'g']:
                if key in col_idx:
                    row[key + '_mm'] = parse_value(line[col_idx[key]])

            # IntH2_total (after lower(): 'inth2_total')
            for total_name in ['inth2_total']:
                if total_name in col_idx:
                    row['IntH2_total'] = parse_value(line[col_idx[total_name]])

            # Layer-wise expressions: different names per project
            # 2ceng: IntH2_cyl2 (L1), IntH2_cyl4 (L2)
            # 3ceng: IntH2_s1 (L1), IntH2_s2 (L2), IntH2_s3 (L3)
            # 4ceng: IntH2_s1 (L1), IntH2_s2 (L2), IntH2_s3 (L3), InH2_s4 (L4)
            # 5ceng+: IntH2_s1..IntH2_sN expected
            layer_map = {
                'IntH2_L1': ['intH2_cyl2', 'intH2_s1'],
                'IntH2_L2': ['intH2_cyl4', 'intH2_s2'],
                'IntH2_L3': ['intH2_s3'],
                'IntH2_L4': ['intH2_s4', 'inh2_s4'],
                'IntH2_L5': ['intH2_s5'],
                'IntH2_L6': ['intH2_s6'],
                'IntH2_L7': ['intH2_s7'],
                'IntH2_L8': ['intH2_s8'],
            }
            for out_name, candidates in layer_map.items():
                for cand in candidates:
                    if cand in col_idx:
                        row[out_name] = parse_value(line[col_idx[cand]])
                        break

            # B0_T and Bcenter_T for shielding factor
            for bcol in ['b0_t', 'bcenter_t']:
                if bcol in col_idx:
                    row[bcol] = parse_value(line[col_idx[bcol]])

            rows.append(row)
    return rows


def match_row(main_row, export_rows, experiment, layer):
    """Find the matching export row for a given main table row."""
    a_exp = main_row['a_mm']
    g_exp = main_row['g_mm']
    t_exp = main_row['T_mm']

    # Match by IntH2_total value (most reliable)
    for ex in export_rows:
        if ex.get('IntH2_total') is not None and main_row.get('IntH2_total') is not None:
            if abs(ex['IntH2_total'] - main_row['IntH2_total']) / max(abs(main_row['IntH2_total']), 1e-30) < 0.01:
                return ex

    # Fallback: match by geometry (for agmatrix where T,a,g are all available)
    for ex in export_rows:
        a_ex = ex.get('a_mm')
        g_ex = ex.get('g_mm')
        t_ex = ex.get('t_mm')

        match_a = a_ex is not None and abs(a_ex - a_exp) < 0.001
        match_g = (g_ex is None and g_exp == 0) or (g_ex is not None and abs(g_ex - g_exp) < 0.001)
        match_t = t_ex is not None and abs(t_ex - t_exp) < 0.01

        if match_a and match_g and match_t:
            return ex

    return None


def main():
    # Read existing clean data
    main_rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ['T_mm', 'a_mm', 'g_mm', 'IntH2_total']:
                if key in row and row[key]:
                    row[key] = float(row[key])
            for key in ['layer']:
                if key in row:
                    row[key] = int(float(row[key]))
            main_rows.append(row)

    # Read all export files
    export_files = {
        ('asweep', 1): 'export_1ceng_asweep.csv',
        ('Tcompare', 1): 'export_1ceng_Tcompare.csv',
        ('asweep', 2): 'export_2ceng_asweep.csv',
        ('Tcompare', 2): 'export_2ceng_Tcompare.csv',
        ('agmatrix', 2): 'export_2ceng_agmatrix.csv',
        ('asweep', 3): 'export_3ceng_asweep.csv',
        ('Tcompare', 3): 'export_3ceng_Tcompare.csv',
        ('agmatrix', 3): 'export_3ceng_agmatrix.csv',
        ('asweep', 4): 'export_4ceng_asweep.csv',
        ('Tcompare', 4): 'export_4ceng_Tcompare.csv',
        ('agmatrix', 4): 'export_4ceng_agmatrix.csv',
        # Next-round experiments (5-7 layers)
        ('fixedT10_g02', 5): 'export_5ceng_fixedT10_g02.csv',
        ('fixedT10_g02', 6): 'export_6ceng_fixedT10_g02.csv',
        ('fixedT10_g02', 7): 'export_7ceng_fixedT10_g02.csv',
    }

    export_cache = {}
    for (exp, layer), fname in export_files.items():
        path = os.path.join(EXPORT_DIR, fname)
        if os.path.exists(path):
            export_cache[(exp, layer)] = read_export(path)
            print(f"Read {fname}: {len(export_cache[(exp, layer)])} rows")
        else:
            print(f"WARNING: {fname} not found")

    # Merge: for each main row, find matching export row
    matched = 0
    unmatched = 0
    for row in main_rows:
        exp = row['experiment']
        layer = row['layer']
        key = (exp, layer)

        if key not in export_cache:
            # Single layer: IntH2_L1 = IntH2_total
            if layer == 1:
                row['IntH2_L1'] = row.get('IntH2_total', None)
            unmatched += 1
            continue

        ex_row = match_row(row, export_cache[key], exp, layer)
        if ex_row:
            for lname in ['IntH2_L1', 'IntH2_L2', 'IntH2_L3', 'IntH2_L4']:
                if lname in ex_row:
                    row[lname] = ex_row[lname]
            matched += 1
        else:
            print(f"  No match: exp={exp}, layer={layer}, a={row['a_mm']}, g={row['g_mm']}, T={row['T_mm']}")
            unmatched += 1

    print(f"\nMatched: {matched}, Unmatched: {unmatched}")

    # Write output
    fieldnames = ['experiment', 'layer', 'T_mm', 'a_mm', 'g_mm',
                  'IntH2_total',
                  'IntH2_L1', 'IntH2_L2', 'IntH2_L3', 'IntH2_L4',
                  'IntH2_L5', 'IntH2_L6', 'IntH2_L7', 'IntH2_L8',
                  'B0_T', 'Bcenter_T']
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(main_rows)

    print(f"Wrote {OUTPUT_CSV} ({len(main_rows)} rows)")
    print("\nLayer-wise data summary:")
    for lname in ['IntH2_L1', 'IntH2_L2', 'IntH2_L3', 'IntH2_L4',
                   'IntH2_L5', 'IntH2_L6', 'IntH2_L7', 'IntH2_L8',
                   'B0_T', 'Bcenter_T']:
        count = sum(1 for r in main_rows if lname in r and r[lname] is not None)
        print(f"  {lname}: {count} rows")


if __name__ == '__main__':
    main()
