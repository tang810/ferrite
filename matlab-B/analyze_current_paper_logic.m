%% analyze_current_paper_logic.m
% Build the current paper evidence chain from Maxwell exports and experiment
% templates.
%
% Outputs:
%   ../analysis_ready/matlab_B_results/current_paper_structure_basis.csv
%   ../analysis_ready/matlab_B_results/current_paper_hybrid_enhancement.csv
%   ../analysis_ready/matlab_B_results/current_paper_axial_cap_tradeoff.csv
%   ../analysis_ready/matlab_B_results/current_paper_required_results.csv
%   ../analysis_ready/matlab_B_results/current_paper_noise_proxy_1to30Hz.csv
%   ../analysis_ready/matlab_B_results/current_paper_material_loss_sensitivity.csv
%   ../analysis_ready/matlab_B_results/current_paper_hybrid_SF_IntH2.png
%   ../analysis_ready/matlab_B_results/current_paper_axial_cap_tradeoff.png

clear; clc;

script_dir = fileparts(mfilename('fullpath'));
root_dir = fileparts(script_dir);
raw_dir = fullfile(root_dir, 'data', 'raw');
processed_dir = fullfile(root_dir, 'data', 'processed');
out_dir = fullfile(root_dir, 'analysis_ready', 'matlab_B_results');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

%% Constants and baseline values
% Keep these constants explicit so the paper text can cite the same
% assumptions as the calculation.
kB = 1.380649e-23;
Temp_K = 300;
freq_Hz = (1:30).';
mu0 = 4*pi*1e-7;

% Existing legacy scripts use these pickup-coil placeholders. Use ratios
% for conclusions unless the real sensor/coil calibration is available.
Nturns = 1;
I_A = 1;
pickup_area_m2 = 1;

% Ferrite loss assumption inherited from the older MATLAB scripts. Metallic
% amorphous/nanocrystalline loss should be treated as a sensitivity sweep.
mu_pp_ferrite_over_mu0 = 6.1;
mu_pp_ferrite = mu_pp_ferrite_over_mu0 * mu0;

% Confirmed ferrite-only transverse baseline.
base_x_case = "C2_N4_t015_g008_x";
base_x_SFx = 3.62910729;
base_x_IntH2 = 4.16011287324e-06;
base_x_B0_T = 1.25663682659e-06;

% Confirmed ferrite-only axial baseline.
base_z_case = "C2_N4_t015_g008_z";
base_z_B0_T = 1.25663644033e-06;
base_z_Bcenter_T = 5.20892809375e-07;
base_z_SFz = base_z_B0_T / base_z_Bcenter_T;
base_z_IntH2 = 2.97131561251e-06;

% Geomagnetic residual-field estimate. This is a scaling estimate under the
% linear-permeability assumption, not a nonlinear B-H saturation simulation.
Bgeo_T = 50e-6;

%% 1. Structure optimization evidence: why four ferrite layers are the base
StructureBasis = table( ...
    base_x_case, ...
    100, 200, 4, 0.15, 0.08, 0.60, 0.84, ...
    base_x_SFx, base_x_IntH2, base_x_B0_T, ...
    "Chosen as manufacturable validation base, not claimed as global optimum.", ...
    'VariableNames', {'case_id','Rin_mm','L_mm','N','layer_t_mm','gap_mm', ...
    'total_ferrite_t_mm','radial_Tspace_mm','SFx','IntH2_total','B0_Bx_T','paper_claim'});
writetable(StructureBasis, fullfile(out_dir, 'current_paper_structure_basis.csv'));

%% 2. Hybrid enhancement evidence: amorphous vs nanocrystalline outer layer
hybrid_csv = fullfile(processed_dir, 'hybrid_outer_layer_metrics.csv');
if ~isfile(hybrid_csv)
    hybrid_csv = fullfile(raw_dir, 'hybrid_outer_layer_exports.csv');
end
Hybrid = readtable(hybrid_csv, 'Delimiter', ',', 'TextType', 'string', 'VariableNamingRule', 'preserve');

if ~ismember('SFx_gain_vs_ferrite', Hybrid.Properties.VariableNames)
    Hybrid.SFx_gain_vs_ferrite = Hybrid.SFx ./ base_x_SFx;
end
if ~ismember('IntH2_ratio_vs_ferrite', Hybrid.Properties.VariableNames)
    Hybrid.IntH2_ratio_vs_ferrite = Hybrid.IntH2_total ./ base_x_IntH2;
end

Hybrid.noise_amp_ratio_same_mu_pp = sqrt(Hybrid.IntH2_ratio_vs_ferrite);
Hybrid.paper_use = repmat("Use for hybrid SF-IntH2 tradeoff.", height(Hybrid), 1);
if ismember('outer_material', Hybrid.Properties.VariableNames)
    idx_nano = Hybrid.outer_material == "nanocrystalline";
    Hybrid.paper_use(idx_nano) = "Priority candidate: highest SFx and lowest IntH2 among current outer-layer cases.";
end
writetable(Hybrid, fullfile(out_dir, 'current_paper_hybrid_enhancement.csv'));

%% 3. Axial cap evidence: single-side nanocrystalline cap
cap_export_csv = fullfile(raw_dir, 'axial_single_nanocrystalline_cap_exports.csv');
cap_int_csv = fullfile(raw_dir, 'axial_single_nanocrystalline_cap_intH2.csv');
p0_export_csv = fullfile(raw_dir, 'p0_amorphous_single_shell_cap_exports.csv');
p0_int_csv = fullfile(raw_dir, 'p0_amorphous_single_shell_cap_intH2.csv');

CapExport = readtable(cap_export_csv, 'Delimiter', ',', 'TextType', 'string', 'VariableNamingRule', 'preserve');
CapInt = readtable(cap_int_csv, 'Delimiter', ',', 'TextType', 'string', 'VariableNamingRule', 'preserve');
P0Export = readtable(p0_export_csv, 'Delimiter', ',', 'TextType', 'string', 'VariableNamingRule', 'preserve');
P0Int = readtable(p0_int_csv, 'Delimiter', ',', 'TextType', 'string', 'VariableNamingRule', 'preserve');

cap_SFz = CapExport.SFz(1);
cap_IntH2_ferrite = CapInt.IntH2_ferrite_only(1);
cap_IntH2_cap = CapInt.IntH2_caps(1);
cap_IntH2_total = CapInt.IntH2_total_with_caps(1);

p0_SFz = P0Export.SFz(1);
p0_IntH2_shell = P0Int.IntH2_shell(1);
p0_IntH2_cap = P0Int.IntH2_cap(1);
p0_IntH2_total = P0Int.IntH2_total(1);

AxialCap = table( ...
    ["open_ferrite_only"; P0Export.case_id(1); CapExport.case_id(1)], ...
    ["four-layer ferrite, open ends"; "P0 amorphous shell + single +Z amorphous cap"; "four-layer ferrite + single +Z nanocrystalline cap"], ...
    [base_z_SFz; p0_SFz; cap_SFz], ...
    [1/base_z_SFz; P0Export.LeakageRatioz(1); CapExport.LeakageRatioz(1)], ...
    [base_z_IntH2; p0_IntH2_total; cap_IntH2_total], ...
    [base_z_IntH2; 0; cap_IntH2_ferrite], ...
    [0; p0_IntH2_shell + p0_IntH2_cap; cap_IntH2_cap], ...
    [1; p0_SFz/base_z_SFz; cap_SFz/base_z_SFz], ...
    [1; p0_IntH2_total/base_z_IntH2; cap_IntH2_total/base_z_IntH2], ...
    [1; sqrt(p0_IntH2_total/base_z_IntH2); sqrt(cap_IntH2_total/base_z_IntH2)], ...
    ["Baseline for axial leakage."; "P0 reference improves SFz slightly and has lower IntH2 integral, but amorphous mu'' must be measured or swept."; "Improves SFz but increases IntH2; PSD experiment is needed before claiming sensitivity improvement."], ...
    'VariableNames', {'case_id','configuration','SFz','LeakageRatioz','IntH2_total', ...
    'IntH2_ferrite','IntH2_cap','SFz_gain_vs_open','IntH2_ratio_vs_open', ...
    'noise_amp_ratio_same_mu_pp','paper_claim'});
writetable(AxialCap, fullfile(out_dir, 'current_paper_axial_cap_tradeoff.csv'));

%% 4. Material-separated noise proxy
% deltaB^2 is proportional to sum(mu_pp_i * IntH2_i). This section keeps
% ferrite and high-permeability metallic material separated.
NoiseRows = table();

% Ferrite-only x baseline.
NoiseRows = [NoiseRows; make_noise_row("x_ferrite_only", "ferrite", ...
    base_x_SFx, base_x_IntH2, 0, mu_pp_ferrite_over_mu0, NaN, ...
    freq_Hz, Temp_K, Nturns, I_A, pickup_area_m2, mu0, kB)];

% Hybrid x cases. Treat non-ferrite mu''/mu0 as NaN here; actual values are
% handled in the sensitivity sweep below.
for i = 1:height(Hybrid)
    q_outer = 0;
    if ismember('IntH2_outer', Hybrid.Properties.VariableNames) && isfinite(Hybrid.IntH2_outer(i))
        q_outer = Hybrid.IntH2_outer(i);
    end
    q_ferrite = max(Hybrid.IntH2_total(i) - q_outer, 0);
    label = "x_" + Hybrid.outer_material(i);
    NoiseRows = [NoiseRows; make_noise_row(label, Hybrid.outer_material(i), ...
        Hybrid.SFx(i), q_ferrite, q_outer, mu_pp_ferrite_over_mu0, NaN, ...
        freq_Hz, Temp_K, Nturns, I_A, pickup_area_m2, mu0, kB)];
end

% Axial cap rows.
NoiseRows = [NoiseRows; make_noise_row("z_open_ferrite_only", "ferrite", ...
    base_z_SFz, base_z_IntH2, 0, mu_pp_ferrite_over_mu0, NaN, ...
    freq_Hz, Temp_K, Nturns, I_A, pickup_area_m2, mu0, kB)];
NoiseRows = [NoiseRows; make_noise_row("z_p0_amorphous_shell_cap", "amorphous", ...
    p0_SFz, 0, p0_IntH2_total, mu_pp_ferrite_over_mu0, NaN, ...
    freq_Hz, Temp_K, Nturns, I_A, pickup_area_m2, mu0, kB)];
NoiseRows = [NoiseRows; make_noise_row("z_single_nanocrystalline_cap", "nanocrystalline_cap", ...
    cap_SFz, cap_IntH2_ferrite, cap_IntH2_cap, mu_pp_ferrite_over_mu0, NaN, ...
    freq_Hz, Temp_K, Nturns, I_A, pickup_area_m2, mu0, kB)];

writetable(NoiseRows, fullfile(out_dir, 'current_paper_noise_proxy_1to30Hz.csv'));

%% 5. Sensitivity sweep for unknown amorphous/nanocrystalline mu''
loss_ratio_vec = [0.1; 0.3; 1; 3; 10; 30; 100];
Sensitivity = table();
for i = 1:height(Hybrid)
    q_outer = 0;
    if ismember('IntH2_outer', Hybrid.Properties.VariableNames) && isfinite(Hybrid.IntH2_outer(i))
        q_outer = Hybrid.IntH2_outer(i);
    end
    q_ferrite = max(Hybrid.IntH2_total(i) - q_outer, 0);
    Sensitivity = [Sensitivity; make_loss_sweep("x_" + Hybrid.outer_material(i), ...
        q_ferrite, q_outer, base_x_IntH2, loss_ratio_vec)];
end
Sensitivity = [Sensitivity; make_loss_sweep("z_single_nanocrystalline_cap", ...
    cap_IntH2_ferrite, cap_IntH2_cap, base_z_IntH2, loss_ratio_vec)];
Sensitivity = [Sensitivity; make_loss_sweep("z_p0_amorphous_shell_cap", ...
    0, p0_IntH2_total, base_z_IntH2, loss_ratio_vec)];
writetable(Sensitivity, fullfile(out_dir, 'current_paper_material_loss_sensitivity.csv'));

%% 6. Geomagnetic residual-field scaling estimate
GeomagX = table( ...
    repmat("x", height(Hybrid), 1), Hybrid.case_id, Hybrid.SFx, ...
    Bgeo_T ./ Hybrid.SFx, (Bgeo_T ./ Hybrid.SFx) * 1e6, ...
    repmat("linear SF scaling from 50 uT external field", height(Hybrid), 1), ...
    'VariableNames', {'field_dir','case_id','SF','Bcenter_geo_T','Bcenter_geo_uT','notes'});

GeomagZ = table( ...
    repmat("z", height(AxialCap), 1), AxialCap.case_id, AxialCap.SFz, ...
    Bgeo_T ./ AxialCap.SFz, (Bgeo_T ./ AxialCap.SFz) * 1e6, ...
    repmat("linear SF scaling from 50 uT external field", height(AxialCap), 1), ...
    'VariableNames', {'field_dir','case_id','SF','Bcenter_geo_T','Bcenter_geo_uT','notes'});

GeomagResidual = [GeomagX; GeomagZ];
writetable(GeomagResidual, fullfile(out_dir, 'current_paper_geomagnetic_residual_estimates.csv'));

%% 7. Result requirements for the paper evidence chain
RequiredResults = table( ...
    ["Structure optimization"; "Hybrid enhancement"; "Axial cap tradeoff"; ...
     "Prototype shielding factor"; "Magnetometer PSD"; "Material loss support"], ...
    ["Why four-layer ferrite is selected as base"; ...
     "Why add outer amorphous/nanocrystalline, and why prefer nanocrystalline"; ...
     "Whether single-side cap reduces axial leakage without excessive noise proxy"; ...
     "Whether fabricated samples reproduce simulated SF"; ...
     "Whether magnetometer sensitivity actually improves"; ...
     "Whether assumed mu'' values are physically defensible"], ...
    ["manufacturable_thin + current_paper_structure_basis.csv"; ...
     "hybrid_outer_layer_metrics.csv + current_paper_hybrid_enhancement.csv"; ...
     "axial_single_nanocrystalline_cap_*.csv + current_paper_axial_cap_tradeoff.csv"; ...
     "prototype_sf_measurement.csv"; ...
     "magnetometer_sensitivity_measurement.csv"; ...
     "datasheet or impedance/B-H loss measurement, plus current_paper_material_loss_sensitivity.csv"], ...
    ["available"; "available for x direction"; "available for single +Z nanocrystalline cap"; ...
     "pending physical experiment"; "pending physical experiment"; "pending or parametric only"], ...
    ["Can say four-layer is a manufacturable validation candidate, not global optimum."; ...
     "Can say nanocrystalline is the current preferred outer layer by simulated SFx and IntH2."; ...
     "Can say cap improves SFz but increases IntH2, so PSD must decide sensitivity benefit."; ...
     "Needed before claiming real shielding improvement."; ...
     "Needed before claiming magnetometer sensitivity improvement."; ...
     "Needed to avoid overclaiming magnetic-noise prediction for metallic high-mu layers."], ...
    'VariableNames', {'evidence_block','paper_question','required_data','status','allowed_claim'});
writetable(RequiredResults, fullfile(out_dir, 'current_paper_required_results.csv'));

%% 8. Figures
try
    fig1 = figure('Color', 'w', 'Name', 'Hybrid SF-IntH2');
    scatter(Hybrid.IntH2_total, Hybrid.SFx, 70, 'filled');
    set(gca, 'XScale', 'log');
    grid on;
    xlabel('IntH2 total');
    ylabel('SFx');
    title('Hybrid outer-layer SF-IntH2 tradeoff');
    if ismember('label', Hybrid.Properties.VariableNames)
        text(Hybrid.IntH2_total, Hybrid.SFx, "  " + Hybrid.label, 'Interpreter', 'none');
    else
        text(Hybrid.IntH2_total, Hybrid.SFx, "  " + Hybrid.outer_material, 'Interpreter', 'none');
    end
    saveas(fig1, fullfile(out_dir, 'current_paper_hybrid_SF_IntH2.png'));
    close(fig1);

    fig2 = figure('Color', 'w', 'Name', 'Axial cap tradeoff');
    tiledlayout(1, 2);
    nexttile;
    bar(categorical(AxialCap.configuration), AxialCap.SFz);
    ylabel('SFz');
    title('Axial shielding');
    grid on;
    nexttile;
    bar(categorical(AxialCap.configuration), AxialCap.IntH2_total);
    ylabel('IntH2 total');
    title('Noise proxy integral');
    grid on;
    saveas(fig2, fullfile(out_dir, 'current_paper_axial_cap_tradeoff.png'));
    close(fig2);
catch ME
    warning('Figure export skipped: %s', ME.message);
end

fprintf('\nCurrent paper logic analysis completed.\n');
fprintf('Output folder: %s\n', out_dir);
disp(RequiredResults);

%% Local functions
function Row = make_noise_row(case_label, material_label, SF, q_ferrite, q_outer, ...
    mupp_ferrite_over_mu0, mupp_outer_over_mu0, f_vec, Temp_K, Nturns, I_A, A_m2, mu0, kB)

    mupp_ferrite = mupp_ferrite_over_mu0 * mu0;
    mupp_outer = 0;
    if isfinite(mupp_outer_over_mu0)
        mupp_outer = mupp_outer_over_mu0 * mu0;
    end
    q_weighted = mupp_ferrite*q_ferrite + mupp_outer*q_outer;
    B_fT = calc_deltaB_fT(f_vec, Temp_K, Nturns, I_A, A_m2, q_weighted, kB);

    Row = table(case_label, material_label, SF, q_ferrite, q_outer, ...
        q_ferrite + q_outer, mupp_ferrite_over_mu0, mupp_outer_over_mu0, ...
        B_fT(1), mean(B_fT), max(B_fT), ...
        'VariableNames', {'case_label','non_ferrite_material','SF','IntH2_ferrite', ...
        'IntH2_non_ferrite','IntH2_total','mu_pp_ferrite_over_mu0', ...
        'mu_pp_non_ferrite_over_mu0','B_1Hz_fT','B_avg_1_30Hz_fT','B_max_1_30Hz_fT'});
end

function B_fT = calc_deltaB_fT(f_vec, Temp_K, Nturns, I_A, A_m2, q_weighted_mu, kB)
    omega = 2*pi*f_vec;
    P_hyst = pi .* f_vec .* q_weighted_mu;
    B_T = sqrt(8*kB*Temp_K .* P_hyst) ./ (A_m2*Nturns*I_A .* omega);
    B_fT = B_T * 1e15;
end

function T = make_loss_sweep(case_label, q_ferrite, q_outer, q_reference, loss_ratio_vec)
    q_weighted_ratio = (q_ferrite + loss_ratio_vec .* q_outer) ./ q_reference;
    noise_amp_ratio = sqrt(q_weighted_ratio);
    T = table(repmat(case_label, numel(loss_ratio_vec), 1), loss_ratio_vec, ...
        repmat(q_ferrite, numel(loss_ratio_vec), 1), ...
        repmat(q_outer, numel(loss_ratio_vec), 1), ...
        q_weighted_ratio, noise_amp_ratio, ...
        'VariableNames', {'case_label','mu_pp_non_ferrite_over_ferrite', ...
        'IntH2_ferrite','IntH2_non_ferrite','weighted_IntH2_ratio_vs_reference', ...
        'noise_amp_ratio_vs_reference'});
end
