%% analyze_for_paper.m
% Paper-oriented analysis for multilayer ferrite shielding.
% Adds: c5 F-test, eta-gamma similarity analysis, SF trade-off prep.
%
% Input:  ../analysis_ready/all_results_clean.csv
% Output: ../analysis_ready/matlab_B_results/paper_*.csv, paper_*.png

clear; clc; close all;

%% User parameters
input_csv = fullfile('..', 'analysis_ready', 'all_results_layerwise.csv');
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

ag_layers = unique(T.layer(T.experiment == "agmatrix"));
    for layer = ag_layers.'
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

ag_layers = unique(T.layer(T.experiment == "agmatrix"));
    for layer = ag_layers.'
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
%  PART 6: Shielding Factor analysis
% ========================================================================
fprintf('\n=== PART 6: Shielding Factor (SF) analysis ===\n');

% --- Analytical B0: single-turn torus coil at center ---
% Coil: Torus1, MajorRadius=5mm, MinorRadius=0.5mm, Iexc=1mA
% For a thin circular loop: B_center = mu0 * I / (2 * R)
R_coil_m  = 5e-3;    % major radius [m]
I_coil_A  = 1e-3;    % excitation current [A]
B0_center_T = mu0 * I_coil_A / (2 * R_coil_m);
fprintf('Coil: MajorRadius=%.1f mm, Iexc=%.1f mA\n', R_coil_m*1e3, I_coil_A*1e3);
fprintf('Analytical B0 at center (thin-loop approx): %.4e T = %.1f nT\n', ...
    B0_center_T, B0_center_T*1e9);

% Note: Actual torus has finite cross-section (MinorRadius=0.5mm).
% The thin-loop formula is accurate to ~1% for r_minor << R_major.
% More precise: B0 = mu0*I/(2*pi*R) * K(k) where K is complete elliptic integral.
% But r_minor/R_major = 0.1, correction < 0.5%.

names = string(T.Properties.VariableNames);
has_Bc = ismember('Bcenter_T', names);

if has_Bc
    fprintf('--> Bcenter_T found! Computing SF from Maxwell data...\n');
    T.B0_T = B0_center_T * ones(height(T), 1);  % analytical B0 for all rows
    T.Bcenter = T.Bcenter_T;  % from Maxwell
    T.SF = abs(T.B0_T) ./ abs(T.Bcenter_T);
    T.ResidualRatio = 1 ./ T.SF;

    fprintf('SF range: [%.2f, %.2f]\n', min(T.SF), max(T.SF));
    fprintf('Typical SF values:\n');

    % SF summary by layer
    all_layers_sf = unique(T.layer); for layer = all_layers_sf.'
        idx = T.layer == layer & isfinite(T.SF);
        if any(idx)
            fprintf('  N=%d: SF = [%.1f, %.1f], median=%.1f\n', ...
                layer, min(T.SF(idx)), max(T.SF(idx)), median(T.SF(idx)));
        end
    end

    % --- SF vs B_noise scatter ---
    fig_sf = figure('Color', 'w', 'Position', [100 100 900 500]);
    subplot(1,2,1);
    hold on; grid on;
    layers_all = unique(T.layer);
    markers_all = {'o','s','^','d'};
    for i = 1:numel(layers_all)
        idx = T.layer == layers_all(i) & isfinite(T.SF);
        if any(idx)
            sub = T(idx, :);
            scatter(sub.B_avg_1_30_fT, sub.SF, 50, markers_all{i}, ...
                'DisplayName', sprintf('N=%d', layers_all(i)));
        end
    end
    xlabel('B_{avg,1-30Hz} (fT/\surdHz)');
    ylabel('SF = B_0 / B_{center}');
    title('Shielding Factor vs Magnetic Noise');
    legend('Location', 'best');
    set(gca, 'XScale', 'log');

    subplot(1,2,2);
    hold on; grid on;
    for i = 1:numel(layers_all)
        idx = T.layer == layers_all(i) & isfinite(T.SF);
        if any(idx)
            sub = T(idx, :);
            scatter(sub.SF, sub.B_avg_1_30_fT, 50, markers_all{i}, ...
                'DisplayName', sprintf('N=%d', layers_all(i)));
        end
    end
    xlabel('SF = B_0 / B_{center}');
    ylabel('B_{avg,1-30Hz} (fT/\surdHz)');
    title('Magnetic Noise vs Shielding Factor');
    legend('Location', 'best');
    set(gca, 'YScale', 'log');

    saveas(fig_sf, fullfile(out_dir, 'paper_SF_vs_Bavg.png'));

    % --- SF vs eta ---
    fig_sf2 = figure('Color', 'w', 'Position', [100 100 600 500]);
    hold on; grid on;
    for i = 1:numel(layers_all)
        idx = T.layer == layers_all(i) & isfinite(T.SF);
        if any(idx)
            sub = T(idx, :);
            scatter(sub.eta, sub.SF, 50, markers_all{i}, ...
                'DisplayName', sprintf('N=%d', layers_all(i)));
        end
    end
    xlabel('\eta = N\cdota / T  (iron fill fraction)');
    ylabel('SF = B_0 / B_{center}');
    title('Shielding Factor vs Iron Fill Fraction');
    legend('Location', 'best');
    saveas(fig_sf2, fullfile(out_dir, 'paper_SF_vs_eta.png'));

    % --- Pareto-optimal points (low B, high SF) ---
    fprintf('\n--- Pareto front candidates (low B_noise AND high SF) ---\n');
    % Normalize both to [0,1] and compute weighted score
    idx_valid = isfinite(T.SF) & isfinite(T.B_avg_1_30_fT);
    if any(idx_valid)
        B_norm = (T.B_avg_1_30_fT(idx_valid) - min(T.B_avg_1_30_fT(idx_valid))) ./ ...
                 (max(T.B_avg_1_30_fT(idx_valid)) - min(T.B_avg_1_30_fT(idx_valid)));
        % For SF, we want HIGH SF, so invert the normalization
        SF_norm = 1 - (T.SF(idx_valid) - min(T.SF(idx_valid))) ./ ...
                     (max(T.SF(idx_valid)) - min(T.SF(idx_valid)));
        score = 0.5*B_norm + 0.5*SF_norm;  % equal weight
        sub_valid = T(idx_valid, :);
        sub_valid.ParetoScore = score;
        sub_valid = sortrows(sub_valid, 'ParetoScore', 'ascend');
        fprintf('Top 5 by Pareto score (50%% B_noise, 50%% SF):\n');
        fprintf('%-6s %-6s %-8s %-8s %-8s %-12s %-10s\n', ...
            'N', 'Exp', 'a(mm)', 'g(mm)', 'T(mm)', 'B_avg', 'SF');
        for j = 1:min(5, height(sub_valid))
            fprintf('%-6d %-6s %-8.3f %-8.3f %-8.3f %-12.4f %-10.1f\n', ...
                sub_valid.layer(j), sub_valid.experiment(j), ...
                sub_valid.a_mm(j), sub_valid.g_eff_mm(j), ...
                sub_valid.T_mm(j), sub_valid.B_avg_1_30_fT(j), sub_valid.SF(j));
        end

        % Write Pareto table
        writetable(sub_valid(:, {'experiment','layer','T_mm','a_mm','g_mm','eta','gamma', ...
            'B_avg_1_30_fT','SF','ParetoScore'}), ...
            fullfile(out_dir, 'paper_pareto_front.csv'));
    end
else
    fprintf('--> Bcenter_T NOT found in data.\n');
    fprintf('    Analytical B0 = %.4e T (%.1f nT) can be used once Bcenter is exported.\n', ...
        B0_center_T, B0_center_T*1e9);
    fprintf('\n');
    fprintf('    To export Bcenter from Maxwell:\n');
    fprintf('    1. Fields -> Calculator, create: Mag_B at (0,0,0), named "Bcenter_T"\n');
    fprintf('    2. Add "Bcenter_T" to Optimetrics export table\n');
    fprintf('    3. Re-export, add Bcenter_T column to all_results_clean.csv\n');
    fprintf('    4. Re-run this script.\n');
end

% Also estimate theoretical SF for reference
fprintf('\n--- Theoretical SF estimate (single-layer cylindrical shell) ---\n');
% Approximate shielding factor for a cylindrical shell with mu_r >> 1:
% SF_axial ~ 1 + mu_r * t / (2 * R)
% Using typical ferrite mu_r ~ 2000 at DC (static simulation)
mu_r_est = 2000;
for t_mm = [2.0, 5.0, 10.0]
    SF_est = 1 + mu_r_est * t_mm / (2 * Rin_mm);
    fprintf('  t=%.0f mm, mu_r=%.0f: SF ~ %.0f\n', t_mm, mu_r_est, SF_est);
end
fprintf('  (These are order-of-magnitude estimates; Maxwell values will differ.)\n');

%% ========================================================================
%  PART 7: Layer-wise IntH2 contribution analysis
% ========================================================================
fprintf('\n=== PART 7: Layer-wise IntH2 contribution ===\n');

max_layers = 8;
layer_cols_available = false(1, max_layers);
layer_names = cell(1, max_layers);
ratio_names = cell(1, max_layers);
for j = 1:max_layers
    layer_names{j} = sprintf('IntH2_L%d', j);
    ratio_names{j} = sprintf('Qratio_L%d', j);
    layer_cols_available(j) = ismember(layer_names{j}, names);
end

fprintf('Layer-wise IntH2 available: ');
for j = 1:max_layers
    fprintf('L%d=%d ', j, layer_cols_available(j));
end
fprintf('\n');

if any(layer_cols_available)
    fprintf('--> Computing layer contributions...\n');

    for j = 1:max_layers
        if layer_cols_available(j)
            col = layer_names{j};
            den = T.IntH2_total;
            valid = isfinite(den) & isfinite(T.(col)) & abs(den) > 1e-40;
            ratio = nan(height(T), 1);
            ratio(valid) = T.(col)(valid) ./ den(valid);
            T.(ratio_names{j}) = ratio;
        end
    end

    % Print layer-wise contribution for best agmatrix points
    idx_multi = T.layer >= 2 & T.experiment == "agmatrix";
    all_layers = unique(T.layer(idx_multi));
    for layer = all_layers.'
        idx = idx_multi & T.layer == layer;
        if any(idx)
            sub = T(idx, :);
            [~, best_i] = min(sub.B_avg_1_30_fT);
            row = sub(best_i, :);
            fprintf('\nN=%d, best agmatrix point: a=%.2f, g=%.2f, T=%.2f\n', ...
                layer, row.a_mm, row.g_eff_mm, row.T_mm);
            fprintf('  B_avg = %.4f fT/sqrtHz\n', row.B_avg_1_30_fT);
            for j = 1:min(layer, max_layers)
                if layer_cols_available(j)
                    fprintf('  Layer %d: IntH2=%.4e, contribution=%.1f%%\n', ...
                        j, row.(layer_names{j}), row.(ratio_names{j})*100);
                end
            end
        end
    end

    % Stacked bar plot for all multilayer cases
    idx_tc = (T.experiment == "Tcompare") & T.layer >= 2 & isfinite(T.IntH2_total);
    if any(idx_tc)
        n_avail = sum(layer_cols_available);
        fig_stack = figure('Color', 'w', 'Position', [100 100 max(800, 150*n_avail) 500]);
        sub_tc = sortrows(T(idx_tc, :), {'T_mm','layer'});
        Y = zeros(height(sub_tc), n_avail);
        leg_names = cell(1, n_avail);
        k = 0;
        for j = 1:max_layers
            if layer_cols_available(j)
                k = k + 1;
                Y(:, k) = sub_tc.(ratio_names{j});
                leg_names{k} = sprintf('L%d', j);
            end
        end
        bar(categorical(compose('N%d T%.0f', sub_tc.layer, sub_tc.T_mm)), Y, 'stacked');
        grid on;
        xlabel('Case');
        ylabel('Q ratio (layer contribution to total)');
        title('Layer-wise contribution to IntH2\_total');
        legend(leg_names, 'Location', 'best');
        saveas(fig_stack, fullfile(out_dir, 'paper_layer_contribution_stacked.png'));
    end
else
    fprintf('--> Layer-wise IntH2 NOT found. These expressions are already\n');
    fprintf('    defined in the AEDT files but not included in the export.\n');
    fprintf('    To export layer-wise data from Maxwell:\n');
    fprintf('    In Optimetrics -> View Results, add to output columns:\n');
    fprintf('      2ceng: IntH2_cyl2, IntH2_cyl4\n');
    fprintf('      3ceng: IntH2_s1, IntH2_s2, IntH2_s3\n');
    fprintf('      4ceng: IntH2_s1, IntH2_s2, IntH2_s3, InH2_s4\n');
    fprintf('    Then export CSV and update all_results_clean.csv.\n');
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
