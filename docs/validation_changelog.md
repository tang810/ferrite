# Manuscript and Validation Changelog

## 2026-05-28 Update

- Reworked the manuscript into an IEEE TIM-oriented internal review draft with the requested five-section structure:
  - I. Introduction
  - II. Measurement-Oriented Characterization Methodology
  - III. Validation Matrix and Planned Experimental Campaign
  - IV. Expected Results Organization for the Full Manuscript
  - V. Summary of Current Draft and Next-Step Work
- Replaced the previous Results/Discussion/Conclusion structure with a planned validation campaign and full-manuscript roadmap.
- Removed repeated Results-style statements for incomplete axial, segmented, permeability-sensitivity, and field-map studies.
- Rewrote the Abstract as a method-and-plan abstract for internal review, without claiming completion of planned simulations or experiments.
- Kept the current formal title.
- Added `docs/internal_review_note_for_senior.md`, a one-page Chinese note for internal review.

## Earlier 2026-05-28 Data-Gated Draft Update

- Added a follow-up edit for the `paper_intro_methods(1).tex` / `paper_intro_methods(3).pdf` request. No separate files with those suffixes were found in the workspace, so the active `paper_intro_methods.tex` and `paper_intro_methods.pdf` were updated.
- Rewrote the Abstract to report only completed validation and eligible transverse continuous-shell conclusions.
- Updated the Introduction contribution language from an evaluation/data pipeline emphasis to a measurement-oriented characterization method.
- Merged duplicate contribution paragraphs in the Introduction.
- Compressed the prototype measurement protocol in Methods and moved the uncertainty equations to an Appendix note.
- Reorganized Results subsections to match the requested IEEE TIM-oriented structure:
  - IV.A Directional Reference Validation
  - IV.B Transverse Continuous-Shell Characterization
  - IV.C Equal-Volume Comparison
  - IV.D Layer-Resolved IntH2 Distribution
  - IV.E Mesh and Boundary-Domain Convergence
  - IV.F Axial Shielding Characterization
  - IV.G Segmented-Shell Correction
  - IV.H Permeability Sensitivity
  - IV.I Field-Map Interpretation
- Expanded the mesh convergence table to include mesh level, total elements, elements across ferrite thickness, adaptive passes, `Bcenter_x`, `SFx`, `IntH2_total`, and relative change columns.
- Expanded the mesh convergence table to include air-domain scale.
- Marked unavailable mesh metadata explicitly: total element count, adaptive passes, and air-domain scale were not exported.
- Kept boundary-domain convergence out of conclusions because 2R, 3R, and 5R exports are still pending.
- Added explicit axial shielding text stating that `B0_reference_z` passed but shielded z cases are missing, so `SFz`, `LeakageRatioz`, and `SFz/SFx` are not reported.
- Added explicit segmented-shell text for `C2_N4_t015_g008_x`, `Nseg=12`, `g_phi=1.6 mm`; aligned and staggered results remain pending.
- Added explicit permeability-sensitivity text for the required `mu_r'=500, 1000, 2000, 5000` comparison; only `mu_r'=1000` baselines are available.
- Rewrote Discussion to focus on low-noise instrumentation relevance, directionality, IntH2 as a magnetic-noise-related loss indicator, and unresolved material/manufacturing sensitivity.
- Rewrote Conclusion to limit claims to transverse continuous-shell cases and avoid final instrument-level recommendations.

## Updated CSV and Tracking Files

- `data/processed/mesh_convergence_metrics.csv`
  - Added `adaptive_passes`.
  - Retained `air_domain_size`/air-domain scale as blank because it was not exported.
  - Preserved missing metadata as blank values rather than fabricating values.
- `data/raw/mesh_convergence_exports.csv`
  - Added a blank `adaptive_passes` column so future exports can fill it directly.
- `data/validation/mesh_convergence_validation.csv`
  - Updated metadata status to include missing adaptive-pass metadata.
- `scripts/postprocess/process_validation_studies.py`
  - Updated mesh processing schema so future runs preserve the adaptive-pass column.
- `docs/remaining_todo.md`
  - Rewritten as a clean list of results that still cannot enter conclusions.

## Results Still Not Eligible

- Boundary-domain convergence at 2R, 3R, and 5R.
- Shielded axial cases and `SFz` metrics.
- Segmented aligned and segmented staggered correction.
- Permeability sweeps beyond `mu_r'=1000`.
- Field-map-based mechanism interpretation.
- Prototype SF measurements.
