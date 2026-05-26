%% analyze_for_paper.m
% Paper-oriented analysis for multilayer ferrite shielding.
% Adds: c5 F-test, eta-gamma similarity analysis, SF trade-off prep.
%
% Input:  ../analysis_ready/all_results_clean.csv
% Output: ../analysis_ready/matlab_B_results/paper_*.csv, paper_*.png

clear; clc; close all;

%% User parameters
input_csv = fullfile('..', 'analysis_ready', 'all_results_clean.csv');
out_dir  = fullfile('..', 'analysis_ready', 'matlab_B_results');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

% --- Physical constants (same as analyze_project100_results.m) ---
f_vec    = (1:30).';
Temp_K   = 300;
kB       = 1.380649e-23;
mu0      = 4*pi*1e-7;
mu_pp_over_mu0 = 6.1;
mu_pp    = mu_pp_over_mu0 * mu0;
qint_scale = 1;
Nturns   = 1;
I_A      = 1e-3;
R_pickup_m = 5e-3;
r_pickup_m = 0.5e-3;
A_pickup_m2 = 4*pi^2*R_pickup_m*r_pickup_m;
Rin_mm   = 100;
H_mm     = 200;
T_max_opt = 10;

%% ========================================================================
%  PART 1: Read data and compute B metrics
% ========================================================================
fprintf('=== PART 1: Loading data and computing B metrics ===\n');
T = readtable(input_csv);
T.Qint = T.IntH2_total * qint_scale;

% Handle missing g for 1-layer
T.g_eff_mm = T.g_mm;
idx_g_missing = T.layer == 1 & ~isfinite(T.g_eff_mm);
T.g_eff_mm(idx_g_missing) = 0;

% Compute B metrics
n = height(T);
B_avg_1_30_fT = zeros(n, 1);
B_1Hz_fT     = zeros(n, 1);
MaterialVolume_mm3 = zeros(n, 1);

for i = 1:n
    B_fT = calc_B_fT_from_Qint(f_vec, Temp_K, Nturns, I_A, ...
        A_pickup_m2, mu_pp, T.Qint(i), kB);
    B_1Hz_fT(i)     = B_fT(1);
    B_avg_1_30_fT(i) = mean(B_fT);
    MaterialVolume_mm3(i) = calc_layer_volume_mm3( ...
        T.layer(i), Rin_mm, T.a_mm(i), T.g_eff_mm(i), H_mm);
end

T.B_avg_1_30_fT = B_avg_1_30_fT;
T.B_1Hz_fT     = B_1Hz_fT;
T.MaterialVolume_mm3 = MaterialVolume_mm3;

%% ========================================================================
%  PART 1b: Add dimensionless parameters eta and gamma
% ========================================================================
fprintf('=== Adding dimensionless parameters eta, gamma ===\n');

% eta = Na / T = iron fill fraction
T.eta = T.layer .* T.a_mm ./ T.T_mm;
% For T=0 or missing, use formula: Na / (Na + (N-1)g)
idx_bad_eta = ~isfinite(T.eta) | T.eta <= 0;
T.eta(idx_bad_eta) = T.layer(idx_bad_eta) .* T.a_mm(idx_bad_eta) ./ ...
    (T.layer(idx_bad_eta) .* T.a_mm(idx_bad_eta) + ...
     (T.layer(idx_bad_eta) - 1) .* T.g_eff_mm(idx_bad_eta));

% gamma = g/a = gap-to-thickness ratio
T.gamma = T.g_eff_mm ./ T.a_mm;
T.gamma(T.layer == 1) = 0;  % no gap for single layer

% Total ferrite = N*a
T.total_ferrite_mm = T.layer .* T.a_mm;

fprintf('   eta  range: [%.4f, %.4f]\n', min(T.eta), max(T.eta));
fprintf('   gamma range: [%.4f, %.4f]\n', min(T.gamma), max(T.gamma));

%% ========================================================================
%  PART 2: c5 F-test significance analysis
% ========================================================================
fprintf('\n=== PART 2: c5 F-test for coupling significance ===\n');

fid = fopen(fullfile(out_dir, 'paper_c5_ftest_results.csv'), 'w');
fprintf(fid, 'layer,SSE_full,SSE_reduced,df_full,df_reduced,F_stat,p_value,c5,R2_full,R2_reduced,significant_at_0.05\n');

for layer = [2 3 4]
    idx = T.experiment == "agmatrix" & T.layer == layer;
    if sum(idx) < 7
        fprintf('Layer %d: insufficient data (n=%d)\n', layer, sum(idx));
        continue;
    end
    sub = T(idx, :);
    a = sub.a_mm;
    g = sub.g_mm;
    B = sub.B_avg_1_30_fT;

    % Full model: B = c0 + c1*a + c2*g + c3*a^2 + c4*g^2 + c5*a*g
    X_full = [ones(size(a)), a, g, a.^2, g.^2, a.*g];
    coef_full = X_full \ B;
    B_pred_full = X_full * coef_full;
    SSE_full = sum((B - B_pred_full).^2);
    SST = sum((B - mean(B)).^2);
    R2_full = 1 - SSE_full / SST;

    % Reduced model (no coupling): B = c0 + c1*a + c2*g + c3*a^2 + c4*g^2
    X_reduced = [ones(size(a)), a, g, a.^2, g.^2];
    coef_reduced = X_reduced \ B;
    B_pred_reduced = X_reduced * coef_reduced;
    SSE_reduced = sum((B - B_pred_reduced).^2);
    R2_reduced = 1 - SSE_reduced / SST;

    % F-test: H0: c5 = 0
    n_pts = numel(B);
    df_full    = n_pts - 6;  % 6 parameters in full model
    df_reduced = n_pts - 5;  % 5 parameters in reduced model
    df_diff    = df_reduced - df_full;  % = 1

    F_stat = ((SSE_reduced - SSE_full) / df_diff) / (SSE_full / df_full);
    p_value = 1 - fcdf(F_stat, df_diff, df_full);

    c5 = coef_full(6);
    significant = p_value < 0.05;

    fprintf('Layer %d: F=%.4f, p=%.6f, c5=%.6f, R2_full=%.4f, R2_reduced=%.4f, significant=%d\n', ...
        layer, F_stat, p_value, c5, R2_full, R2_reduced, significant);
    fprintf(fid, '%d,%.6e,%.6e,%d,%d,%.4f,%.6e,%.6f,%.4f,%.4f,%d\n', ...
        layer, SSE_full, SSE_reduced, df_full, df_reduced, F_stat, p_value, ...
        c5, R2_full, R2_reduced, significant);
end
fclose(fid);

% Also output full coefficient table with std errors and t-statistics
fprintf('\n--- Coefficient statistics (full model) ---\n');
fid2 = fopen(fullfile(out_dir, 'paper_coefficient_statistics.csv'), 'w');
fprintf(fid2, 'layer,coefficient,estimate,SE,t_stat,p_value\n');

for layer = [2 3 4]
    idx = T.experiment == "agmatrix" & T.layer == layer;
    if sum(idx) < 7, continue; end
    sub = T(idx, :);
    a = sub.a_mm; g = sub.g_mm; B = sub.B_avg_1_30_fT;
    X = [ones(size(a)), a, g, a.^2, g.^2, a.*g];
    [coef, ~, ~, ~, stats] = regress(B, X);
    % regress in MATLAB stats toolbox gives: R2, F, p, error variance
    % We'll compute SE manually
    n_pts = numel(B);
    resid = B - X * coef;
    sigma2 = sum(resid.^2) / (n_pts - 6);
    XtX_inv = inv(X' * X);
    SE = sqrt(diag(XtX_inv) * sigma2);
    t_stat = coef ./ SE;
    p_vals_coef = 2 * (1 - tcdf(abs(t_stat), n_pts - 6));

    coef_names = {'c0','c1','c2','c3','c4','c5'};
    for j = 1:6
        fprintf(fid2, '%d,%s,%.6f,%.6f,%.4f,%.6f\n', ...
            layer, coef_names{j}, coef(j), SE(j), t_stat(j), p_vals_coef(j));
    end
end
fclose(fid2);
fprintf('Coefficient statistics written to paper_coefficient_statistics.csv\n');

%% ========================================================================
%  PART 3: eta-gamma similarity analysis
% ========================================================================
fprintf('\n=== PART 3: eta-gamma similarity analysis ===\n');

% 3a. Check if eta-gamma can collapse data across layers
%     For agmatrix data, check if B_avg clusters by (eta, gamma) regardless of N
idx_ag = T.experiment == "agmatrix";

% Plot: B_avg vs eta, colored by gamma, different markers for N
fig_eta = figure('Color', 'w', 'Position', [100 100 900 500]);
subplot(1,2,1);
hold on; grid on;
layers_ag = unique(T.layer(idx_ag));
markers = {'o','s','^'};
colors_gamma = lines(20);
for i = 1:numel(layers_ag)
    idx = idx_ag & T.layer == layers_ag(i);
    sub = T(idx, :);
    scatter(sub.eta, sub.B_avg_1_30_fT, 60, sub.gamma, 'filled', ...
        markers{i}, 'DisplayName', sprintf('N=%d', layers_ag(i)));
end
xlabel('\eta = N\cdota / T  (iron fill fraction)');
ylabel('B_{avg,1-30Hz} (fT/\surdHz)');
title('B_{avg} vs \eta');
cb = colorbar; cb.Label.String = '\gamma = g/a';
legend('Location', 'best');

subplot(1,2,2);
hold on; grid on;
for i = 1:numel(layers_ag)
    idx = idx_ag & T.layer == layers_ag(i);
    sub = T(idx, :);
    scatter(sub.gamma, sub.B_avg_1_30_fT, 60, sub.eta, 'filled', ...
        markers{i}, 'DisplayName', sprintf('N=%d', layers_ag(i)));
end
xlabel('\gamma = g/a  (gap-to-thickness ratio)');
ylabel('B_{avg,1-30Hz} (fT/\surdHz)');
title('B_{avg} vs \gamma');
cb2 = colorbar; cb2.Label.String = '\eta';
legend('Location', 'best');

saveas(fig_eta, fullfile(out_dir, 'paper_eta_gamma_Bavg.png'));
fprintf('eta-gamma plot saved.\n');

% 3b. Fit B ~ f(eta, gamma) across ALL layers to test similarity
fprintf('\n--- Cross-layer eta-gamma regression ---\n');
sub_all_ag = T(idx_ag, :);
eta_all = sub_all_ag.eta;
gamma_all = sub_all_ag.gamma;
B_all    = sub_all_ag.B_avg_1_30_fT;

% Model 1: B = c0 + c1*eta + c2*gamma (linear)
X_eg1 = [ones(size(eta_all)), eta_all, gamma_all];
coef_eg1 = X_eg1 \ B_all;
B_pred_eg1 = X_eg1 * coef_eg1;
R2_eg1 = 1 - sum((B_all - B_pred_eg1).^2) / sum((B_all - mean(B_all)).^2);

% Model 2: B = c0 + c1*eta + c2*gamma + c3*eta*gamma
X_eg2 = [ones(size(eta_all)), eta_all, gamma_all, eta_all.*gamma_all];
coef_eg2 = X_eg2 \ B_all;
B_pred_eg2 = X_eg2 * coef_eg2;
R2_eg2 = 1 - sum((B_all - B_pred_eg2).^2) / sum((B_all - mean(B_all)).^2);

% Model 3: B = c0 + c1*eta + c2*gamma + c3/N (add layer count explicitly)
eta_N_all = 1 ./ sub_all_ag.layer;
X_eg3 = [ones(size(eta_all)), eta_all, gamma_all, eta_N_all];
coef_eg3 = X_eg3 \ B_all;
B_pred_eg3 = X_eg3 * coef_eg3;
R2_eg3 = 1 - sum((B_all - B_pred_eg3).^2) / sum((B_all - mean(B_all)).^2);

fprintf('Model 1 (eta + gamma):               R2 = %.4f\n', R2_eg1);
fprintf('Model 2 (eta + gamma + eta*gamma):    R2 = %.4f\n', R2_eg2);
fprintf('Model 3 (eta + gamma + 1/N):          R2 = %.4f\n', R2_eg3);

% If R2_eg1 is already very high (>0.95), eta and gamma alone explain most variance
% Then similarity holds: N only matters through how it changes eta and gamma
fprintf('\n--> If R2 for eta+gamma alone > 0.95, then eta and gamma are\n');
fprintf('    the dominant dimensionless parameters (similarity holds).\n');
fprintf('    If adding 1/N significantly improves R2, layer count has an\n');
fprintf('    independent effect beyond eta and gamma.\n');

% Write eta-gamma regression results
fid_eg = fopen(fullfile(out_dir, 'paper_eta_gamma_regression.csv'), 'w');
fprintf(fid_eg, 'model,R2,coef_c0,coef_eta,coef_gamma,coef_extra\n');
fprintf(fid_eg, 'eta+gamma,%.4f,%.6f,%.6f,%.6f,\n', R2_eg1, coef_eg1);
fprintf(fid_eg, 'eta+gamma+eta*gamma,%.4f,%.6f,%.6f,%.6f,%.6f\n', R2_eg2, coef_eg2);
fprintf(fid_eg, 'eta+gamma+1overN,%.4f,%.6f,%.6f,%.6f,%.6f\n', R2_eg3, coef_eg3);
fclose(fid_eg);

% 3c. Plot: predicted vs actual for best eta-gamma model
fig_pred = figure('Color', 'w', 'Position', [100 100 600 500]);
hold on; grid on;
plot([min(B_all) max(B_all)], [min(B_all) max(B_all)], 'k--', 'LineWidth', 1);
for i = 1:numel(layers_ag)
    idx_l = sub_all_ag.layer == layers_ag(i);
    scatter(B_all(idx_l), B_pred_eg3(idx_l), 50, markers{i}, ...
        'DisplayName', sprintf('N=%d', layers_ag(i)));
end
xlabel('B_{avg} Maxwell (fT/\surdHz)');
ylabel('B_{avg} predicted from \eta,\gamma,1/N');
title(sprintf('Cross-layer similarity model (R^2=%.4f)', R2_eg3));
legend('Location', 'best');
axis equal;
saveas(fig_pred, fullfile(out_dir, 'paper_eta_gamma_predicted_vs_actual.png'));

%% ========================================================================
%  PART 4: Nonlinear penalty analysis
% ========================================================================
fprintf('\n=== PART 4: Nonlinear penalty of reduced iron fill ===\n');

% Quantify: how much does B_avg increase when eta decreases?
% Focus on T=10mm fixed-thickness comparison
idx_T10 = abs(T.T_mm - 10) < 0.01;
sub_T10 = T(idx_T10, :);
sub_T10 = sortrows(sub_T10, 'layer');

fprintf('\nT=10mm fixed total thickness comparison:\n');
fprintf('%-6s %-8s %-8s %-8s %-6s %-12s %-12s\n', ...
    'N', 'a(mm)', 'g(mm)', 'T(mm)', 'eta', 'B_avg', 'Penalty');
if height(sub_T10) >= 2
    B_ref = sub_T10.B_avg_1_30_fT(1);  % reference: 1-layer
    for i = 1:height(sub_T10)
        penalty = (sub_T10.B_avg_1_30_fT(i) - B_ref) / B_ref * 100;
        fprintf('%-6d %-8.3f %-8.3f %-8.3f %-6.4f %-12.4f %-10.1f%%\n', ...
            sub_T10.layer(i), sub_T10.a_mm(i), sub_T10.g_eff_mm(i), ...
            sub_T10.T_mm(i), sub_T10.eta(i), ...
            sub_T10.B_avg_1_30_fT(i), penalty);
    end

    % Fit: log(B_avg) vs log(eta) or eta to check linearity
    eta_T10 = sub_T10.eta;
    B_T10   = sub_T10.B_avg_1_30_fT;

    % Power law: B ~ eta^alpha
    X_log = [ones(size(eta_T10)), log(eta_T10)];
    coef_log = X_log \ log(B_T10);
    alpha_power = coef_log(2);
    fprintf('\nPower law fit: B ~ eta^(%.3f)\n', alpha_power);
    fprintf('Alpha = -1 means penalty is exactly proportional to 1/eta.\n');
    fprintf('Alpha < -1 means penalty is SUPER-linear (worse than proportional).\n');
end

%% ========================================================================
%  PART 5: Output enhanced data with eta, gamma columns
% ========================================================================
T_enhanced = T(:, {'experiment','layer','T_mm','a_mm','g_mm','eta','gamma', ...
    'total_ferrite_mm','IntH2_total','Qint','B_1Hz_fT','B_avg_1_30_fT', ...
    'MaterialVolume_mm3'});
writetable(T_enhanced, fullfile(out_dir, 'paper_enhanced_results.csv'));
fprintf('\nEnhanced results with eta, gamma written to paper_enhanced_results.csv\n');

%% ========================================================================
%  PART 6: SF vs B_noise trade-off prep (placeholder until SF data exists)
% ========================================================================
fprintf('\n=== PART 6: SF trade-off prep ===\n');
fprintf('NOTE: SF (Shielding Factor) data not yet available.\n');
fprintf('When B0_T and Bcenter_T are exported from Maxwell, add them\n');
fprintf('to the input CSV as columns, then re-run this script.\n');
fprintf('The script will compute: SF = abs(B0_T) / abs(Bcenter_T)\n');
fprintf('and generate: B_avg vs SF trade-off plot (Pareto front).\n');

% Check if B0_T and Bcenter_T exist in the data
names = string(T.Properties.VariableNames);
has_B0 = ismember('B0_T', names);
has_Bc = ismember('Bcenter_T', names);
if has_B0 && has_Bc
    fprintf('--> B0_T and Bcenter_T found! Computing SF...\n');
    T.SF = abs(T.B0_T) ./ abs(T.Bcenter_T);
    T.ResidualRatio = abs(T.Bcenter_T) ./ abs(T.B0_T);

    % SF vs B_avg scatter
    fig_sf = figure('Color', 'w', 'Position', [100 100 700 500]);
    hold on; grid on;
    for i = 1:numel(layers_ag)
        idx = T.experiment == "agmatrix" & T.layer == layers_ag(i);
        if any(idx)
            sub = T(idx, :);
            scatter(sub.B_avg_1_30_fT, sub.SF, 50, markers{i}, ...
                'DisplayName', sprintf('N=%d', layers_ag(i)));
        end
    end
    xlabel('B_{avg,1-30Hz} (fT/\surdHz)');
    ylabel('SF = |B_0| / |B_{center}|');
    title('Shielding Factor vs Magnetic Noise (agmatrix data)');
    legend('Location', 'best');
    saveas(fig_sf, fullfile(out_dir, 'paper_SF_vs_Bavg.png'));

    % Pareto front: best points trading off SF and B_noise
    fprintf('SF range: [%.2f, %.2f]\n', min(T.SF), max(T.SF));
else
    fprintf('--> B0_T and Bcenter_T NOT found in data.\n');
    fprintf('    Export these from Maxwell Field Calculator:\n');
    fprintf('    B0_T    = Mag_B at center point (no shield)\n');
    fprintf('    Bcenter_T = Mag_B at center point (with shield)\n');
end

% Check for layer-wise IntH2
has_L1 = ismember('IntH2_L1', names);
has_L2 = ismember('IntH2_L2', names);
has_L3 = ismember('IntH2_L3', names);
has_L4 = ismember('IntH2_L4', names);
fprintf('\nLayer-wise IntH2 available: L1=%d, L2=%d, L3=%d, L4=%d\n', ...
    has_L1, has_L2, has_L3, has_L4);
if has_L1
    fprintf('--> Layer-wise data found! Run layer contribution analysis.\n');
    % Layer contribution stacked bar
    % (implement when data available)
else
    fprintf('--> Layer-wise IntH2 NOT found. Export from Maxwell:\n');
    fprintf('    In Field Calculator, for each ferrite layer object:\n');
    fprintf('    IntH2_L1 = Integral(Volume(ferrite_1), Dot(H,H))\n');
    fprintf('    (Already defined as IntH2_s1, IntH2_s2, etc. in AEDT files)\n');
end

%% ========================================================================
%  Done
% ========================================================================
fprintf('\n========================================\n');
fprintf('Paper analysis complete.\n');
fprintf('Output files in: %s\n', out_dir);
fprintf('  paper_c5_ftest_results.csv\n');
fprintf('  paper_coefficient_statistics.csv\n');
fprintf('  paper_enhanced_results.csv\n');
fprintf('  paper_eta_gamma_regression.csv\n');
fprintf('  paper_eta_gamma_Bavg.png\n');
fprintf('  paper_eta_gamma_predicted_vs_actual.png\n');
fprintf('========================================\n');

%% ========================================================================
%  Local functions (same as analyze_project100_results.m)
% ========================================================================
function B_fT = calc_B_fT_from_Qint(f_vec, Temp_K, Nturns, I_A, A_m2, mu_pp, Qint, kB)
    omega = 2*pi*f_vec;
    P_hyst = pi .* f_vec .* mu_pp .* Qint;
    B_T = sqrt(8*kB*Temp_K .* P_hyst) ./ (A_m2*Nturns*I_A .* omega);
    B_fT = B_T * 1e15;
end

function V = calc_layer_volume_mm3(Nlayer, Rin_mm, a_mm, g_mm, H_mm)
    V = 0;
    for k = 1:Nlayer
        r_in  = Rin_mm + (k-1)*(a_mm + g_mm);
        r_out = r_in + a_mm;
        V = V + pi*H_mm*(r_out^2 - r_in^2);
    end
end
