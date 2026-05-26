# Manufacturable thin ferrite simulation plan

This experiment replaces the earlier thick-shell assumption with constraints from the physical prototype:

```text
ferrite sheet thickness: 0.08 mm <= t <= 0.60 mm
```

The prototype is not an ideal continuous cylinder. It is closer to ferrite sheets or strips wrapped around a cylindrical support, so two model levels are needed.

## Level 1: continuous-shell screening

Use a continuous cylindrical ferrite shell first. This is fast and gives the trend for:

- layer count `N_layers`
- per-layer ferrite thickness `t_ferrite_mm`
- radial air/adhesive gap `g_radial_mm`
- total ferrite thickness `T_ferrite_total_mm`
- center shielding factor `SF`
- noise source indicator `IntH2_total`

The first screening matrix is:

```text
manufacturable_thin_ferrite_sim_matrix.csv
stage = screen_continuous
```

This answers whether multilayering is even promising when every ferrite layer is limited to 0.08--0.60 mm.

## Level 2: segmented-shell 3D correction

After screening, simulate only the best few candidates as true segmented 3D shells:

- `N_segments`: number of ferrite strips around the circumference
- `circumferential_gap_mm`: physical gap between adjacent strips
- `coverage_phi`: circumferential ferrite coverage fraction

This checks how much the real slots reduce shielding performance.

## Required exports

For every candidate:

1. Use the same no-shield reference model to export `B0_T`, `B0_Bx_T`, `B0_By_T`, `B0_Bz_T`.
2. Export the shielded center field:

```text
Bcenter_T
Bcenter_Bx_T
Bcenter_By_T
Bcenter_Bz_T
```

3. Export magnetic-noise indicators:

```text
IntH2_total
IntH2_L1, IntH2_L2, ...
```

Compute:

```text
SF = abs(B0_T) / abs(Bcenter_T)
ResidualRatio = abs(Bcenter_T) / abs(B0_T)
eta_S = ln(SF) / V_f
```

## Decision rule

A multilayer candidate supports the material-saving claim only if:

```text
SF_multi >= SF_target
V_multi < V_single_at_same_SF
IntH2_total_multi <= acceptable noise limit
```

If the segmented 3D result is much worse than the continuous-shell result, report the segmentation penalty and optimize the circumferential gap before claiming material savings.
