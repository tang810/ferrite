# Draft Introduction and Methods

## I. Introduction

Ultra-sensitive magnetic measurements require a magnetic environment with both low field and low magnetic noise. Atomic magnetometers, spin-exchange-relaxation-free (SERF) magnetometers, comagnetometers, magnetoencephalography systems, and precision-physics instruments are easily affected by static and low-frequency magnetic disturbances [1]-[5]. Passive magnetic shielding remains one of the most widely used approaches for generating such an environment, because high-permeability materials can shunt magnetic flux away from the protected volume [6]-[8]. However, when the sensor noise floor reaches the femtotesla level, the magnetic shield itself can become a limiting noise source rather than a passive mechanical enclosure [9], [10].

Metallic shields, especially permalloy and other high-permeability alloys, provide strong attenuation of static and low-frequency fields, but their high electrical conductivity introduces eddy-current magnetic noise [9], [11]. This noise is particularly important in the low-frequency band used by SERF magnetometers and related ultra-sensitive sensors. Ferrite materials provide an attractive alternative because they combine high magnetic permeability with much lower electrical conductivity than metallic shielding materials [12], [13]. Low-noise cylindrical ferrite shields have demonstrated that the eddy-current contribution can be strongly suppressed, and previous theoretical work has shown that the remaining low-frequency noise is mainly associated with hysteresis loss and the imaginary part of the complex permeability [9], [12]-[15]. A recent cubic ferrite shield further demonstrated the practical interest of low-noise ferrite shielding [16], but the present work addresses a different geometry: manufacturable multilayer cylindrical thin shells rather than a cubic panel enclosure.

Despite this advantage, a thick monolithic ferrite cylinder is difficult to fabricate and scale. Ferrites are brittle after sintering, machining large thin-walled cylinders is costly, and the available ferrite products are often sheets, strips, annuli, or small blocks rather than integral large shells. A manufacturable route is therefore to assemble the shield from multilayer thin-ferrite cylindrical shells. In such a structure, each ferrite layer can remain within the available sheet thickness range, while the total shielding ability is tuned through the layer number, radial gap, and total ferrite volume.

The multilayer thin-shell approach introduces a design problem that is not captured by simply increasing the wall thickness. Layer thickness, interlayer radial gaps, circumferential segmentation, and ferrite volume jointly affect the center leakage field, the shielding factor, and the magnetic-noise-related field-energy integral. For a finite open-ended cylindrical shell, transverse and axial shielding are not equivalent, and axial leakage through the open ends can be substantially different from transverse penetration through the sidewall [6], [27]-[29]. Gaps can increase magnetic leakage and redistribute the field inside the ferrite; additional layers can improve shielding but may also add magnetic material that contributes to hysteresis-related noise [14], [17], [24]. Therefore, the design must be judged by shielding performance, material usage, and a geometry-dependent magnetic-noise-related indicator at the same time.

This article develops a finite-element-based design and evaluation framework for multilayer cylindrical thin-ferrite shells. The innovation is threefold. First, it treats multilayer ferrite sheets as a manufacturable alternative to monolithic ferrite cylinders. Second, it evaluates shielding performance, ferrite volume, and magnetic-noise-related indicators in a coupled manner rather than optimizing shielding factor alone. Third, it uses continuous-shell simulations for rapid parameter screening and segmented-shell simulations to correct for realistic circumferential gaps. The framework separates two electromagnetic problems: an external uniform-field model for calculating the no-shield reference field, the shielded center field, and the shielding factor; and a virtual pickup-coil model for calculating layer-resolved \(\int H^2 dV\) indicators related to magnetic-noise generation. The study focuses on manufacturable ferrite layers with thicknesses of 0.08-0.60 mm; this range is retained as the current mechanical feasibility window and will be refined after mechanical-performance tests of the ferrite sheets. The objective is not to report demagnetization experiments or measured magnetic-noise spectra, but to establish a simulation-based basis for selecting practical multilayer ferrite-shell geometries.

The remainder of this article is organized as follows. Section II introduces the magnetic-noise-related model, the multilayer cylindrical geometry, the two finite-element calculation models, the data-export pipeline, and the comparison criteria. Section III defines the planned result structure for reference-field verification, transverse screening, fixed-volume comparison, layer-resolved \(\mathrm{IntH2}\), axial extension, segmented-shell correction, convergence checks, and permeability sensitivity. Section IV summarizes the expected design implications that will be replaced by result-supported conclusions after the simulation matrix is complete.

## II. Modeling and Analysis

### A. Coordinate Definition and Simulation Matrix

The cylindrical coordinate system is defined with the cylinder axis along the Cartesian \(z\)-axis. The \(x\)- and \(y\)-directions are transverse directions, and the \(z\)-direction is the axial direction. Because the investigated shield is a finite open-ended cylinder, the three directions are not assumed to be equivalent. An \(x\)-directed or \(y\)-directed external field evaluates transverse shielding, whereas a \(z\)-directed external field evaluates axial shielding through the open ends. The full shielding performance should therefore be reported as \(\mathrm{SF}_x\), \(\mathrm{SF}_y\), and \(\mathrm{SF}_z\), together with the corresponding leakage ratios. The current matrix starts with \(x\)-directed excitation as the transverse screening case and should be extended to \(z\)-directed excitation for axial shielding evaluation.

The finite-element screening matrix is summarized in Table I and Table II. The repository currently contains partial export tables for several manufacturable-thin cases; these partial files are treated as data-pipeline inputs only and are not interpreted as final paper results until the corresponding B0 reference, shielded center field, and layer-resolved \(\mathrm{IntH2}\) exports are complete and processed. The priority-1 matrix in Table II defines the main transverse continuous-shell study to be evaluated first. The \(N_L=6\) case is retained only as an optional high-layer-count case and will not be used as a main result unless its AEDT model is solved, exported, and processed.

**Table I. Repository Data Status at the Time of Drafting**

| Data group | Cases | Status in repository | Use in this draft |
|---|---|---|---|
| B0 reference | \(M0\_B0_x\) | planned/to be exported as standalone reference | defines required reference export |
| Continuous-shell priority-1 cases | \(N_L=1\), \(a=0.08/0.20/0.40/0.60\ \mathrm{mm}\); \(N_L=2\), \(a=0.20\ \mathrm{mm}\), \(g=0.10\ \mathrm{mm}\); \(N_L=3\), \(a=0.20\ \mathrm{mm}\), \(g=0.10\ \mathrm{mm}\); \(N_L=4\), \(a=0.15\ \mathrm{mm}\), \(g=0.08\ \mathrm{mm}\) | partial repository CSV rows exist; complete AEDT exports are still to be evaluated case by case | planned main matrix; no numerical conclusion is drawn here |
| Optional \(N_L=6\) case | \(N_L=6\), \(a=0.10\ \mathrm{mm}\), \(g=0.08\ \mathrm{mm}\) | planned optional case | not a main-result case unless solved/exported/processed |
| Axial-field extension | selected \(z\)-directed cases | planned | to be evaluated after transverse screening |
| Segmented-shell correction | aligned and staggered slots | planned | to be evaluated after continuous-shell screening |
| Permeability sensitivity | \(\mu_r'=500/1000/2000/5000\) | planned | to be evaluated after baseline pipeline is stable |

**Table II. Priority-1 and Planned Simulation Matrix**

| Parameter | Symbol | Values in current matrix | Notes |
|---|---:|---:|---|
| Inner radius | \(R_{\mathrm{in}}\) | 100 mm | cylindrical shield inner radius |
| Axial length | \(L\) | 200 mm | open-ended sidewall model |
| Priority-1 layer number | \(N_L\) | 1, 2, 3, 4 | main continuous-shell transverse screening |
| Optional layer number | \(N_L\) | 6 | optional, not used as main result unless exported and processed |
| Ferrite layer thickness | \(a\) | 0.08-0.60 mm | current manufacturable range; to be refined by mechanical tests |
| Radial gap | \(g\) | 0, 0.08, 0.10 mm | air/adhesive spacing between layers |
| Total ferrite thickness | \(T_f\) | 0.08-0.60 mm | \(T_f=N_La\) |
| Total radial occupation | \(T_{\mathrm{space}}\) | 0.08-1.00 mm | includes ferrite and radial gaps |
| Segment number | \(N_{\mathrm{seg}}\) | 12 | segmented-shell correction |
| Circumferential slot width | \(g_{\phi}\) | 1.6 mm | arc gap between adjacent strips |
| Coverage fraction | \(\eta_{\phi}\) | approximately 0.95 | computed at representative layer radius |
| External field direction | \(q\) | \(x\), planned \(z\) | \(x/y\): transverse; \(z\): axial |
| Relative permeability | \(\mu_r'\) | 500, 1000, 2000, 5000 | sensitivity analysis; 1000 is default screening value |
| Conductivity | \(\sigma\) | 0.01 S/m | screening value; replace with measured material data |

The priority-1 case list is: B0 reference; \(N_L=1\), \(a=0.08\), 0.20, 0.40, and 0.60 mm; \(N_L=2\), \(a=0.20\ \mathrm{mm}\), \(g=0.10\ \mathrm{mm}\); \(N_L=3\), \(a=0.20\ \mathrm{mm}\), \(g=0.10\ \mathrm{mm}\); and \(N_L=4\), \(a=0.15\ \mathrm{mm}\), \(g=0.08\ \mathrm{mm}\). All numerical trends from this matrix will be reported only after the corresponding AEDT exports have passed the post-processing and validation steps described below.

### B. Magnetic-Noise-Related Indicator

The magnetic field noise generated by a passive shield can be calculated from the dissipated power in the material through the fluctuation-dissipation theorem [9], [18]. A virtual pickup coil is placed at the observation point. For a coil with area \(A\), turn number \(N_c\), and angular frequency \(\omega=2\pi f\), the voltage noise spectral density induced by a magnetic field noise spectral density \(S_B(f)\) is

\[
S_V(f)=A^2N_c^2\omega^2S_B(f).
\]

The same voltage noise can be expressed as

\[
S_V(f)=4k_{\mathrm{B}}T R_{\mathrm{eff}}(f),
\]

where \(k_{\mathrm{B}}\) is the Boltzmann constant, \(T\) is the absolute temperature, and \(R_{\mathrm{eff}}\) is the effective resistance representing the material loss coupled to the virtual coil. In this article, the virtual coil current is written as

\[
I(t)=I_0\sin(\omega t),
\]

where \(I_0\) is the peak current. With this convention, the time-averaged dissipated power is

\[
P(f)=\frac{1}{2}I_0^2 R_{\mathrm{eff}}(f).
\]

The magnetic field noise amplitude spectral density is therefore

\[
\delta B(f)=\sqrt{S_B(f)}
=\frac{1}{A N_c I_0 \omega}\sqrt{8k_{\mathrm{B}}T P(f)}.
\]

For ferrites in the low-frequency range considered here, eddy-current loss is suppressed by the low electrical conductivity, and hysteresis loss is the dominant material-loss term [9], [12], [13]. The hysteresis power under the peak-field convention is written as

\[
P_{\mathrm{hyst}}=
\frac{1}{2}\omega \mu'' \int_V H_{\mathrm{vc}}^2\,dV,
\]

where \(H_{\mathrm{vc}}\) is the peak magnetic field strength generated by the virtual coil. The subscript "vc" is used to avoid confusion with the no-shield reference field \(B_0\) in the external-field model. The parameter \(\mu''\) is the absolute imaginary permeability in SI units. If the measured or supplied material property is the relative imaginary permeability \(\mu_r''\), then

\[
\mu''=\mu_0\mu_r''.
\]

Substitution gives

\[
\delta B_{\mathrm{hyst}}(f)
=\frac{1}{A N_c I_0}
\left(
\frac{2k_{\mathrm{B}}T\mu''}{\pi f}
\int_V H_{\mathrm{vc}}^2\,dV
\right)^{1/2}.
\]

Equivalently, the coil normalization can be expressed by the magnetic moment \(m=A N_c I_0\). In that form, \(N_c\) is absorbed into \(m\), and it must not be omitted independently:

\[
\delta B_{\mathrm{hyst}}(f)
=\frac{1}{m}
\left(
\frac{2k_{\mathrm{B}}T\mu''}{\pi f}
\int_V H_{\mathrm{vc}}^2\,dV
\right)^{1/2}.
\]

In the present finite-element study, the absolute noise amplitude is not claimed as a measured magnetic noise. Instead, the geometry-dependent quantity

\[
\mathrm{IntH2}=\int_V H_{\mathrm{vc}}^2\,dV
\]

is used as a magnetic-noise-related indicator. This indicator captures how a candidate geometry changes the material volume exposed to the virtual-coil magnetic field. It does not include sensor noise, environmental noise, vibration-induced noise, material batch variation, or experimental demagnetization state, and therefore it should not be interpreted as the final experimentally measured magnetic noise [19], [20].

For a multilayer shell, each ferrite layer is kept as an independent finite-element body. The layer-resolved indicators are

\[
\mathrm{IntH2}_{L_i}=\int_{V_{L_i}}H_{\mathrm{vc}}^2\,dV,\quad i=1,2,\ldots,N_L,
\]

and the total indicator is

\[
\mathrm{IntH2}_{\mathrm{total}}=
\sum_{i=1}^{N_L}\mathrm{IntH2}_{L_i}.
\]

The layer-resolved form is used because the innermost layer and the outer layers do not necessarily contribute equally to the total magnetic-noise-related source term.

### C. Multilayer Cylindrical Thin-Shell Geometry

The investigated structure is a multilayer cylindrical thin-ferrite shell. Unless otherwise stated, the continuous-shell screening model is an open-ended cylinder with inner radius \(R_{\mathrm{in}}\), axial length \(L\), layer number \(N_L\), single-layer ferrite thickness \(a\), and radial gap \(g\) between adjacent layers. The current simulation matrix uses

\[
R_{\mathrm{in}}=100\ \mathrm{mm},\quad L=200\ \mathrm{mm},
\]

and manufacturable ferrite layer thicknesses in the range

\[
0.08\ \mathrm{mm}\leq a\leq0.60\ \mathrm{mm}.
\]

The total ferrite thickness is

\[
T_f=N_La,
\]

and the total radial occupation thickness, including the interlayer gaps, is

\[
T_{\mathrm{space}}=N_La+(N_L-1)g.
\]

The outer radius of the multilayer shell is

\[
R_{\mathrm{out}}=R_{\mathrm{in}}+T_{\mathrm{space}}.
\]

For the \(i\)th layer, the inner and outer radii are

\[
R_{i,\mathrm{in}}=R_{\mathrm{in}}+(i-1)(a+g),
\]

\[
R_{i,\mathrm{out}}=R_{i,\mathrm{in}}+a.
\]

For a continuous open-ended cylindrical shell, the ferrite volume is

\[
V_f=\pi L\sum_{i=1}^{N_L}
\left(R_{i,\mathrm{out}}^2-R_{i,\mathrm{in}}^2\right).
\]

For a closed-ended variant, endcap volume should be added explicitly; it is not included in the open-ended sidewall model used for the current manufacturability screening. This distinction is important because endcaps can change both axial shielding and the virtual-coil field distribution [28], [29].

### D. Segmented-Shell Geometry

The segmented-shell model represents a practical assembly in which each cylindrical layer is made from \(N_{\mathrm{seg}}\) ferrite strips around the circumference. The circumferential gap between two adjacent strips is denoted by \(g_{\phi}\). Two slot arrangements are considered. In the aligned-slot model, all layers have the same angular slot positions, so the gaps can form a continuous magnetic-leakage path through the multilayer wall. In the staggered-slot model, the slot pattern of the \(i\)th layer is rotated by an offset angle \(\Delta\phi_i\), for example \(\Delta\phi_i=(i-1)\pi/N_{\mathrm{seg}}\), so that a gap in one layer is partially covered by ferrite in the neighboring layer. Comparing these two cases quantifies whether staggered assembly can reduce the segmentation penalty.

For a layer evaluated at the mean radius

\[
R_{i,\mathrm{m}}=\frac{R_{i,\mathrm{in}}+R_{i,\mathrm{out}}}{2},
\]

the total circumference is \(2\pi R_{i,\mathrm{m}}\). If each of the \(N_{\mathrm{seg}}\) slots has arc gap \(g_{\phi}\), the circumferential coverage fraction is defined as

\[
\eta_{\phi,i}
=1-\frac{N_{\mathrm{seg}}g_{\phi}}{2\pi R_{i,\mathrm{m}}}.
\]

When the layer thickness is much smaller than the radius, a single representative coverage fraction can be reported by using the innermost or mean shell radius. In the current segmented screening cases,

\[
N_{\mathrm{seg}}=12,\quad g_{\phi}=1.6\ \mathrm{mm},
\]

and \(\eta_{\phi}\) is approximately 0.95 for the \(R_{\mathrm{in}}=100\ \mathrm{mm}\) shell. The segmented ferrite volume is then approximated as

\[
V_{f,\mathrm{seg}}=
\sum_{i=1}^{N_L}\eta_{\phi,i}
\pi L\left(R_{i,\mathrm{out}}^2-R_{i,\mathrm{in}}^2\right),
\]

or calculated directly from the three-dimensional solid bodies in Maxwell. The segmented model is used to quantify the shielding and \(\mathrm{IntH2}\) penalty introduced by circumferential leakage gaps.

### E. External Uniform-Field Model for Shielding Factor

The first finite-element condition is the external uniform-field model. It is used only for calculating the no-shield reference field, the shielded center field, the shielding factor, and the leakage ratio. The field \(B_{\mathrm{center}}\) is the center leakage field under external excitation and is not a post-demagnetization remanent field.

For each field direction \(q\in\{x,y,z\}\), the reference model replaces the ferrite domains by vacuum, and the magnetic flux density at the cylinder center is recorded as \(B_{0,q}\). In the shielded model, the ferrite material is retained, and the corresponding center leakage field is recorded as \(B_{\mathrm{center},q}\). The directional shielding factor is

\[
\mathrm{SF}_q=\frac{|B_{0,q}|}{|B_{\mathrm{center},q}|},
\]

and the leakage ratio, also called the transmission ratio, is

\[
\mathrm{LeakageRatio}_q=
\frac{|B_{\mathrm{center},q}|}{|B_{0,q}|}
=\frac{1}{\mathrm{SF}_q}.
\]

For vector-field export, the center-field magnitude is calculated from

\[
B=\sqrt{B_x^2+B_y^2+B_z^2}.
\]

The external uniform field is applied using a tangential \(H\)-field boundary or the equivalent uniform magnetic-field setup in Maxwell. For an \(x\)-directed transverse case, the outer air-region boundaries are assigned so that the unshielded model produces a uniform \(H_{\mathrm{ext},x}\) at the center. The \(z\)-directed axial case is generated in the same way with the excitation direction rotated to the cylinder axis. The no-shield and shielded models use exactly the same air region, boundary condition, excitation amplitude, field direction, mesh-control strategy, and observation point; only the ferrite material assignment is changed.

### F. Virtual Pickup-Coil Model for \(\mathrm{IntH2}\)

The second finite-element condition is the virtual pickup-coil model. It is independent from the external uniform-field model and is used only to calculate \(\int H_{\mathrm{vc}}^2 dV\) and the layer-resolved \(\mathrm{IntH2}_{L_i}\) values. A circular virtual coil is placed at the cylinder center. The reproducible coil parameters for the current screening model are: coil radius \(r_c=2.5\ \mathrm{mm}\), coil area \(A=\pi r_c^2=19.635\ \mathrm{mm^2}\), turn number \(N_c=1\), and peak current \(I_0=1\ \mathrm{A}\). The coil normal defines the measurement direction. A coil normal along \(x\) gives \(\mathrm{IntH2}_x\), which corresponds to the transverse magnetic-noise-related indicator used in the present \(x\)-direction screening. For complete cylindrical-shield evaluation, the same calculation should be repeated with the coil normal along \(y\) and \(z\), giving \(\mathrm{IntH2}_y\) and \(\mathrm{IntH2}_z\).

For each ferrite layer, the Maxwell field calculator evaluates

\[
H_{\mathrm{vc}} \rightarrow |H_{\mathrm{vc}}| \rightarrow |H_{\mathrm{vc}}|^2
\rightarrow \int_{V_{L_i}} |H_{\mathrm{vc}}|^2 dV.
\]

The exported integral must be converted to SI volume units before it is used in the noise equation. If Maxwell exports the volume integration using \(\mathrm{mm}^3\) while \(H\) is in \(\mathrm{A/m}\), the conversion is

\[
\left[\int H^2dV\right]_{\mathrm{SI}}
=10^{-9}
\left[\int H^2dV\right]_{\mathrm{mm^3}},
\]

because \(1\ \mathrm{mm}^3=10^{-9}\ \mathrm{m}^3\). The SI unit of \(\int H^2dV\) is \(\mathrm{A^2\,m^{-1}}\).

### G. Maxwell Simulation Settings

The simulations are performed in ANSYS Maxwell, following the finite-element treatment commonly used for ferrite magnetic shields and enclosed shielding structures [13], [22], [23]. The external uniform-field cases are solved with the magnetostatic solver. The ferrite is modeled as a linear isotropic material in the first screening stage. The default screening values are relative permeability

\[
\mu_r'=1000
\]

and conductivity

\[
\sigma=0.01\ \mathrm{S/m}.
\]

These are not treated as final material constants. They are screening values based on the current AEDT material definition and the order of magnitude of Mn-Zn ferrite catalog properties, using TDK PC95 Mn-Zn ferrite as a catalog reference until the prototype material grade is fixed [26]. To test the robustness of the structural conclusions, a permeability sensitivity analysis is planned with

\[
\mu_r'=500,\ 1000,\ 2000,\ 5000.
\]

When measured material data are available, the static or low-frequency real permeability \(\mu_r'\), conductivity \(\sigma\), and relative imaginary permeability \(\mu_r''(f)\) will replace these screening values. The complex permeability can be measured following low-frequency ferrite-permeability methods and soft-magnetic core measurement standards [21], [25]. The imaginary part \(\mu_r''\) is not required for the magnetostatic shielding-factor calculation; it will be used in post-processing only if an absolute hysteresis-noise estimate is calculated from \(\mathrm{IntH2}\).

The surrounding region is assigned as air or vacuum. The air region is extended sufficiently beyond the shield so that the outer boundary does not distort the field near the cylinder; in implementation, the minimum distance from the shell to the outer boundary should be several times larger than \(R_{\mathrm{out}}\) and \(L/2\). A magnetic insulation boundary or equivalent open-region boundary is then applied to the outer boundary according to the solver setup. The same air-region size and boundary condition are used for the no-shield and shielded models.

Thin ferrite layers require local mesh refinement. Each layer thickness will be meshed with at least several elements across the radial direction, and additional refinement will be applied near radial gaps, circumferential slots, and layer edges. For segmented shells, the mesh will be further refined at the strip ends because magnetic leakage and field concentration occur near the slot boundaries. Convergence will be checked by monitoring \(B_{\mathrm{center},q}\), \(\mathrm{SF}_q\), and \(\mathrm{IntH2}_{\mathrm{total},q}\) rather than only the global energy error.

### H. Data Export and Post-Processing Pipeline

Each AEDT case will be exported before any paper-level metric is calculated. For every shielded case, the required external-field exports are

\[
B_{\mathrm{center},x},\quad B_{\mathrm{center},y},\quad
B_{\mathrm{center},z},\quad B_{\mathrm{center,Mag}},
\]

reported in tesla as `Bcenter_Bx_T`, `Bcenter_By_T`, `Bcenter_Bz_T`, and `Bcenter_Mag_T`. The virtual-coil model exports

\[
\mathrm{IntH2}_{\mathrm{total}},\quad
\mathrm{IntH2}_{L_1},\ldots,\mathrm{IntH2}_{L_N}.
\]

The B0 reference model is exported separately for each external-field direction as

\[
B_{0,x},\quad B_{0,y},\quad B_{0,z},\quad B_{0,\mathrm{Mag}},
\]

reported as `B0_Bx_T`, `B0_By_T`, `B0_Bz_T`, and `B0_Mag_T`.

The repository post-processing pipeline is organized as follows. The script `build_dataset.py` merges the simulation matrix, B0 reference exports, and shielded-case exports into a single dataset. The script `compute_metrics.py` calculates \(\mathrm{SF}_q\), \(\mathrm{LeakageRatio}_q\), \(V_f\), \(\eta_S\), \(\eta_S^*\), \(\rho_H\), and \(\chi_H\). The script `validate_layerwise_intH2.py` checks whether \(\mathrm{IntH2}_{\mathrm{total}}\) is consistent with \(\sum_i \mathrm{IntH2}_{L_i}\). The script `plot_paper_figures.py` generates the figures planned for Section III after the processed dataset contains the required exports. Missing quantities remain blank and are not interpreted as zero.

**Table III. Simulation Status Table**

| case_id | model_type | field_dir | coil_dir | \(N_L\) | \(a\) (mm) | \(g\) (mm) | \(T_f\) (mm) | \(T_{\mathrm{space}}\) (mm) | segment_pattern | status | exported_quantities | used_in_paper |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| M0_B0_x | no_shield | x | - | 0 | 0 | 0 | 0 | 0 | none | planned | B0 components and magnitude | no |
| C1_N1_t008_x | continuous_shell | x | x | 1 | 0.08 | 0 | 0.08 | 0.08 | none | planned | Bcenter, IntH2_L1 | no |
| C1_N1_t020_x | continuous_shell | x | x | 1 | 0.20 | 0 | 0.20 | 0.20 | none | planned | Bcenter, IntH2_L1 | no |
| C1_N1_t040_x | continuous_shell | x | x | 1 | 0.40 | 0 | 0.40 | 0.40 | none | planned | Bcenter, IntH2_L1 | no |
| C1_N1_t060_x | continuous_shell | x | x | 1 | 0.60 | 0 | 0.60 | 0.60 | none | planned | Bcenter, IntH2_L1 | no |
| C2_N2_t020_g010_x | continuous_shell | x | x | 2 | 0.20 | 0.10 | 0.40 | 0.50 | none | planned | Bcenter, IntH2_L1-L2 | no |
| C2_N3_t020_g010_x | continuous_shell | x | x | 3 | 0.20 | 0.10 | 0.60 | 0.80 | none | planned | Bcenter, IntH2_L1-L3 | no |
| C2_N4_t015_g008_x | continuous_shell | x | x | 4 | 0.15 | 0.08 | 0.60 | 0.84 | none | planned | Bcenter, IntH2_L1-L4 | no |
| C2_N6_t010_g008_x | continuous_shell | x | x | 6 | 0.10 | 0.08 | 0.60 | 1.00 | none | planned | Bcenter, IntH2_L1-L6 | no |
| M0_B0_z | no_shield | z | - | 0 | 0 | 0 | 0 | 0 | none | planned | B0 components and magnitude | no |
| S2_N3_t020_g010_seg12_aligned_x | segmented_shell_3d | x | x | 3 | 0.20 | 0.10 | 0.60 | 0.80 | aligned | planned | Bcenter, IntH2_total | no |
| S2_N3_t020_g010_seg12_staggered_x | segmented_shell_3d | x | x | 3 | 0.20 | 0.10 | 0.60 | 0.80 | staggered | planned | Bcenter, IntH2_total | no |

Only the allowed status labels `planned`, `built`, `solved`, `exported`, `processed`, and `used_in_paper` are used in the machine-readable status table. A case will be marked `used_in_paper` only after the exported quantities are complete and the post-processing checks have passed.

### I. Comparison Criteria for Multilayer Designs

Multilayer candidates are compared under three fairness conditions. First, in a fixed-total-radial-space comparison, \(T_{\mathrm{space}}\) is kept constant and \(a\) is adjusted according to

\[
a=\frac{T_{\mathrm{space}}-(N_L-1)g}{N_L}.
\]

This comparison answers whether dividing the same radial envelope into more layers improves shielding or changes \(\mathrm{IntH2}_{\mathrm{total}}\).

Second, in a fixed-ferrite-volume comparison, \(V_f\) is kept approximately constant. The total ferrite thickness \(T_f=N_La\) is only a thin-shell approximation for volume comparison when \(a\ll R_{\mathrm{in}}\). In the formal comparison, \(V_f\) is calculated from the exact layer-radius formula in Section II-C or directly from the CAD solid volume. This comparison tests whether redistributing the same amount of ferrite into multiple layers provides better shielding efficiency than a single thicker layer.

Third, in a fixed-target-shielding-factor comparison, different structures are compared at the same target \(\mathrm{SF}_q\). The required ferrite volume, total radial occupation, segmentation penalty, and \(\mathrm{IntH2}_{\mathrm{total},q}\) are then evaluated. This comparison is important because a design with a slightly higher \(\mathrm{SF}_q\) may be unattractive if it requires much more ferrite or produces a much larger magnetic-noise-related indicator.

In addition to \(\mathrm{SF}_q\), this work reports ferrite volume \(V_f\), \(\mathrm{LeakageRatio}_q\), \(\mathrm{IntH2}_{\mathrm{total},q}\), layer-resolved \(\mathrm{IntH2}_{L_i,q}\), and auxiliary material-efficiency metrics. If \(V_f\) is expressed in \(\mathrm{mm^3}\), the dimensional metric

\[
\eta_S=\frac{\ln(\mathrm{SF}_q)}{V_f}
\]

has units of \(\mathrm{mm^{-3}}\). A dimensionless normalized form is also reported:

\[
\eta_S^*=
\frac{V_{\mathrm{ref}}}{V_f}\ln(\mathrm{SF}_q),
\]

where \(V_{\mathrm{ref}}\) is the ferrite volume of a selected baseline, here the continuous single-layer shell with \(a=0.60\ \mathrm{mm}\). These metrics are introduced only as convenient indicators in this article. The logarithm is used because shielding factors multiply across ideal cascaded attenuation stages, while their logarithms add. Dividing \(\ln(\mathrm{SF}_q)\) by \(V_f\) therefore provides a compact way to compare attenuation per unit ferrite volume. It is not treated as a universally established material property.

Two additional magnetic-noise-related indicators are used to avoid equating lower material volume with lower noise:

\[
\rho_H=\frac{\mathrm{IntH2}_{\mathrm{total},q}}{V_f},
\]

and

\[
\chi_H=
\frac{\mathrm{IntH2}_{\mathrm{total},q}}{\ln(\mathrm{SF}_q)}.
\]

The first quantity describes the average virtual-coil field-energy integral per unit ferrite volume. The second describes the magnetic-noise-related integral required per logarithmic unit of shielding. Final design ranking is therefore based on \(\mathrm{SF}_q\), \(\mathrm{LeakageRatio}_q\), \(V_f\), \(\eta_S^*\), \(\mathrm{IntH2}_{\mathrm{total},q}\), \(\rho_H\), and \(\chi_H\), rather than on any single metric.

## III. Results

The numerical results in this section will be filled only after the corresponding AEDT exports and post-processing files are available. The present draft defines the required figures, tables, and interpretation logic without reporting unsupported numerical values.

### A. Verification of B0 Reference and Field-Direction Definition

This subsection will verify that the no-shield reference model produces the intended uniform field direction and magnitude at the observation point. The required table will list \(B_{0,x}\), \(B_{0,y}\), \(B_{0,z}\), and \(B_{0,\mathrm{Mag}}\) for each external-field direction. The text will confirm that the \(x\)-directed case is used for transverse shielding and that the \(z\)-directed case is used for axial shielding. No shielded-case comparison will be interpreted until this reference is exported.

### B. Continuous-Shell Screening Under Transverse External Field

This subsection will report the priority-1 continuous-shell transverse screening after the \(x\)-directed B0 reference and shielded exports are complete. Fig. 3 will show \(\mathrm{SF}_x\) versus ferrite volume \(V_f\). A companion table will list \(\mathrm{LeakageRatio}_x\), \(T_f\), \(T_{\mathrm{space}}\), and \(V_f\) for each priority-1 case. The interpretation will focus on whether increasing layer number improves shielding at comparable ferrite usage or radial occupation.

### C. Comparison at Fixed Ferrite Volume

This subsection will compare cases with approximately equal ferrite volume, especially the single-layer \(a=0.60\ \mathrm{mm}\), three-layer \(3\times0.20\ \mathrm{mm}\), and four-layer \(4\times0.15\ \mathrm{mm}\) candidates. Fig. 4 will show \(\mathrm{SF}_x\), \(\eta_S^*\), and \(\mathrm{LeakageRatio}_x\) for the fixed-volume group. The discussion will distinguish exact CAD or layer-radius volume from the thin-shell approximation \(T_f=N_La\).

### D. Layer-Resolved IntH2 Contribution

This subsection will use the virtual pickup-coil exports to analyze \(\mathrm{IntH2}_{L_i}\). Fig. 5 will show \(\mathrm{IntH2}_{\mathrm{total},x}\) versus \(V_f\), and Fig. 6 will show the layer-resolved fractions

\[
\frac{\mathrm{IntH2}_{L_i,x}}{\mathrm{IntH2}_{\mathrm{total},x}}.
\]

The validation table from `validate_layerwise_intH2.py` will be reported before interpreting the layer fractions. Cases with inconsistent \(\mathrm{IntH2}_{\mathrm{total}}\) and \(\sum_i\mathrm{IntH2}_{L_i}\) will be excluded from paper conclusions until re-exported.

### E. Axial-Field Extension for Selected Candidates

This subsection is planned for selected \(z\)-directed cases after the transverse screening identifies representative candidates. It will report \(\mathrm{SF}_z\) and \(\mathrm{LeakageRatio}_z\), not infer axial behavior from \(x\)-directed results. A planned figure will compare \(\mathrm{SF}_x\) and \(\mathrm{SF}_z\) for the same geometries to quantify the open-ended cylinder penalty.

### F. Segmented-Shell Correction: Aligned and Staggered Slots

This subsection is planned after continuous-shell screening. Fig. 7 will compare the continuous-shell result with segmented-shell results for aligned and staggered slots. The planned metrics are the segmentation penalty in shielding factor,

\[
\frac{\mathrm{SF}_{x,\mathrm{seg}}}{\mathrm{SF}_{x,\mathrm{cont}}},
\]

and the corresponding change in \(\mathrm{IntH2}_{\mathrm{total},x}\), \(\eta_S^*\), \(\rho_H\), and \(\chi_H\). The text will discuss whether staggered slots reduce a through-wall leakage path relative to aligned slots.

### G. Mesh and Boundary-Domain Convergence

This subsection will report convergence checks for the final candidate set. The planned convergence table will vary local mesh density in the ferrite thickness, gap, and slot regions, and will vary the air-domain size or open-boundary distance. A result will be considered usable only when \(B_{\mathrm{center},q}\), \(\mathrm{SF}_q\), and \(\mathrm{IntH2}_{\mathrm{total},q}\) change by less than the chosen tolerance.

### H. Permeability Sensitivity Analysis

This subsection is planned after the baseline matrix is processed. The planned sweep will use \(\mu_r'=500\), 1000, 2000, and 5000 for selected representative geometries. The figure will show how \(\mathrm{SF}_x\), \(\mathrm{LeakageRatio}_x\), and \(\mathrm{IntH2}_{\mathrm{total},x}\) change with \(\mu_r'\). The sensitivity analysis will not replace measured ferrite parameters; it will only test whether the structural ranking is robust to plausible permeability variation.

## IV. Expected Design Implications

Before the final AEDT exports are complete, the conclusions of this manuscript are written as expected design implications rather than verified numerical findings. The proposed framework is expected to clarify whether multilayer thin-ferrite cylindrical shells can provide useful shielding efficiency under manufacturable sheet-thickness constraints. It is also expected to separate three effects that are otherwise easy to confuse: increased shielding factor, reduced ferrite volume, and reduced magnetic-noise-related \(\mathrm{IntH2}\). After the priority-1 matrix, axial extension, segmented-shell correction, and validation checks are completed, this section will be replaced by result-supported conclusions.

## References

[1] J. C. Allred, R. N. Lyman, T. W. Kornack, and M. V. Romalis, "High-sensitivity atomic magnetometer unaffected by spin-exchange relaxation," *Phys. Rev. Lett.*, vol. 89, no. 13, Sep. 2002, Art. no. 130801.

[2] I. K. Kominis, T. W. Kornack, J. C. Allred, and M. V. Romalis, "A subfemtotesla multichannel atomic magnetometer," *Nature*, vol. 422, no. 6932, pp. 596-599, Apr. 2003.

[3] M. P. Ledbetter, I. M. Savukov, V. M. Acosta, D. Budker, and M. V. Romalis, "Spin-exchange-relaxation-free magnetometry with Cs vapor," *Phys. Rev. A*, vol. 77, no. 3, Mar. 2008, Art. no. 033408.

[4] S. Baillet, "Magnetoencephalography for brain electrophysiology and imaging," *Nature Neurosci.*, vol. 20, no. 3, pp. 327-339, Mar. 2017.

[5] T. E. Chupp, P. Fierlinger, M. J. Ramsey-Musolf, and J. T. Singh, "Electric dipole moments of atoms, molecules, nuclei, and particles," *Rev. Mod. Phys.*, vol. 91, no. 1, Jan. 2019, Art. no. 015001.

[6] T. J. Sumner, J. M. Pendlebury, and K. F. Smith, "Conventional magnetic shielding," *J. Phys. D: Appl. Phys.*, vol. 20, no. 9, pp. 1095-1101, Sep. 1987.

[7] V. Kelha, J. Pukki, R. Peltonen, A. Penttinen, R. Ilmoniemi, and J. Heino, "Design, construction, and performance of a large-volume magnetic shield," *IEEE Trans. Magn.*, vol. 18, no. 1, pp. 260-270, Jan. 1982.

[8] I. Altarev *et al.*, "A magnetically shielded room with ultra low residual field and gradient," *Rev. Sci. Instrum.*, vol. 85, no. 7, Jul. 2014, Art. no. 075106.

[9] S.-K. Lee and M. V. Romalis, "Calculation of magnetic field noise from high-permeability magnetic shields and conducting objects with simple geometry," *J. Appl. Phys.*, vol. 103, no. 8, Apr. 2008, Art. no. 084904.

[10] H. B. Dang, A. C. Maloof, and M. V. Romalis, "Ultrahigh sensitivity magnetic field and magnetization measurements with an atomic magnetometer," *Appl. Phys. Lett.*, vol. 97, no. 15, Oct. 2010, Art. no. 151110.

[11] D. Ma *et al.*, "A novel low-noise mu-metal magnetic shield with winding shape," *Sens. Actuators A, Phys.*, vol. 346, Oct. 2022, Art. no. 113884.

[12] T. W. Kornack, S. J. Smullin, S.-K. Lee, and M. V. Romalis, "A low-noise ferrite magnetic shield," *Appl. Phys. Lett.*, vol. 90, no. 22, May 2007, Art. no. 223501.

[13] D. Ma *et al.*, "Parameter modeling analysis of a cylindrical ferrite magnetic shield to reduce magnetic noise," *IEEE Trans. Ind. Electron.*, vol. 69, no. 1, pp. 991-998, Jan. 2022.

[14] J. Lu *et al.*, "Study of magnetic noise of a multi-annular ferrite shield," *IEEE Access*, vol. 8, pp. 40918-40924, 2020.

[15] B. Sun *et al.*, "Correlating the microstructure of Mn-Zn ferrite with magnetic noise for magnetic shield applications," *Ceram. Int.*, vol. 49, no. 8, pp. 11960-11967, Apr. 2023.

[16] B. Sun, D. Ma, X. Fang, Y. Xue, J. Lu, H. Chen, M. Zhang, H. Wei, B. Han, and Y. Zhai, "Suppression of magnetic noise and field in cubic low-noise ferrite magnetic shields," *IEEE Trans. Instrum. Meas.*, vol. 73, pp. 1-10, 2024, Art. no. 1501810, doi: 10.1109/TIM.2024.3385809.

[17] J. Lu *et al.*, "Effect of gaps on magnetic noise of cylindrical ferrite shield," *J. Phys. D: Appl. Phys.*, vol. 54, no. 25, Jun. 2021, Art. no. 255002.

[18] R. Kubo, "The fluctuation-dissipation theorem," *Rep. Prog. Phys.*, vol. 29, no. 1, pp. 255-284, Jan. 1966.

[19] C. Liu *et al.*, "Investigation on the effects of micro-vibration on the atomic comagnetometer," *IEEE Trans. Instrum. Meas.*, vol. 72, 2023, Art. no. 9511711.

[20] P. Dutta and P. M. Horn, "Low-frequency fluctuations in solids: 1/f noise," *Rev. Mod. Phys.*, vol. 53, no. 3, pp. 497-516, Jul. 1981.

[21] K. Yang *et al.*, "Improved measurement of the low-frequency complex permeability of ferrite annulus for low-noise magnetic shielding," *IEEE Access*, vol. 7, pp. 126059-126065, 2019.

[22] K. Yang *et al.*, "Minimizing magnetic fields of the low-noise MnZn ferrite magnetic shield for atomic magnetometer," *J. Phys. D: Appl. Phys.*, vol. 55, no. 1, Jan. 2022, Art. no. 015003.

[23] Z. Xu, Z. Zhang, B. Wu, H. Wang, X. Kong, and M. Wang, "A study of enclosed magnetic shielding room by simulation," *IEEE Trans. Appl. Supercond.*, vol. 31, no. 8, pp. 1-5, Nov. 2021.

[24] X. Xu, L. Wang, W. Liu, and Z. Zhao, "Theoretical modeling and characterization of equivalent magnetic properties in laminated composite magnetic shielding," *Measurement*, vol. 251, 2025, Art. no. 117237.

[25] IEC 62044-2, *Cores Made of Soft Magnetic Materials - Measuring Methods - Part 2: Magnetic Properties at Low Excitation Level*, 2005.

[26] TDK Corporation, "Mn-Zn ferrite material characteristics: PC95 and related Mn-Zn ferrite grades," product catalog, accessed May 26, 2026. [Online]. Available: https://product.tdk.com/system/files/dam/doc/product/ferrite/ferrite/ferrite-core/catalog/ferrite_mn-zn_material_characteristics_en.pdf

[27] A. Mager, "Magnetic shields," *IEEE Trans. Magn.*, vol. 6, no. 1, pp. 67-75, Mar. 1970.

[28] K. Nagashima, I. Sasada, and K. Tashiro, "High-performance bench-top cylindrical magnetic shield with magnetic shaking enhancement," *IEEE Trans. Magn.*, vol. 38, no. 5, pp. 3335-3337, Sep. 2002.

[29] J. M. G. D. K. O'Connell, J. M. Brown, and T. W. Kornack, "Technique for high axial shielding factor performance of large-scale, thin, open-ended, cylindrical Metglas magnetic shields," arXiv:1107.2625, 2011.
