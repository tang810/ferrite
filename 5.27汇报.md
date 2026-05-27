# Finite-Element Evaluation Framework for Multilayer Thin-Ferrite Cylindrical Shields in Low-Noise Magnetic Measurement Systems

## Abstract

Passive ferrite shields are critical for suppressing static and low-frequency magnetic disturbances in ultra-sensitive measurement instruments, including atomic magnetometers, SERF comagnetometers, and magnetoencephalography systems. When monolithic ferrite cylinders are impractical due to sintering and machining constraints, multilayer thin-shell assembly offers a manufacturable alternative, but the design trade space among layer count, ferrite thickness, radial gaps, shielding factor, and magnetic-noise-related loss integrals must be evaluated under a consistent measurement-oriented boundary condition. This paper presents a finite-element evaluation framework that treats the shield as a device under test in a calibrated uniform-field measurement configuration. A directional shielding factor is defined from a validated no-shield reference field and the shielded center leakage field. A virtual pickup-coil model provides the geometry-dependent loss indicator \(\int H^2 dV\) (IntH2), which enters shield-induced noise calculations through the fluctuation-dissipation theorem but is not itself a measured noise spectrum. The framework is applied to seven transverse continuous-shell candidates with 1--4 ferrite layers of thickness 0.08--0.60 mm under fixed x-directed tangential-H excitation. At fixed ferrite volume (\(V_f\approx 75600\ \mathrm{mm^3}\)), the four-layer design achieves SFx = 3.629, a 27.6% improvement over the best single-layer design (SFx = 2.845), while also giving the lowest IntH2_total among the equal-volume candidates. Mesh convergence for two representative cases and a validated z-directed no-shield reference are further provided to strengthen numerical credibility. Axial shielded cases, segmented-shell correction, boundary-domain convergence, permeability sensitivity, field-map exports, and prototype SF measurement remain explicitly marked as pending validation items rather than reported results. The framework establishes a reproducible methodology for evaluating manufacturable multilayer ferrite shields and provides a measurement-oriented baseline for systematic shield assessment.
## I. Introduction

Ultra-sensitive magnetic measurement systems are limited not only by intrinsic sensor noise, but also by the magnetic environment created by the shield surrounding the sensor. In atomic magnetometers, spin-exchange-relaxation-free (SERF) comagnetometers, magnetoencephalography instruments, and precision symmetry tests, the shield determines the leakage field reaching the sensing volume and can also introduce magnetic-field noise through material loss [1]-[5]. The shield should therefore be treated as part of the measurement chain rather than merely as a passive enclosure. For low-noise magnetic instrumentation, shielding factor, leakage-field directionality, ferrite volume, radial occupation, and material-loss-related noise indicators must be evaluated together.

High-permeability metallic shields remain widely used for attenuation of static and low-frequency environmental fields [6]-[8]. However, metallic shields also introduce Johnson-noise-like magnetic fluctuations through eddy-current loss, and this contribution can become relevant in the frequency band of high-sensitivity magnetometers [9]-[11]. Ferrites provide an attractive alternative because their electrical conductivity is much lower than that of metallic alloys, thereby suppressing eddy-current magnetic noise. The remaining low-frequency shield-induced noise is associated mainly with magnetic loss, represented by the imaginary permeability \(\mu_r''\), and with the spatial distribution of the magnetic field inside the ferrite [9], [12]-[15]. Recent ferrite shield studies, including a cubic ferrite shield reported in IEEE Transactions on Instrumentation and Measurement [16], demonstrate the relevance of ferrites to low-noise instrumentation. Nevertheless, cubic panel shields do not directly address the open-ended cylindrical geometry commonly used around atomic sensors and compact comagnetometers.

A monolithic cylindrical ferrite shield is difficult to manufacture when the wall is thin and the diameter is large. Ferrites are brittle after sintering, and machining a thin-walled cylinder with an inner diameter of approximately 200 mm and a wall thickness in the 0.08--0.60 mm range is mechanically risky. Commercial ferrite sheets, strips, annuli, and blocks are more naturally assembled into multilayer cylindrical shells. This creates a measurement-oriented design problem: the layer count \(N_L\), layer thickness \(a\), radial gap \(g\), total ferrite volume \(V_f\), and total radial occupation must be selected while simultaneously controlling the leakage field and the geometry-dependent loss integral that enters shield-induced noise calculations.

**Table I. Comparison with Prior Ferrite Shield Studies**

| Work | Geometry | Evaluation Quantity | Method | Noise-related Metric | Scope or Unreported Element |
|---|---|---|---|---|---|
| Kornack et al. 2007 [12] | Single ferrite cylinder | SF, \(\delta B(f)\) | Exp. + analytic | Measured \(\delta B(f)\) | Single geometry; multilayer design not addressed |
| Lee and Romalis 2008 [9] | Simple shapes (sphere, inf. cyl., plate) | \(\delta B(f)\) formula | Analytic | Derived \(\delta B(f) \propto \sqrt{\int H^2 dV}\) | No finite-length multilayer ferrite cylinder |
| Ma et al. 2022 [13] | Cylindrical ferrite + mu-metal | SF, noise via IntH2 | FEM | IntH2 for single ferrite body | Validated no-shield directional reference and layer-resolved IntH2 not explicitly reported |
| Sun et al. 2024 [16] | Cubic ferrite shield | SF, \(\delta B(f)\) | FEM + Exp. | Measured \(\delta B(f)\) | Cubic geometry; cylindrical multilayer shell not addressed |
| Fang et al. 2021 [30] | Magnetic shield measurement setup | SF | Experimental | None | Noise-related ferrite loss metric not included |
| This work | Multilayer thin-ferrite cylindrical shell | Directional SF, \(V_f\), layer-resolved IntH2 | FEM + data consistency checks | Geometry-dependent loss indicator | Transverse continuous-shell results are preliminary; axial, segmented, convergence, and experimental validation remain separate checks |

Previous work provides important models and measurements for ferrite shields, but the quantities required for a low-noise cylindrical measurement instrument are not always reported in a unified way. As summarized in Table I, previous studies have not simultaneously reported a validated no-shield directional reference, layer-resolved IntH2 analysis, and a multilayer thin-ferrite cylindrical geometry under a unified evaluation framework. The resulting gap is not simply the absence of a multilayer ferrite design; rather, it is the absence of a reproducible measurement-oriented workflow that connects a calibrated directional reference field, shielded center leakage field, ferrite volume, and material-loss-related geometry indicator.

This paper addresses that gap by developing a finite-element evaluation framework for multilayer thin-ferrite cylindrical shells. The novelty is the combined measurement-oriented procedure, consisting of: 1) a validated no-shield directional reference for shielding-factor evaluation; 2) a virtual pickup-coil loss-integral model for geometry-dependent noise assessment; 3) layer-resolved IntH2 decomposition for multilayer shields; 4) fixed-volume comparison between single-layer and multilayer candidates; and 5) unit-consistent auxiliary metrics for low-noise shield design.

The contributions are as follows.

1. A directional no-shield reference model is established for shielding-factor evaluation. For the transverse case, the exported reference field is checked against the expected vacuum value \(B_0=\mu_0H_0\) and against the transverse numerical residuals, ensuring that SFx is computed from the intended field component rather than from the vector magnitude.

2. A measurement-oriented FEM workflow separates the external uniform-field model from the virtual pickup-coil model. The former evaluates \(B_0\), \(B_{\mathrm{center}}\), SFq, and LeakageRatioq; the latter evaluates IntH2_total and layer-resolved \(\mathrm{IntH2}_{L_i}\).

3. A continuous-shell transverse screening matrix is processed for manufacturable thin-ferrite cylindrical candidates. The reported transverse results are limited to the tested continuous-shell conditions and screening material parameters, and are not presented as a completed instrument design.

4. A reproducible data-processing and consistency-check procedure is established, including directional-reference validation, SF calculation, layerwise IntH2 summation verification, and unit-consistent auxiliary metrics. An uncertainty-aware experimental protocol is further provided to guide future validation.

The remainder of this paper is organized as follows. Section II defines the evaluation methodology, including the coordinate system, directional shielding factor, no-shield reference validation, virtual pickup-coil loss integral, geometry, FEM settings, comparison metrics, convergence checks, and future experimental validation protocol. Section III presents the currently available transverse continuous-shell results and identifies which validations remain pending. Section IV discusses what the present data can and cannot prove for low-noise instrumentation. Section V summarizes expected design implications and limitations.

## II. Evaluation Methodology

### A. Measurement Configuration and Coordinate Definition

The shield is treated as a device under test (DUT) in a calibrated magnetic measurement configuration. The cylinder axis is defined as the Cartesian \(z\)-direction, while \(x\) and \(y\) span the transverse plane. Because the DUT is a finite open-ended cylinder, transverse and axial shielding are not equivalent: SFx and SFy describe transverse shielding through the cylindrical sidewall, whereas SFz describes axial shielding affected by the open ends [6], [27]-[29]. The present processed dataset focuses on the \(x\)-directed transverse configuration; the same definitions apply to selected \(z\)-directed cases when axial data are available.

Two finite-element models are used and must not be physically conflated. The external uniform-field model evaluates environmental-field attenuation and provides \(B_0\), \(B_{\mathrm{center}}\), SFq, and LeakageRatioq. The virtual pickup-coil model evaluates the coupling of material loss to the measured magnetic field through the fluctuation-dissipation theorem and provides IntH2_total and \(\mathrm{IntH2}_{L_i}\). Both models use the same cylindrical shell geometry, layer definitions, and observation point at \((0,0,0)\), but they represent different measurement questions.

[Fig. 1. Measurement-oriented evaluation framework: (a) external uniform-field model with tangential-H boundary excitation, shield at center, and observation point at \((0,0,0)\); (b) virtual pickup-coil model at the same observation point; (c) exported quantities and post-processed metrics, including SFx/SFz, LeakageRatioq, \(V_f\), IntH2_total, \(\mathrm{IntH2}_{L_i}\), \(\eta_S\), \(\eta_S^*\), \(\rho_H\), and \(\chi_H\).]

### B. Directional Shielding Factor and Leakage Ratio

For an applied external field along direction \(q\in\{x,y,z\}\), the no-shield reference field at the observation point is

\[
\mathbf{B}_0=(B_{0,x},B_{0,y},B_{0,z}),
\]

and the shielded center leakage field is

\[
\mathbf{B}_{\mathrm{center}}=(B_{\mathrm{center},x},B_{\mathrm{center},y},B_{\mathrm{center},z}).
\]

The directional shielding factor is

\[
\mathrm{SF}_q=\frac{|B_{0,q}|}{|B_{\mathrm{center},q}|},
\]

and the corresponding leakage ratio is

\[
\mathrm{LeakageRatio}_q=\frac{|B_{\mathrm{center},q}|}{|B_{0,q}|}=\frac{1}{\mathrm{SF}_q}.
\]

The formal SF calculation uses the directional component, not \(|\mathbf{B}|\). Thus, SFx is computed from \(B_{0,x}\) and \(B_{\mathrm{center},x}\), while SFz is computed from \(B_{0,z}\) and \(B_{\mathrm{center},z}\). The magnitude \(B_{\mathrm{Mag}}\) is retained only as an auxiliary consistency check.

### C. No-Shield Directional Reference

The no-shield reference is the calibration standard for the external-field model. In this model, the ferrite bodies are deleted or assigned vacuum while the air region, boundary scale, observation point, and excitation amplitude are kept identical to the shielded model. The external field is applied using tangential-H boundary conditions on the outer air-region surfaces. For the transverse \(x\)-directed reference, an \(x\)-directed tangential H field with \(H_0=1\ \mathrm{A/m}\) is applied to the appropriate air-region faces, and the faces normal to \(x\) are assigned zero tangential H field. The same procedure is used for the \(z\)-directed reference with the tangential H vector aligned to \(z\).

The theoretical check for the no-shield model follows directly from vacuum magnetostatics:

\[
B_0=\mu_0 H_0=(4\pi\times10^{-7})(1)=1.256637\times10^{-6}\ \mathrm{T}.
\]

Therefore, for an ideal \(x\)-directed reference, \(B_{0,x}\) should be approximately \(1.256637\times10^{-6}\ \mathrm{T}\), while \(B_{0,y}\) and \(B_{0,z}\) should be much smaller. The exported transverse reference used in the present dataset, \(B_{0,x}=1.2566\times10^{-6}\ \mathrm{T}\), is consistent with this expectation. The residual \(y\)- and \(z\)-components are treated as numerical residuals caused by finite-element discretization, finite-domain boundary approximation, and interpolation at the observation point.

The directional reference is accepted only if the primary component dominates the transverse components. For example, the \(x\)-directed reference must satisfy

\[
\frac{|B_{0,x}|}{\max(|B_{0,y}|,|B_{0,z}|)}\ge 10.
\]

A much larger ratio is preferred. Cases whose reference direction fails this check are marked failed_validation and are not used for paper figures or conclusions.

### D. Virtual Pickup-Coil Model and IntH2

The virtual pickup-coil model follows the fluctuation-dissipation formalism of Lee and Romalis [9]. A virtual coil at the observation point generates a magnetic field \(H_{\mathrm{vc}}\) in the ferrite. For a coil area \(A\), turn number \(N_c\), peak current \(I_0\), and magnetic moment \(m=AN_cI_0\), the hysteresis-loss contribution to magnetic-field noise can be written as

\[
\delta B_{\mathrm{hyst}}(f)=\frac{1}{m}\left(\frac{2k_{\mathrm{B}}T\mu''}{\pi f}\int_V H_{\mathrm{vc}}^2\,dV\right)^{1/2},
\]

where \(\mu''=\mu_0\mu_r''\) is the absolute imaginary permeability if \(\mu_r''\) is specified as a relative quantity. The current \(I_0\) is the peak current used in the virtual-coil excitation; if an RMS current convention is used in another implementation, the normalization must be converted consistently.

This paper does not report measured magnetic-noise spectra because \(\mu_r''(f)\) for the specific ferrite material has not been measured in the present dataset. The exported quantity is therefore the geometry-dependent magnetic-noise-related loss indicator

\[
\mathrm{IntH2}=\int_V H_{\mathrm{vc}}^2\,dV,
\]

with SI unit \(\mathrm{A^2\,m}\). IntH2 is not a measured magnetic noise value. It becomes an absolute noise prediction only after measured \(\mu_r''(f)\), temperature, frequency, and virtual-coil normalization are specified. The relative ranking by IntH2 is meaningful only under identical material properties, identical virtual-coil normalization, and identical observation direction.

For a multilayer shell, each ferrite layer is integrated separately:

\[
\mathrm{IntH2}_{L_i}=\int_{V_{L_i}}H_{\mathrm{vc}}^2\,dV,
\]

and

\[
\mathrm{IntH2}_{\mathrm{total}}=\sum_{i=1}^{N_L}\mathrm{IntH2}_{L_i}.
\]

The post-processing pipeline checks

\[
\frac{|\mathrm{IntH2}_{\mathrm{total}}-\sum_i\mathrm{IntH2}_{L_i}|}{|\mathrm{IntH2}_{\mathrm{total}}|}<10^{-3}.
\]

Cases that fail this layerwise summation check are excluded from figure generation until the AEDT field-calculator expressions are corrected and re-exported. The standard expression names are IntH2_total and IntH2_L1 through IntH2_L4 for the current main matrix.

### E. Multilayer Cylindrical Shell Geometry

The DUT is an open-ended multilayer cylindrical shell with inner radius \(R_{\mathrm{in}}\), axial length \(L\), layer count \(N_L\), ferrite thickness \(a\), and radial interlayer gap \(g\). In the current main matrix,

\[
R_{\mathrm{in}}=100\ \mathrm{mm},\qquad L=200\ \mathrm{mm}.
\]

The total ferrite thickness is

\[
T_f=N_La,
\]

and the total radial occupation is

\[
T_{\mathrm{space}}=N_La+(N_L-1)g.
\]

For layer \(i\), where \(i=1\) is the innermost layer,

\[
R_{i,\mathrm{in}}=R_{\mathrm{in}}+(i-1)(a+g),
\]

\[
R_{i,\mathrm{out}}=R_{i,\mathrm{in}}+a.
\]

The ferrite volume is computed from the exact cylindrical-shell formula,

\[
V_f=\pi L\sum_{i=1}^{N_L}\left(R_{i,\mathrm{out}}^2-R_{i,\mathrm{in}}^2\right),
\]

rather than from a thin-shell approximation. Although \(V_f\) is displayed in \(\mathrm{mm^3}\) for engineering readability, all SI-derived metrics are computed after unit conversion.

For segmented-shell studies, the circumferential coverage fraction is defined as

\[
\eta_\phi=1-\frac{N_{\mathrm{seg}}g_\phi}{2\pi R_{\mathrm{mid}}},
\]

where \(N_{\mathrm{seg}}\) is the number of circumferential segments, \(g_\phi\) is the gap width between adjacent segments, and \(R_{\mathrm{mid}}\) is the mid-radius of the layer. Segmented aligned and staggered cases are treated as separate validation cases and are not substituted for continuous-shell results.

### F. Finite-Element Simulation Settings and Data Export

The FEM model is solved in Ansys Maxwell using the magnetostatic solver. The screening material parameters used for the present processed dataset are \(\mu_r'=1000\) and \(\sigma=0.01\ \mathrm{S/m}\). These values are screening parameters, not measured material constants for a final prototype. A permeability-sensitivity study is required before the ranking is treated as material robust.

The external uniform-field model exports \(B_{\mathrm{center},x}\), \(B_{\mathrm{center},y}\), \(B_{\mathrm{center},z}\), and \(B_{\mathrm{center,Mag}}\) for shielded cases. The no-shield reference exports \(B_{0,x}\), \(B_{0,y}\), \(B_{0,z}\), and \(B_{0,\mathrm{Mag}}\). The virtual pickup-coil model exports IntH2_total and the layerwise quantities \(\mathrm{IntH2}_{L_i}\). The raw CSV files are combined by case_id and field direction. The scripts then compute SFq, LeakageRatioq, \(V_f\), \(\eta_S\), \(\eta_S^*\), \(\rho_H\), and \(\chi_H\). Missing, planned, or failed_validation rows remain excluded from paper-ready figures.

The main processed transverse cases are listed in Table II. Axial, segmented, mesh-convergence, and permeability-sensitivity cases are separate validation stages and should not be merged into the main transverse interpretation unless their raw exports and validation files are available.

**Table II. Main Continuous-Shell Transverse Simulation Matrix**

| Case | \(N_L\) | \(a\) (mm) | \(g\) (mm) | Field direction | Coil direction | Status |
|---|---:|---:|---:|---|---|---|
| B0_reference_x | 0 | 0 | 0 | x | -- | exported, validation passed |
| C1_N1_t008_x | 1 | 0.08 | 0 | x | x | processed |
| C1_N1_t020_x | 1 | 0.20 | 0 | x | x | processed |
| C1_N1_t040_x | 1 | 0.40 | 0 | x | x | processed |
| C1_N1_t060_x | 1 | 0.60 | 0 | x | x | processed |
| C2_N2_t020_g010_x | 2 | 0.20 | 0.10 | x | x | processed |
| C2_N3_t020_g010_x | 3 | 0.20 | 0.10 | x | x | processed |
| C2_N4_t015_g008_x | 4 | 0.15 | 0.08 | x | x | processed |

### G. Comparison Metrics

The volume-normalized shielding index is defined as

\[
\eta_S=\frac{\ln(\mathrm{SF}_x)}{V_f},
\]

with unit \(\mathrm{m^{-3}}\) when \(V_f\) is expressed in \(\mathrm{m^3}\). This is an auxiliary comparison index introduced in this paper, not a universal material property. The logarithm is used because ideal shielding factors multiply for cascaded attenuation stages, while their logarithms add.

To remove the arbitrary scale of \(\eta_S\), a dimensionless normalized index is also used:

\[
\eta_S^*=\frac{\ln(\mathrm{SF}_x)/V_f}{\ln(\mathrm{SF}_{x,\mathrm{ref}})/V_{\mathrm{ref}}},
\]

where the reference is the continuous single-layer shell with \(a=0.60\ \mathrm{mm}\). Two additional loss-related auxiliary metrics are

\[
\rho_H=\frac{\mathrm{IntH2}_{\mathrm{total}}}{V_f[\mathrm{m^3}]},
\]

and

\[
\chi_H=\frac{\mathrm{IntH2}_{\mathrm{total}}}{\ln(\mathrm{SF}_x)}.
\]

Here, \(\rho_H\) identifies loss-integral density per ferrite volume, while \(\chi_H\) compares the geometry-dependent loss integral to logarithmic attenuation. These metrics are intended for side-by-side evaluation of SFx, \(V_f\), IntH2_total, and radial occupation. They do not by themselves determine a shield design.

### H. Mesh and Boundary-Domain Convergence

Mesh and boundary-domain convergence are required before the numerical ranking can be treated as final. The convergence check uses coarse, medium, and fine mesh settings for representative thin and multilayer cases, and air-domain scales such as 2R, 3R, and 5R for representative shield geometries. The acceptance target is

\[
\frac{|\mathrm{SF}_{x,\mathrm{fine}}-\mathrm{SF}_{x,\mathrm{medium}}|}{\mathrm{SF}_{x,\mathrm{fine}}}<0.05,
\]

and

\[
\frac{|\mathrm{IntH2}_{\mathrm{fine}}-\mathrm{IntH2}_{\mathrm{medium}}|}{\mathrm{IntH2}_{\mathrm{fine}}}<0.05.
\]

For boundary-domain convergence, the target is a less than 5% change in SFx between the 3R and 5R air-region scales. Until formal mesh and boundary-domain convergence is completed, the reported ranking should be regarded as indicative.

### I. Future Experimental Validation Protocol

The present manuscript defines a validation protocol but does not claim completed experimental validation. A Helmholtz coil or calibrated uniform-field source can provide an applied field \(B_{\mathrm{app}}\), and a calibrated magnetometer placed at the shield center can measure \(B_{\mathrm{center}}\). The experimental directional shielding factor would be

\[
\mathrm{SF}_{q,\mathrm{exp}}=\frac{|B_{\mathrm{app},q}|}{|B_{\mathrm{center},q}|}.
\]

The relative uncertainty can be propagated as

\[
\left(\frac{u(\mathrm{SF}_{q,\mathrm{exp}})}{\mathrm{SF}_{q,\mathrm{exp}}}\right)^2=
\left(\frac{u(B_{\mathrm{app},q})}{B_{\mathrm{app},q}}\right)^2+
\left(\frac{u(B_{\mathrm{center},q})}{B_{\mathrm{center},q}}\right)^2.
\]

Important uncertainty sources include coil-current calibration, coil-constant uncertainty, magnetometer calibration, sensor positioning, field-gradient error at the center, ambient drift, and remanent field after handling. Absolute magnetic-noise validation requires measured \(\mu_r''(f)\) or direct noise spectra under the same geometry and sensor configuration. Such measurements are outside the present processed dataset and should be reported separately when available.
## III. Results

### A. No-Shield Reference Validation

The no-shield reference model for the \(x\)-directed configuration was evaluated with all ferrite assigned as vacuum, under the tangential-H boundary excitation described in Section II-C. The exported center-point fields are

\[
B_{0,x} = 1.2566 \times 10^{-6}\ \mathrm{T}, \quad
B_{0,y} = -3.83 \times 10^{-15}\ \mathrm{T},
\]
\[
B_{0,z} = -1.94 \times 10^{-13}\ \mathrm{T}, \quad
B_{0,\mathrm{Mag}} = 1.2566 \times 10^{-6}\ \mathrm{T}.
\]

The field-direction purity ratio is

\[
\frac{|B_{0,x}|}{\max(|B_{0,y}|, |B_{0,z}|)} = 6.47 \times 10^6,
\]

confirming that the reference field is an effectively pure \(x\)-directed uniform field. This \(B_{0,x}\) value is used as the denominator in all SFx calculations that follow. A separate \(z\)-directed no-shield reference has also been exported for axial-shielding studies:

\[
B_{0,z}=1.2566\times10^{-6}\ \mathrm{T},\quad
B_{0,x}=-2.47\times10^{-15}\ \mathrm{T},\quad
B_{0,y}=-3.36\times10^{-14}\ \mathrm{T}.
\]

The corresponding axial direction-purity ratio is \(3.74\times10^7\). This validates the denominator for SFz, but the shielded \(z\)-directed cases have not yet been exported and therefore are not used for axial conclusions.

### B. Transverse Continuous-Shell Screening

All seven continuous-shell cases were evaluated under the same tangential-H boundary condition and magnetostatic settings as the no-shield reference. Table III reports the complete transverse screening results.

**Table III. Transverse Continuous-Shell Shielding Results**

| Case | \(N_L\) | \(a\) (mm) | \(g\) (mm) | \(V_f\) (mm³) | \(B_{\mathrm{center},x}\) (T) | SFx | LeakageRatiox | \(\eta_S\) (mm⁻³) | \(\eta_S^*\) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C1_N1_t008_x | 1 | 0.08 | 0 | 10057 | \(9.375\times10^{-7}\) | 1.340 | 0.746 | \(2.91\times10^{-5}\) | 2.203 |
| C1_N1_t020_x | 1 | 0.20 | 0 | 25158 | \(8.353\times10^{-7}\) | 1.504 | 0.665 | \(1.62\times10^{-5}\) | 1.228 |
| C1_N1_t040_x | 1 | 0.40 | 0 | 50366 | \(5.832\times10^{-7}\) | 2.155 | 0.464 | \(1.52\times10^{-5}\) | 1.153 |
| C1_N1_t060_x | 1 | 0.60 | 0 | 75624 | \(4.418\times10^{-7}\) | 2.845 | 0.352 | \(1.38\times10^{-5}\) | 1.045 |
| C2_N2_t020_g010_x | 2 | 0.20 | 0.10 | 50391 | \(5.616\times10^{-7}\) | 2.238 | 0.447 | \(1.60\times10^{-5}\) | 1.209 |
| C2_N3_t020_g010_x | 3 | 0.20 | 0.10 | 75700 | \(4.197\times10^{-7}\) | 2.994 | 0.334 | \(1.45\times10^{-5}\) | 1.095 |
| C2_N4_t015_g008_x | 4 | 0.15 | 0.08 | 75715 | \(3.463\times10^{-7}\) | 3.629 | 0.276 | \(1.70\times10^{-5}\) | 1.287 |

All seven cases satisfy SFx > 1, confirming that each geometry provides net attenuation of the external transverse field. The B0 direction validation passes for all shielded-case exports as well (the shielded center field remains x-dominated in all cases). All layerwise IntH2 consistency checks pass with relative errors at or below \(10^{-12}\).

[Fig. 3. SFx versus ferrite volume \(V_f\) for all seven cases: highlight the equal-volume group (\(V_f \approx 75600\ \mathrm{mm^3}\)) containing C1_N1_t060_x, C2_N3_t020_g010_x, and C2_N4_t015_g008_x. Single-layer trend SFx(\(a\)) is monotonic with diminishing returns.]

**Single-layer thickness dependence.** For the \(N_L = 1\) series, SFx increases monotonically with \(a\) from 1.340 (\(a = 0.08\ \mathrm{mm}\)) to 2.845 (\(a = 0.60\ \mathrm{mm}\)). This is the expected behavior: thicker ferrite provides a larger cross-sectional area for flux shunting, reducing the center leakage field. The leakage ratio decreases correspondingly from 0.746 to 0.352. However, \(\eta_S\) decreases with increasing thickness, from \(2.91\times10^{-5}\) to \(1.38\times10^{-5}\ \mathrm{mm^{-3}}\), indicating that the incremental shielding per unit ferrite volume diminishes as the shell thickens. This diminishing-return behavior is consistent with the logarithmic nature of shielding in cylindrical geometries [6]: the innermost portion of a thick shell is partially shielded by the outer portion and therefore contributes less incremental attenuation. Correspondingly, \(\eta_S^*\) decreases from 2.203 to 1.045, showing that the thinnest single-layer case uses its ferrite volume most efficiently—though it provides the weakest absolute shielding.

**Multilayer comparison.** At near-equal ferrite volume (\(V_f \approx 75600\ \mathrm{mm^3}\)), the four-layer case C2_N4_t015_g008_x achieves SFx = 3.629—a 27.6% improvement over the best single-layer case C1_N1_t060_x (SFx = 2.845) and a 21.2% improvement over the three-layer case C2_N3_t020_g010_x (SFx = 2.994). The three-layer case provides a 5.2% gain over the single-layer baseline, while the four-layer case delivers a substantially larger improvement with an additional radial occupation of 0.24 mm. The two-layer case C2_N2_t020_g010_x achieves SFx = 2.238 at \(V_f = 50391\ \mathrm{mm^3}\) and \(T_f = 0.40\ \mathrm{mm}\)—comparable to the single-layer \(a = 0.40\ \mathrm{mm}\) case (SFx = 2.155, \(V_f = 50366\ \mathrm{mm^3}\)), with a 3.9% improvement from splitting one 0.40 mm layer into two 0.20 mm layers with a 0.10 mm gap.

### C. Fixed-Volume Comparison

Table IV isolates the three cases that form the equal-volume comparison group (\(V_f \approx 75600\ \mathrm{mm^3}\)).

**Table IV. Fixed-Volume Comparison**

| Case | \(N_L\) | \(T_f\) (mm) | \(T_{\mathrm{space}}\) (mm) | \(V_f\) (mm³) | SFx | \(\eta_S\) (mm⁻³) | \(\eta_S^*\) | \(\rho_H\) (A²/m²) | \(\chi_H\) (A²·m) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C1_N1_t060_x | 1 | 0.60 | 0.60 | 75624 | 2.845 | \(1.38\times10^{-5}\) | 1.045 | \(6.15\times10^{-2}\) | \(4.45\times10^{-6}\) |
| C2_N3_t020_g010_x | 3 | 0.60 | 0.80 | 75700 | 2.994 | \(1.45\times10^{-5}\) | 1.095 | \(5.79\times10^{-2}\) | \(4.00\times10^{-6}\) |
| C2_N4_t015_g008_x | 4 | 0.60 | 0.84 | 75715 | 3.629 | \(1.70\times10^{-5}\) | 1.287 | \(5.49\times10^{-2}\) | \(3.23\times10^{-6}\) |

[Fig. 4. Fixed-volume comparison (\(V_f \approx 75600\ \mathrm{mm^3}\)): bar charts for SFx, IntH2_total, \(\chi_H\), and \(\eta_S^*\) across the three candidates C1_N1_t060_x, C2_N3_t020_g010_x, and C2_N4_t015_g008_x.]

Among the processed transverse continuous-shell cases, the four-layer candidate has the highest SFx, the highest \(\eta_S^*\), and the lowest \(\rho_H\) and \(\chi_H\). This result should be interpreted as an indicative ranking for the tested boundary condition and screening material parameters. The improvement is attributed to flux redistribution among multiple high-permeability layers and interlayer gaps. This interpretation should be supported by magnetic-flux-density contour plots and flux-line visualizations before it is used as a general design rule.

### D. Layer-Resolved Loss Indicator

Table V reports the layer-resolved IntH2 values for all seven cases.

**Table V. Layer-Resolved Loss Indicator IntH2**

| Case | \(N_L\) | IntH2_total (A²·m) | IntH2_L1 | IntH2_L2 | IntH2_L3 | IntH2_L4 | Layerwise check |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| C1_N1_t008_x | 1 | \(3.819\times10^{-6}\) | \(3.819\times10^{-6}\) | — | — | — | passed |
| C1_N1_t020_x | 1 | \(4.383\times10^{-6}\) | \(4.383\times10^{-6}\) | — | — | — | passed |
| C1_N1_t040_x | 1 | \(4.973\times10^{-6}\) | \(4.973\times10^{-6}\) | — | — | — | passed |
| C1_N1_t060_x | 1 | \(4.649\times10^{-6}\) | \(4.649\times10^{-6}\) | — | — | — | passed |
| C2_N2_t020_g010_x | 2 | \(4.917\times10^{-6}\) | \(2.428\times10^{-6}\) | \(2.490\times10^{-6}\) | — | — | passed |
| C2_N3_t020_g010_x | 3 | \(4.381\times10^{-6}\) | \(1.125\times10^{-6}\) | \(1.582\times10^{-6}\) | \(1.674\times10^{-6}\) | — | passed |
| C2_N4_t015_g008_x | 4 | \(4.160\times10^{-6}\) | \(8.127\times10^{-7}\) | \(8.253\times10^{-7}\) | \(8.572\times10^{-7}\) | \(1.665\times10^{-6}\) | passed |

For the single-layer series, IntH2_total exhibits non-monotonic behavior: it increases from \(3.82\times10^{-6}\) to \(4.97\times10^{-6}\ \mathrm{A^2\cdot m}\) as \(a\) increases from 0.08 to 0.40 mm, then decreases to \(4.65\times10^{-6}\) at \(a = 0.60\ \mathrm{mm}\). This non-monotonicity arises from the competition between two effects. Increasing \(a\) expands the integration volume \(V_f\) (tending to increase IntH2), but also strengthens the flux shunting, reducing the internal H-field magnitude throughout the ferrite (tending to decrease IntH2). At small thicknesses, the volume effect dominates; beyond approximately 0.40 mm, the field-reduction effect overtakes it.

For the multilayer cases, a pronounced outer-layer dominance is observed. In the four-layer case, the outermost layer L4 contributes \(1.665\times10^{-6}\ \mathrm{A^2\cdot m}\) (40.0% of IntH2_total), while the three inner layers L1–L3 each contribute approximately \(8.13\times10^{-7}\) to \(8.57\times10^{-7}\ \mathrm{A^2\cdot m}\) (roughly 20% each). The L4/L1 IntH2 ratio is 2.05. The two-layer case shows L2 contributing 50.6% of IntH2_total; the three-layer case shows L3 contributing 38.2%. In every multilayer case, the outermost layer carries the largest loss-integral contribution. The physical mechanism is discussed in Section IV-B.

The four-layer case achieves the lowest IntH2_total (\(4.160\times10^{-6}\ \mathrm{A^2\cdot m}\)) among all cases with \(V_f \approx 75600\ \mathrm{mm^3}\), 10.5% lower than the single-layer best. This result indicates that multilayer redistribution can improve transverse shielding without increasing the geometry-dependent loss integral under the tested conditions.

### E. Mesh and Boundary-Domain Convergence

Mesh convergence was evaluated for two representative transverse cases: C1_N1_t008_x, the thinnest single-layer shell, and C2_N4_t015_g008_x, the four-layer equal-volume candidate. Three mesh levels were used, corresponding to approximately one, three, and five elements across the ferrite thickness. The exported convergence quantities are listed in Table VI. Total element count and air-domain size were not exported in the current AEDT run and are therefore marked TODO; these metadata must be added before final submission.

**Table VI. Mesh-Convergence Check**

| Case | Mesh level | Total elements | Elements across \(a\) | Air-domain size | \(B_{\mathrm{center},x}\) (T) | SFx | IntH2_total (A\(^2\)m) | \(\Delta B_{\mathrm{center},x}\) | \(\Delta\)SFx | \(\Delta\)IntH2 | Status |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| C1_N1_t008_x | coarse | TODO | 1 | TODO | \(9.265\times10^{-7}\) | 1.356 | \(3.800\times10^{-6}\) | -- | -- | -- | exported |
| C1_N1_t008_x | medium | TODO | 3 | TODO | \(9.375\times10^{-7}\) | 1.340 | \(3.819\times10^{-6}\) | \(1.18\times10^{-2}\) | \(1.19\times10^{-2}\) | \(5.01\times10^{-3}\) | exported |
| C1_N1_t008_x | fine | TODO | 5 | TODO | \(9.375\times10^{-7}\) | 1.340 | \(3.819\times10^{-6}\) | \(1.07\times10^{-10}\) | \(0\) | \(2.62\times10^{-10}\) | passed medium-to-fine |
| C2_N4_t015_g008_x | coarse | TODO | 1 | TODO | \(3.463\times10^{-7}\) | 3.629 | \(4.160\times10^{-6}\) | -- | -- | -- | exported |
| C2_N4_t015_g008_x | medium | TODO | 3 | TODO | \(3.463\times10^{-7}\) | 3.629 | \(4.160\times10^{-6}\) | \(3.15\times10^{-10}\) | \(3.14\times10^{-10}\) | \(9.61\times10^{-12}\) | exported |
| C2_N4_t015_g008_x | fine | TODO | 5 | TODO | \(3.463\times10^{-7}\) | 3.629 | \(4.160\times10^{-6}\) | \(2.89\times10^{-10}\) | \(2.76\times10^{-10}\) | \(0\) | passed medium-to-fine |

[Fig. 7. Mesh and boundary-domain convergence: (a) SFx versus elements across ferrite thickness; (b) IntH2_total versus elements across ferrite thickness; (c) TODO boundary-domain convergence once 2R/3R/5R exports are available.]

Using the medium-to-fine criterion, both cases satisfy the adopted numerical thresholds of \(\Delta\)SFx < 1%, \(\Delta\)IntH2_total < 2%, and \(\Delta B_{\mathrm{center},x}\) < 1%. However, the present convergence table is incomplete because total element counts and air-domain metadata were not exported. Boundary-domain convergence is not yet available; the current template requires 2R, 3R, and 5R air-domain exports for C2_N4_t015_g008_x before boundary effects can be claimed as negligible.

### F. Axial Shielding Check for Equal-Volume Candidates

The \(z\)-directed no-shield reference has been validated, but shielded \(z\)-directed simulations for the equal-volume candidates have not yet been exported. Table VII therefore provides the required result structure and marks the missing quantities explicitly. No SFz-based conclusion is drawn at this stage.

**Table VII. Axial Shielding Check Template**

| Case | \(N_L\) | \(a\) (mm) | \(g\) (mm) | \(V_f\) (mm\(^3\)) | \(B_{\mathrm{center},z}\) (T) | SFz | LeakageRatioz | SFz/SFx | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C1_N1_t060_z | 1 | 0.60 | 0 | 75624 | TODO | TODO | TODO | TODO | pending AEDT export |
| C2_N3_t020_g010_z | 3 | 0.20 | 0.10 | 75700 | TODO | TODO | TODO | TODO | pending AEDT export |
| C2_N4_t015_g008_z | 4 | 0.15 | 0.08 | 75715 | TODO | TODO | TODO | TODO | pending AEDT export |

[Fig. 8. SFx/SFz comparison for equal-volume candidates. TODO: shielded \(z\)-directed exports are required.]

Because the shield is an open-ended cylinder, axial shielding is expected to differ from transverse shielding. The transverse ranking should not be generalized to SFz unless the axial cases support the same trend.

### G. Segmented-Shell Correction for Manufacturable Assembly

The present shielding results are based on continuous cylindrical shells. To connect the model to manufacturable segmented assembly, the leading four-layer case must be compared with segmented aligned and staggered slot patterns. The baseline continuous row is available; the segmented rows are templates pending AEDT export.

**Table VIII. Segmented-Shell Correction Template**

| Case | Segment pattern | \(\eta_\phi\) | \(B_{\mathrm{center},x}\) (T) | SFx | SFx\(_{\mathrm{seg}}\)/SFx\(_{\mathrm{cont}}\) | IntH2_total (A\(^2\)m) | IntH2\(_{\mathrm{seg}}\)/IntH2\(_{\mathrm{cont}}\) | Interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---|
| C2_N4_t015_g008_x | continuous | 1.00 | \(3.463\times10^{-7}\) | 3.629 | 1.000 | \(4.160\times10^{-6}\) | 1.000 | processed baseline |
| S_N4_t015_g008_seg12_aligned_x | aligned | 0.95 | TODO | TODO | TODO | TODO | TODO | pending AEDT export |
| S_N4_t015_g008_seg12_staggered_x | staggered | 0.95 | TODO | TODO | TODO | TODO | TODO | pending AEDT export |

[Fig. 9. Segmented-shell correction. TODO: aligned and staggered segmented exports are required.]

Aligned circumferential slots may form through-wall leakage paths, whereas staggered slots may partially cover the gaps in adjacent layers. The segmented-to-continuous penalty must be quantified before manufacturability claims are made.

### H. Permeability Sensitivity

The processed transverse matrix uses \(\mu_r'=1000\) and \(\sigma=0.01\ \mathrm{S/m}\) as screening material parameters. A sensitivity study is required to test whether the structural ranking remains stable for plausible Mn-Zn ferrite permeability variation. Table IX lists the required sweep. Only the \(\mu_r'=1000\) baseline rows are currently available; all other values are TODO.

**Table IX. Permeability-Sensitivity Template**

| Base case | \(\mu_r'\) | \(B_{\mathrm{center},x}\) (T) | SFx | LeakageRatiox | IntH2_total (A\(^2\)m) | \(\eta_S^*\) | \(\rho_H\) | \(\chi_H\) | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| C1_N1_t060_x | 500 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |
| C1_N1_t060_x | 1000 | \(4.418\times10^{-7}\) | 2.845 | 0.352 | \(4.649\times10^{-6}\) | 1.045 | \(6.15\times10^{-11}\) | \(4.45\times10^{-6}\) | processed baseline |
| C1_N1_t060_x | 2000 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |
| C1_N1_t060_x | 5000 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |
| C2_N4_t015_g008_x | 500 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |
| C2_N4_t015_g008_x | 1000 | \(3.463\times10^{-7}\) | 3.629 | 0.276 | \(4.160\times10^{-6}\) | 1.287 | \(5.49\times10^{-11}\) | \(3.23\times10^{-6}\) | processed baseline |
| C2_N4_t015_g008_x | 2000 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |
| C2_N4_t015_g008_x | 5000 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | pending |

[Fig. 10. Permeability sensitivity. TODO: \(\mu_r'=500,2000,5000\) exports are required.]

No robustness claim with respect to \(\mu_r'\) is made until the sweep is completed. If the ranking changes with permeability, the current transverse conclusion must be treated as material-parameter dependent.

### I. Prototype-Level Shielding-Factor Measurement Protocol

No prototype shielding-factor measurement has been performed in the current dataset. The required experimental workflow is retained as a protocol: measure \(B_{0,q}\) at the center with a calibrated Helmholtz or triaxial coil system, insert the shield without moving the sensor, measure \(B_{\mathrm{center},q}\), and compute

\[
\mathrm{SF}_{q,\mathrm{exp}}=\frac{|B_{0,q}|}{|B_{\mathrm{center},q}|}.
\]

For independent measurements, the relative uncertainty is

\[
\frac{u(\mathrm{SF}_{q,\mathrm{exp}})}{\mathrm{SF}_{q,\mathrm{exp}}}
=
\sqrt{
\left[\frac{u(B_{0,q})}{B_{0,q}}\right]^2+
\left[\frac{u(B_{\mathrm{center},q})}{B_{\mathrm{center},q}}\right]^2
}.
\]

If the no-shield and shielded measurements share correlated coil-current or sensor-calibration terms, the correlated form is

\[
u_r^2(\mathrm{SF}_{q,\mathrm{exp}})=
u_r^2(B_0)+u_r^2(B_{\mathrm{center}})
-2\rho\,u_r(B_0)u_r(B_{\mathrm{center}}).
\]

The experimental CSV template has been added, but no experimental SF value is reported.

## IV. Discussion

### A. Why Multilayer Design Improves Shielding at Fixed Volume

The fixed-volume comparison in Table IV shows a clear but non-uniform benefit from multilayer construction. Moving from one to three layers at constant \(T_f = 0.60\ \mathrm{mm}\) yields a 5.2% SFx improvement, while moving from three to four layers (with modestly thinner individual layers, \(a = 0.15\) vs. 0.20 mm) yields a 21.2% SFx improvement. This nonlinearity can be understood from the magnetic circuit perspective.

In a cylindrical shield under transverse excitation, the shielding effectiveness depends on the reluctance of the flux-shunting path through the ferrite sidewall. A single thick layer provides one continuous path. Multiple layers separated by gaps introduce additional ferrite-air interfaces and redistribute the magnetic flux among the layers. The improvement is attributed to flux redistribution among multiple high-permeability layers and interlayer gaps. This interpretation should be supported by magnetic-flux-density contour plots and flux-line visualizations.

The observed improvement from \(N_L = 3\) to \(N_L = 4\) suggests that the shielding benefit is not governed by total ferrite volume alone. It may depend on the coupled choice of layer thickness, radial gap, and total radial occupation. A denser parametric sweep is required before this behavior can be interpreted as a threshold effect.

### B. Outer-Layer Dominance of the Loss Indicator

The layer-resolved IntH2 data reveal a consistent outer-layer dominance across all multilayer cases: L2 contributes 50.6% of IntH2_total in the two-layer case, L3 contributes 38.2% in the three-layer case, and L4 contributes 40.0% in the four-layer case.

This outer-layer dominance should be interpreted from the finite-element distribution of \(H_{\mathrm{vc}}^2\) within the virtual pickup-coil model, rather than from a simple radial-distance argument. In the virtual pickup-coil model, the excitation source is at the center: the virtual coil carries current \(I_0\) and generates a dipole-like magnetic field that propagates outward through the shielded volume and into the ferrite layers. Although the inner layer (L1) is closest to the virtual coil, the high-permeability multilayer structure redistributes the coil-generated magnetic flux. The outer layer can carry a larger volume-integrated \(H_{\mathrm{vc}}^2\) because it participates strongly in the flux-return path in the surrounding region. Therefore, the layer-resolved IntH2 distribution reflects the combined effects of distance from the coil, permeability contrast between ferrite layers and vacuum gaps, flux redistribution at each ferrite-vacuum interface, and the differing ferrite volumes of each layer.

It is important to note that this virtual-coil-field mechanism is distinct from the external uniform-field mechanism that governs the shielding factor. In the external-field model, the outermost layer is the first to intercept the applied field and provides the primary flux-shunting path. In the virtual-coil model, the innermost layer is closest to the source, but the outer layers can still dominate the integrated \(H^2\) because of their participation in the flux-return circuit. The two models serve complementary purposes: the external-field model evaluates shielding performance, while the virtual-coil model evaluates the geometric factor that couples material loss to measured field noise.

[Fig. 5. Virtual pickup-coil field distribution: (a) model geometry with coil at center; (b) \(H_{\mathrm{vc}}\) magnitude contour plot on the transverse mid-plane, showing dipole-like field pattern and attenuation through ferrite layers; (c) \(H_{\mathrm{vc}}^2\) distribution on the same plane, highlighting the outer-layer concentration; (d) bar chart of layer-resolved IntH2 fractions for the four-layer case (L1: 19.5%, L2: 19.8%, L3: 20.6%, L4: 40.0%).]

This interpretation should be supported by \(H_{\mathrm{vc}}\) or \(H_{\mathrm{vc}}^2\) contour plots in the virtual pickup-coil model (see Fig. 5 placeholder). Field-map visualization would confirm whether the outer-layer dominance in the integrated \(H_{\mathrm{vc}}^2\) corresponds to regions of concentrated field near the outer-layer boundaries, as the flux-return-path hypothesis suggests.

The finding suggests a possible design implication for low-noise shields: if the outer-layer dominance is confirmed by field maps and experimental noise measurements, strategies that reduce the \(H_{\mathrm{vc}}\) field in this layer, such as using lower-loss ferrite for the outermost layer, may reduce the shield-induced noise contribution. This implication remains conditional on measured \(\mu_r''(f)\) and instrument-level validation.

### C. Contribution to Measurement Science and Low-Noise Instrumentation

This work contributes to measurement science in three specific ways. First, the validated no-shield reference with a direction-purity ratio exceeding \(10^6\) establishes a methodology for calibrating finite-element shield models against a well-defined uniform-field measurement configuration—a prerequisite for quantitative shielding-factor comparisons across studies. Second, the layer-resolved IntH2 analysis provides a noise-budgeting tool for instrument designers: by identifying which layer contributes most to the geometry-dependent loss, the analysis guides targeted material optimization (e.g., using lower-loss ferrite for the outermost layer) rather than uniform material specification across all layers. Third, the pipeline from boundary-condition validation through directional SF calculation to layerwise IntH2 verification is fully automated and reproducible; the same scripts can process new geometries, materials, and field directions without modification, lowering the barrier for systematic shield evaluation in the instrumentation community.

## V. Conclusions

A finite-element evaluation framework for multilayer thin-ferrite cylindrical shields has been developed and demonstrated on seven transverse continuous-shell candidates under a validated x-directed tangential-H boundary condition. A validated z-directed no-shield reference, mesh-convergence processing, and templates for axial shielding, segmented-shell correction, permeability sensitivity, field-map export, and prototype SF measurement have also been added to define the remaining submission-critical validation path. The principal findings supported by the current exported data are:

1. The four-layer architecture (\(N_L = 4\), \(a = 0.15\ \mathrm{mm}\), \(g = 0.08\ \mathrm{mm}\)) achieves a shielding factor SFx = 3.629 at ferrite volume \(V_f = 75715\ \mathrm{mm^3}\), 27.6% higher than the best single-layer design at equal ferrite usage, with a modest additional radial occupation of 0.24 mm.

2. The outermost ferrite layer contributes 40% of the total geometry-dependent loss indicator IntH2. This observation is derived from the virtual pickup-coil model and should be supported by \(H_{\mathrm{vc}}^2\) field-map visualization before being used as a general physical explanation.

3. Under the tested transverse continuous-shell conditions with screening material parameters, the four-layer candidate simultaneously achieves the highest SFx and the lowest IntH2_total among the equal-volume candidates. This is an indicative transverse continuous-shell ranking, not a geometry-independent design rule.

4. The directional shielding factor definition and no-shield reference validation provide a measurement-calibrated baseline for both transverse and axial field directions. Mesh convergence for the two representative x-directed cases satisfies the adopted medium-to-fine criteria, although total element counts and boundary-domain convergence still need to be exported.

The present study still has limitations that must be addressed before direct instrument-level adoption:

- **Material parameters**: The use of screening material parameters (\(\mu_r' = 1000\), \(\sigma = 0.01\ \mathrm{S/m}\)) limits the generality of the reported ranking. The robustness of the geometric ranking with respect to \(\mu_r'\), \(\mu_r''(f)\), and conductivity must be verified through material characterization and permeability-sensitivity analysis.

- **Axial shielded cases pending**: The z-directed no-shield reference has been validated, but the selected shielded SFz cases have not yet been exported. Transverse conclusions must not be generalized to axial shielding.

- **Continuous-shell-only main result**: All processed shielding cases are continuous cylindrical shells. Segmented-shell configurations with circumferential gaps, required for practical assembly from flat ferrite sheets, remain pending.

- **No prototype experimental validation**: The experimental protocol specified in Section II-I has not been executed. Direct SFx/SFz measurements and indirect IntH2 validation through measured magnetic-noise spectra are still required.

- **Boundary-domain convergence and mesh metadata**: Mesh-convergence values are available for C1_N1_t008_x and C2_N4_t015_g008_x, but total element counts and air-domain metadata were not exported. Boundary-domain convergence remains pending.

The remaining validation items before IEEE TIM submission are: (i) shielded SFz exports for selected equal-volume candidates; (ii) segmented aligned and staggered shell exports for the leading four-layer candidate; (iii) permeability sensitivity exports for \(\mu_r'=500, 2000,\) and 5000; (iv) boundary-domain convergence for 2R, 3R, and 5R air-domain scales; (v) AEDT field-map exports for \(B\), flux lines, \(H_{\mathrm{vc}}\), and \(H_{\mathrm{vc}}^2\); and (vi) prototype-level SF measurement if experimental hardware is available. Until these checks are complete, the framework should be regarded as a reproducible measurement-oriented evaluation workflow for candidate comparison.
## References

[1] J. C. Allred, R. N. Lyman, T. W. Kornack, and M. V. Romalis, "High-sensitivity atomic magnetometer unaffected by spin-exchange relaxation," *Phys. Rev. Lett.*, vol. 89, no. 13, Sep. 2002, Art. no. 130801.

[2] I. K. Kominis, T. W. Kornack, J. C. Allred, and M. V. Romalis, "A subfemtotesla multichannel atomic magnetometer," *Nature*, vol. 422, no. 6932, pp. 596–599, Apr. 2003.

[3] M. P. Ledbetter, I. M. Savukov, V. M. Acosta, D. Budker, and M. V. Romalis, "Spin-exchange-relaxation-free magnetometry with Cs vapor," *Phys. Rev. A*, vol. 77, no. 3, Mar. 2008, Art. no. 033408.

[4] S. Baillet, "Magnetoencephalography for brain electrophysiology and imaging," *Nature Neurosci.*, vol. 20, no. 3, pp. 327–339, Mar. 2017.

[5] T. E. Chupp, P. Fierlinger, M. J. Ramsey-Musolf, and J. T. Singh, "Electric dipole moments of atoms, molecules, nuclei, and particles," *Rev. Mod. Phys.*, vol. 91, no. 1, Jan. 2019, Art. no. 015001.

[6] T. J. Sumner, J. M. Pendlebury, and K. F. Smith, "Conventional magnetic shielding," *J. Phys. D: Appl. Phys.*, vol. 20, no. 9, pp. 1095–1101, Sep. 1987.

[7] V. Kelha, J. Pukki, R. Peltonen, A. Penttinen, R. Ilmoniemi, and J. Heino, "Design, construction, and performance of a large-volume magnetic shield," *IEEE Trans. Magn.*, vol. 18, no. 1, pp. 260–270, Jan. 1982.

[8] I. Altarev *et al.*, "A magnetically shielded room with ultra low residual field and gradient," *Rev. Sci. Instrum.*, vol. 85, no. 7, Jul. 2014, Art. no. 075106.

[9] S.-K. Lee and M. V. Romalis, "Calculation of magnetic field noise from high-permeability magnetic shields and conducting objects with simple geometry," *J. Appl. Phys.*, vol. 103, no. 8, Apr. 2008, Art. no. 084904.

[10] H. B. Dang, A. C. Maloof, and M. V. Romalis, "Ultrahigh sensitivity magnetic field and magnetization measurements with an atomic magnetometer," *Appl. Phys. Lett.*, vol. 97, no. 15, Oct. 2010, Art. no. 151110.

[11] D. Ma *et al.*, "A novel low-noise mu-metal magnetic shield with winding shape," *Sens. Actuators A, Phys.*, vol. 346, Oct. 2022, Art. no. 113884.

[12] T. W. Kornack, S. J. Smullin, S.-K. Lee, and M. V. Romalis, "A low-noise ferrite magnetic shield," *Appl. Phys. Lett.*, vol. 90, no. 22, May 2007, Art. no. 223501.

[13] D. Ma *et al.*, "Parameter modeling analysis of a cylindrical ferrite magnetic shield to reduce magnetic noise," *IEEE Trans. Ind. Electron.*, vol. 69, no. 1, pp. 991–998, Jan. 2022.

[14] J. Lu *et al.*, "Study of magnetic noise of a multi-annular ferrite shield," *IEEE Access*, vol. 8, pp. 40918–40924, 2020.

[15] B. Sun *et al.*, "Correlating the microstructure of Mn–Zn ferrite with magnetic noise for magnetic shield applications," *Ceram. Int.*, vol. 49, no. 8, pp. 11960–11967, Apr. 2023.

[16] B. Sun, D. Ma, X. Fang, Y. Xue, J. Lu, H. Chen, M. Zhang, H. Wei, B. Han, and Y. Zhai, "Suppression of magnetic noise and field in cubic low-noise ferrite magnetic shields," *IEEE Trans. Instrum. Meas.*, vol. 73, pp. 1–10, 2024, Art. no. 1501810.

[17] J. Lu *et al.*, "Effect of gaps on magnetic noise of cylindrical ferrite shield," *J. Phys. D: Appl. Phys.*, vol. 54, no. 25, Jun. 2021, Art. no. 255002.

[18] R. Kubo, "The fluctuation-dissipation theorem," *Rep. Prog. Phys.*, vol. 29, no. 1, pp. 255–284, Jan. 1966.

[19] C. Liu *et al.*, "Investigation on the effects of micro-vibration on the atomic comagnetometer," *IEEE Trans. Instrum. Meas.*, vol. 72, 2023, Art. no. 9511711.

[20] P. Dutta and P. M. Horn, "Low-frequency fluctuations in solids: \(1/f\) noise," *Rev. Mod. Phys.*, vol. 53, no. 3, pp. 497–516, Jul. 1981.

[21] K. Yang *et al.*, "Improved measurement of the low-frequency complex permeability of ferrite annulus for low-noise magnetic shielding," *IEEE Access*, vol. 7, pp. 126059–126065, 2019.

[22] K. Yang *et al.*, "Minimizing magnetic fields of the low-noise MnZn ferrite magnetic shield for atomic magnetometer," *J. Phys. D: Appl. Phys.*, vol. 55, no. 1, Jan. 2022, Art. no. 015003.

[23] Z. Xu, Z. Zhang, B. Wu, H. Wang, X. Kong, and M. Wang, "A study of enclosed magnetic shielding room by simulation," *IEEE Trans. Appl. Supercond.*, vol. 31, no. 8, pp. 1–5, Nov. 2021.

[24] X. Xu, L. Wang, W. Liu, and Z. Zhao, "Theoretical modeling and characterization of equivalent magnetic properties in laminated composite magnetic shielding," *Measurement*, vol. 251, 2025, Art. no. 117237.

[25] *Cores Made of Soft Magnetic Materials—Measuring Methods—Part 2: Magnetic Properties at Low Excitation Level*, IEC 62044-2, 2005.

[26] TDK Corporation, "Mn–Zn ferrite material characteristics: PC95 and related Mn–Zn ferrite grades," product catalog, accessed May 2026. [Online]. Available: https://product.tdk.com/system/files/dam/doc/product/ferrite/ferrite/ferrite-core/catalog/ferrite_mn-zn_material_characteristics_en.pdf

[27] A. Mager, "Magnetic shields," *IEEE Trans. Magn.*, vol. 6, no. 1, pp. 67–75, Mar. 1970.

[28] K. Nagashima, I. Sasada, and K. Tashiro, "High-performance bench-top cylindrical magnetic shield with magnetic shaking enhancement," *IEEE Trans. Magn.*, vol. 38, no. 5, pp. 3335–3337, Sep. 2002.

[29] J. M. G. D. K. O'Connell, J. M. Brown, and T. W. Kornack, "Technique for high axial shielding factor performance of large-scale, thin, open-ended, cylindrical Metglas magnetic shields," arXiv:1107.2625, 2011.

[30] J. Fang, S. Wan, J. Qin, and Y. Chen, "A novel method for in-situ measuring the static shielding factor of a magnetic shield," *Measurement*, vol. 170, 2021, Art. no. 108718.

[31] T. Brys *et al.*, "Magnetic field stabilization for magnetically shielded volumes by external field coils," *J. Appl. Phys.*, vol. 116, no. 8, 2014, Art. no. 084903.
