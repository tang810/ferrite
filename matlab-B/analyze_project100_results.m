%% analyze_project100_results.m
% Batch post-process Project100 AEDT Optimetrics results.
% Input:
%   ../analysis_ready/all_results_clean.csv
% Output folder:
%   ../analysis_ready/matlab_B_results

clear; clc; close all;

%% User parameters
input_csv = fullfile('..', 'analysis_ready', 'all_results_clean.csv');
out_dir = fullfile('..', 'analysis_ready', 'matlab_B_results');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

% Frequency range [Hz]
f_vec = (1:30).';

% Physical constants and material parameters.
Temp_K = 300;
kB = 1.380649e-23;
mu0 = 4*pi*1e-7;
mu_pp_over_mu0 = 6.1;
mu_pp = mu_pp_over_mu0 * mu0;

% Qint unit scaling.
% If AEDT Field Calculator exported the volume integral in SI units, use 1.
% If the exported volume integral used mm^3 instead of m^3, use 1e-9.
% Do not auto-guess this unit; change it here if the AEDT export unit changes.
qint_scale = 1;

% Pickup coil / readout parameters from the previous scripts.
Nturns = 1;
I_A = 1e-3;
R_pickup_m = 5e-3;
r_pickup_m = 0.5e-3;
A_pickup_m2 = 4*pi^2*R_pickup_m*r_pickup_m;

% Geometry assumptions used for material volume only.
Rin_mm = 100;

% Set this to the actual ferrite-cylinder height used in Maxwell.
% This affects MaterialVolume_mm3 and Score, not Maxwell-derived Qint itself.
H_mm = 200;

% Score weights: lower Bavg and lower material volume are better.
wB = 0.7;
wV = 0.3;

% Multi-objective score weights used only when formal shielding-factor
% columns exist. Lower magnetic noise, lower material volume, and lower
% residual field ratio are better.
wB_multi = 0.50;
wV_multi = 0.25;
wResidual_multi = 0.25;

% Constraint used for continuous a-g response-surface optimization.
T_max_opt = 10;

%% Read and validate data
T = readtable(input_csv);
required_columns = ["experiment", "layer", "T_mm", "a_mm", "g_mm", "IntH2_total"];
check_required_columns(T, required_columns);

T.experiment = string(T.experiment);
T.Qint = T.IntH2_total * qint_scale;
T.g_eff_mm = T.g_mm;
idx_g_missing_1layer = T.layer == 1 & ~isfinite(T.g_eff_mm);
T.g_eff_mm(idx_g_missing_1layer) = 0;

if any(~isfinite(T.Qint))
    error('Qint contains NaN or Inf.');
end

if any(T.Qint < 0)
    warning('Some Qint values are negative. They will be clipped to zero.');
    T.Qint = max(T.Qint, 0);
end

% Check the experimental geometry relations without overwriting AEDT-exported
% parameters. Downstream fitting and optimization use the original CSV values.
T = check_experiment_geometry_relations(T);

T = compute_optional_qratios(T);
T = compute_optional_center_field_magnitude(T);
T = compute_optional_shielding_factor(T);

%% Calculate B metrics and material volume
n = height(T);
B_1Hz_fT = zeros(n, 1);
B_avg_1_30_fT = zeros(n, 1);
B_max_1_30_fT = zeros(n, 1);
MaterialVolume_mm3 = zeros(n, 1);

for i = 1:n
    B_fT = calc_B_fT_from_Qint(f_vec, Temp_K, Nturns, I_A, ...
        A_pickup_m2, mu_pp, T.Qint(i), kB);

    B_1Hz_fT(i) = B_fT(1);
    B_avg_1_30_fT(i) = mean(B_fT);
    B_max_1_30_fT(i) = max(B_fT);

    MaterialVolume_mm3(i) = calc_layer_volume_mm3( ...
        T.layer(i), Rin_mm, T.a_mm(i), T.g_eff_mm(i), H_mm);
end

T.B_1Hz_fT = B_1Hz_fT;
T.B_avg_1_30_fT = B_avg_1_30_fT;
T.B_max_1_30_fT = B_max_1_30_fT;
T.MaterialVolume_mm3 = MaterialVolume_mm3;

%% Score
% ScoreWithinExperiment compares points only within the same experiment group.
% ScoreGlobal compares all rows together and is the correct score for global
% ranking across experiment types.
T.ScoreWithinExperiment = nan(n, 1);
experiments = unique(T.experiment, 'stable');
for e = 1:numel(experiments)
    idx = T.experiment == experiments(e);
    b_norm = normalize01(T.B_avg_1_30_fT(idx));
    v_norm = normalize01(T.MaterialVolume_mm3(idx));
    T.ScoreWithinExperiment(idx) = wB*b_norm + wV*v_norm;
end
T.ScoreGlobal = wB*normalize01(T.B_avg_1_30_fT) + ...
    wV*normalize01(T.MaterialVolume_mm3);

has_sf_metrics = all(ismember(["SF", "ResidualRatio"], string(T.Properties.VariableNames)));
if has_sf_metrics
    % Multi-objective score for formal external-field data:
    % noise down, material volume down, residual field ratio down.
    T.ScoreMultiObjective = wB_multi*normalize01(T.B_avg_1_30_fT) + ...
        wV_multi*normalize01(T.MaterialVolume_mm3) + ...
        wResidual_multi*normalize01(T.ResidualRatio);
end

%% Best rows
% BestByExperimentLayer is based on minimum B_avg_1_30_fT.
best_rows = false(n, 1);
for e = 1:numel(experiments)
    exp_name = experiments(e);
    layers = unique(T.layer(T.experiment == exp_name)).';
    for layer = layers
        idx = T.experiment == exp_name & T.layer == layer;
        local = find(idx);
        [~, j] = min(T.B_avg_1_30_fT(local));
        best_rows(local(j)) = true;
    end
end
BestByExperimentLayer = T(best_rows, :);

[~, idx_best_B] = min(T.B_avg_1_30_fT);
OverallBestByB = T(idx_best_B, :);

[~, idx_best_score] = min(T.ScoreGlobal);
OverallBestByScore = T(idx_best_score, :);

if has_sf_metrics
    [~, idx_best_multi] = min(T.ScoreMultiObjective);
    OverallBestByMultiObjective = T(idx_best_multi, :);
else
    OverallBestByMultiObjective = table();
end

%% Agmatrix quadratic response surfaces and constrained optima
AgCoefTable = fit_ag_quadratic_models(T);
AgOptTable = optimize_ag_response_surface(T, AgCoefTable, T_max_opt);
ValidationPoints = write_validation_points(AgOptTable);

%% Write CSV outputs
writetable(T, fullfile(out_dir, 'project100_Bmetrics_all.csv'));
writetable(BestByExperimentLayer, fullfile(out_dir, 'project100_best_by_experiment_layer.csv'));
writetable(OverallBestByB, fullfile(out_dir, 'project100_overall_best_by_B.csv'));
writetable(OverallBestByScore, fullfile(out_dir, 'project100_overall_best_by_score.csv'));
if has_sf_metrics
    writetable(OverallBestByMultiObjective, ...
        fullfile(out_dir, 'project100_overall_best_multiobjective.csv'));
end
writetable(AgCoefTable, fullfile(out_dir, 'project100_agmatrix_quadratic_coefficients.csv'));
writetable(AgOptTable, fullfile(out_dir, 'project100_agmatrix_optimized_candidates.csv'));
writetable(ValidationPoints, fullfile(out_dir, 'project100_maxwell_validation_points.csv'));

%% Console summaries
disp('===== Best by experiment/layer, sorted by B_avg =====');
BestSorted = sortrows(BestByExperimentLayer, 'B_avg_1_30_fT', 'ascend');
disp(BestSorted(:, {'experiment','layer','T_mm','a_mm','g_mm','Qint', ...
    'B_avg_1_30_fT','B_1Hz_fT','MaterialVolume_mm3','ScoreWithinExperiment','ScoreGlobal'}));

disp('===== Overall best by B_avg =====');
disp(OverallBestByB(:, {'experiment','layer','T_mm','a_mm','g_mm','Qint', ...
    'B_avg_1_30_fT','B_1Hz_fT','MaterialVolume_mm3','ScoreWithinExperiment','ScoreGlobal'}));

disp('===== Overall best by Score =====');
disp(OverallBestByScore(:, {'experiment','layer','T_mm','a_mm','g_mm','Qint', ...
    'B_avg_1_30_fT','B_1Hz_fT','MaterialVolume_mm3','ScoreWithinExperiment','ScoreGlobal'}));

if has_sf_metrics
    disp('===== Overall best by multi-objective score =====');
    disp(OverallBestByMultiObjective(:, {'experiment','layer','T_mm','a_mm','g_mm','Qint', ...
        'B_avg_1_30_fT','MaterialVolume_mm3','SF','ResidualRatio','ScoreMultiObjective'}));
end

%% Plots
plot_layer_compare(T, fullfile(out_dir, 'project100_layer_compare_Bavg.png'));
plot_metric_vs_x(T, "asweep", "a_mm", 'a (mm)', ...
    fullfile(out_dir, 'project100_asweep_Bavg.png'));
plot_metric_vs_x(T, "Tcompare", "T_mm", 'T (mm)', ...
    fullfile(out_dir, 'project100_Tcompare_Bavg.png'));

for layer = [2 3 4]
    idx = T.experiment == "agmatrix" & T.layer == layer;
    if any(idx)
        plot_ag_heatmap(T(idx, :), layer, ...
            fullfile(out_dir, sprintf('project100_agmatrix_heatmap_%dceng.png', layer)));
        plot_ag_response_contour(T(idx, :), AgCoefTable, AgOptTable, layer, ...
            T_max_opt, fullfile(out_dir, sprintf('project100_agmatrix_response_%dceng.png', layer)));
    end
end

plot_layer_qratio_stacked(T, fullfile(out_dir, 'project100_layer_Qratio_stacked.png'));
plot_sf_tradeoff(T, fullfile(out_dir, 'project100_SF_vs_Bavg.png'));
plot_residual_field_components(T, fullfile(out_dir, 'project100_residual_field_components.png'));

fprintf('\n完成。结果已写入：\n%s\n', out_dir);
fprintf('关键输出文件：\n');
fprintf('  project100_Bmetrics_all.csv\n');
fprintf('  project100_best_by_experiment_layer.csv\n');
fprintf('  project100_overall_best_by_B.csv\n');
fprintf('  project100_overall_best_by_score.csv\n');
if has_sf_metrics
    fprintf('  project100_overall_best_multiobjective.csv\n');
    fprintf('  project100_SF_vs_Bavg.png\n');
end
fprintf('  project100_agmatrix_quadratic_coefficients.csv\n');
fprintf('  project100_agmatrix_optimized_candidates.csv\n');
fprintf('  project100_maxwell_validation_points.csv\n');

%% Local functions
function check_required_columns(T, required_columns)
    names = string(T.Properties.VariableNames);
    missing = required_columns(~ismember(required_columns, names));
    if ~isempty(missing)
        error('CSV is missing required columns: %s', strjoin(missing, ', '));
    end
end

function T = compute_optional_qratios(T)
    max_layer_for_optional_export = 10;
    layer_cols = "IntH2_L" + string(1:max_layer_for_optional_export);
    names = string(T.Properties.VariableNames);
    for i = 1:numel(layer_cols)
        col = layer_cols(i);
        if ismember(col, names)
            ratio_name = "Qratio_L" + i;
            den = T.IntH2_total;
            valid = isfinite(den) & abs(den) > eps & isfinite(T.(col));
            ratio = nan(height(T), 1);
            ratio(valid) = T.(col)(valid) ./ den(valid);
            T.(ratio_name) = ratio;
        end
    end
end

function T = compute_optional_center_field_magnitude(T)
    names = string(T.Properties.VariableNames);

    % Formal shielding-factor exports can either provide scalar magnitudes
    % directly as B0_T/Bcenter_T, or provide vector components that are then
    % converted to magnitudes here. Component columns are optional.
    if ~ismember("B0_T", names)
        b0_cols = ["B0_Bx_T", "B0_By_T", "B0_Bz_T"];
        if all(ismember(b0_cols, names))
            T.B0_T = sqrt(T.B0_Bx_T.^2 + T.B0_By_T.^2 + T.B0_Bz_T.^2);
        end
    end

    names = string(T.Properties.VariableNames);
    if ~ismember("Bcenter_T", names)
        bc_cols = ["Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T"];
        if all(ismember(bc_cols, names))
            T.Bcenter_T = sqrt(T.Bcenter_Bx_T.^2 + T.Bcenter_By_T.^2 + T.Bcenter_Bz_T.^2);
        end
    end
end

function T = compute_optional_shielding_factor(T)
    names = string(T.Properties.VariableNames);
    if all(ismember(["B0_T", "Bcenter_T"], names))
        B0_abs = abs(T.B0_T);
        Bc_abs = abs(T.Bcenter_T);

        SF = nan(height(T), 1);
        valid_sf = isfinite(B0_abs) & isfinite(Bc_abs) & Bc_abs > eps;
        SF(valid_sf) = B0_abs(valid_sf) ./ Bc_abs(valid_sf);

        ResidualRatio = nan(height(T), 1);
        valid_rr = isfinite(B0_abs) & isfinite(Bc_abs) & B0_abs > eps;
        ResidualRatio(valid_rr) = Bc_abs(valid_rr) ./ B0_abs(valid_rr);

        T.SF = SF;
        T.ResidualRatio = ResidualRatio;
    end
end

function T = check_experiment_geometry_relations(T)
    tol = 1e-6;
    T.T_calc_mm = T.layer .* T.a_mm + (T.layer - 1) .* T.g_eff_mm;
    T.GeometryMismatch_mm = abs(T.T_mm - T.T_calc_mm);

    idx_multilayer = T.layer > 1;
    idx_bad = idx_multilayer & isfinite(T.GeometryMismatch_mm) & ...
        T.GeometryMismatch_mm > tol;

    if any(idx_bad)
        warning(['Some rows have inconsistent T_mm, a_mm, and g_mm. ', ...
            'Max mismatch = %.6g mm. Original CSV geometry values were kept.'], ...
            max(T.GeometryMismatch_mm(idx_bad)));
    end

    idx_one = T.layer == 1;
    if any(isfinite(T.g_eff_mm(idx_one)) & abs(T.g_eff_mm(idx_one)) > tol)
        warning('Some 1-layer rows have nonzero g_mm. Original CSV geometry values were kept.');
    end

    % Keep a diagnostic expected-a column for fixed-total-thickness experiments.
    T.a_expected_from_T_mm = nan(height(T), 1);
    for i = 1:height(T)
        Nlayer = T.layer(i);
        if T.experiment(i) == "Tcompare" || T.experiment(i) == "layer_compare"
            if Nlayer == 1
                T.a_expected_from_T_mm(i) = T.T_mm(i);
            else
                T.a_expected_from_T_mm(i) = ...
                    (T.T_mm(i) - (Nlayer - 1)*T.g_eff_mm(i)) / Nlayer;
            end
        end
    end
end

function B_fT = calc_B_fT_from_Qint(f_vec, Temp_K, Nturns, I_A, A_m2, mu_pp, Qint, kB)
    omega = 2*pi*f_vec;
    P_hyst = pi .* f_vec .* mu_pp .* Qint;
    B_T = sqrt(8*kB*Temp_K .* P_hyst) ./ (A_m2*Nturns*I_A .* omega);
    B_fT = B_T * 1e15;
end

function V = calc_layer_volume_mm3(Nlayer, Rin_mm, a_mm, g_mm, H_mm)
    V = 0;
    for k = 1:Nlayer
        r_in = Rin_mm + (k-1)*(a_mm + g_mm);
        r_out = r_in + a_mm;
        V = V + pi*H_mm*(r_out^2 - r_in^2);
    end
end

function y = normalize01(x)
    y = nan(size(x));
    finite_idx = isfinite(x);
    if ~any(finite_idx)
        return;
    end
    xmin = min(x(finite_idx));
    xmax = max(x(finite_idx));
    if abs(xmax - xmin) < eps
        y(finite_idx) = 0;
    else
        y(finite_idx) = (x(finite_idx) - xmin) ./ (xmax - xmin);
    end
end

function plot_metric_vs_x(T, experiment_name, xfield, xlabel_text, out_png)
    idx_exp = T.experiment == experiment_name;
    if ~any(idx_exp)
        return;
    end

    fig = figure('Color', 'w', 'Name', char(experiment_name));
    hold on; grid on;
    layers = unique(T.layer(idx_exp)).';
    for layer = layers
        idx = idx_exp & T.layer == layer;
        sub = sortrows(T(idx, :), char(xfield));
        plot(sub.(xfield), sub.B_avg_1_30_fT, 'o-', ...
            'LineWidth', 1.8, 'MarkerSize', 7, ...
            'DisplayName', sprintf('%d-layer', layer));
    end
    xlabel(xlabel_text);
    ylabel('B_{avg,1-30Hz} (fT/sqrt(Hz))');
    title(sprintf('%s: B_{avg,1-30Hz}', experiment_name), 'Interpreter', 'none');
    legend('Location', 'best');
    hold off;
    saveas(fig, out_png);
end

function plot_layer_compare(T, out_png)
    idx = T.experiment == "Tcompare" | T.experiment == "layer_compare";
    if ~any(idx)
        return;
    end

    sub_all = T(idx, :);
    T_values = unique(sub_all.T_mm).';
    fig = figure('Color', 'w', 'Name', 'layer comparison');
    hold on; grid on;
    for T_mm = T_values
        sub = sortrows(sub_all(abs(sub_all.T_mm - T_mm) < 1e-9, :), 'layer');
        plot(sub.layer, sub.B_avg_1_30_fT, 'o-', ...
            'LineWidth', 1.8, 'MarkerSize', 7, ...
            'DisplayName', sprintf('T = %.4g mm', T_mm));
    end
    xlabel('Layer number');
    ylabel('B_{avg,1-30Hz} (fT/sqrt(Hz))');
    title('Layer comparison under fixed total thickness');
    xticks(unique(sub_all.layer));
    legend('Location', 'best');
    hold off;
    saveas(fig, out_png);
end

function CoefTable = fit_ag_quadratic_models(T)
    layers_out = [];
    coefs_out = [];
    R2_out = [];
    n_out = [];
    rank_out = [];
    cond_out = [];

    for layer = [2 3 4]
        idx = T.experiment == "agmatrix" & T.layer == layer;
        if ~any(idx)
            continue;
        end
        sub = T(idx, :);
        a = sub.a_mm;
        g = sub.g_mm;
        B = sub.B_avg_1_30_fT;
        valid = isfinite(a) & isfinite(g) & isfinite(B);
        a = a(valid);
        g = g(valid);
        B = B(valid);

        if numel(B) < 6
            warning('Layer %d has fewer than 6 valid agmatrix points. Skip fitting.', layer);
            continue;
        end

        X = [ones(size(a)), a, g, a.^2, g.^2, a.*g];
        rankX = rank(X);
        condX = cond(X);

        if rankX < 6
            warning('Layer %d has rank-deficient agmatrix data. Skip fitting.', layer);
            continue;
        end

        if condX > 1e8
            warning('Layer %d design matrix is ill-conditioned. c5 may be unreliable. condX = %.4e', ...
                layer, condX);
        end

        coef = X \ B;
        B_pred = X * coef;
        SSE = sum((B - B_pred).^2);
        SST = sum((B - mean(B)).^2);
        if abs(SST) < eps
            R2 = NaN;
        else
            R2 = 1 - SSE/SST;
        end

        layers_out = [layers_out; layer]; %#ok<AGROW>
        coefs_out = [coefs_out; coef.']; %#ok<AGROW>
        R2_out = [R2_out; R2]; %#ok<AGROW>
        n_out = [n_out; numel(B)]; %#ok<AGROW>
        rank_out = [rank_out; rankX]; %#ok<AGROW>
        cond_out = [cond_out; condX]; %#ok<AGROW>
    end

    if isempty(layers_out)
        CoefTable = table([], [], [], [], [], [], [], [], [], [], [], ...
            'VariableNames', {'layer','c0','c1','c2','c3','c4','c5','R2','num_points','rankX','condX'});
        return;
    end

    CoefTable = table(layers_out, coefs_out(:,1), coefs_out(:,2), coefs_out(:,3), ...
        coefs_out(:,4), coefs_out(:,5), coefs_out(:,6), R2_out, n_out, rank_out, cond_out, ...
        'VariableNames', {'layer','c0','c1','c2','c3','c4','c5','R2','num_points','rankX','condX'});
end

function OptTable = optimize_ag_response_surface(T, CoefTable, T_max_opt)
    layer_out = [];
    a_out = [];
    g_out = [];
    T_out = [];
    B_out = [];
    c5_out = [];
    R2_out = [];
    method_out = strings(0, 1);

    for i = 1:height(CoefTable)
        layer = CoefTable.layer(i);
        sub = T(T.experiment == "agmatrix" & T.layer == layer, :);
        if isempty(sub)
            continue;
        end

        coef = [CoefTable.c0(i), CoefTable.c1(i), CoefTable.c2(i), ...
            CoefTable.c3(i), CoefTable.c4(i), CoefTable.c5(i)];

        a_min = min(sub.a_mm);
        a_max = max(sub.a_mm);
        g_min = min(sub.g_mm);
        g_max = max(sub.g_mm);
        obj = @(x) eval_ag_quadratic(coef, x(1), x(2));

        method = "dense_grid";
        x_best = [];
        B_best = [];

        if exist('fmincon', 'file') == 2
            try
                x0 = [mean([a_min, a_max]), mean([g_min, g_max])];
                A = [layer, layer-1];
                b = T_max_opt;
                lb = [a_min, g_min];
                ub = [a_max, g_max];
                opts = optimoptions('fmincon', 'Display', 'off');
                [x_best, B_best] = fmincon(obj, x0, A, b, [], [], lb, ub, [], opts);
                method = "fmincon";
            catch
                x_best = [];
                B_best = [];
                method = "dense_grid";
            end
        end

        [x_grid, B_grid] = dense_grid_ag_opt(coef, layer, a_min, a_max, g_min, g_max, T_max_opt);
        if isempty(x_best) || B_grid < B_best
            x_best = x_grid;
            B_best = B_grid;
            if method == "fmincon"
                method = "dense_grid_checked";
            else
                method = "dense_grid";
            end
        end

        T_opt = layer*x_best(1) + (layer-1)*x_best(2);
        if B_best <= 0
            warning(['Layer %d fitted optimum gives non-positive B_pred_fT = %.6g. ', ...
                'The response surface may be unreliable.'], layer, B_best);
        end

        layer_out = [layer_out; layer]; %#ok<AGROW>
        a_out = [a_out; x_best(1)]; %#ok<AGROW>
        g_out = [g_out; x_best(2)]; %#ok<AGROW>
        T_out = [T_out; T_opt]; %#ok<AGROW>
        B_out = [B_out; B_best]; %#ok<AGROW>
        c5_out = [c5_out; CoefTable.c5(i)]; %#ok<AGROW>
        R2_out = [R2_out; CoefTable.R2(i)]; %#ok<AGROW>
        method_out = [method_out; method]; %#ok<AGROW>
    end

    if isempty(layer_out)
        OptTable = table([], [], [], [], [], [], [], strings(0,1), ...
            'VariableNames', {'layer','a_opt_mm','g_opt_mm','T_opt_mm', ...
            'B_pred_fT','c5','R2','method'});
    else
        OptTable = table(layer_out, a_out, g_out, T_out, B_out, c5_out, R2_out, method_out, ...
            'VariableNames', {'layer','a_opt_mm','g_opt_mm','T_opt_mm', ...
            'B_pred_fT','c5','R2','method'});
    end
end

function [x_best, B_best] = dense_grid_ag_opt(coef, layer, a_min, a_max, g_min, g_max, T_max_opt)
    a_vec = linspace(a_min, a_max, 300);
    g_vec = linspace(g_min, g_max, 300);
    [G, A] = meshgrid(g_vec, a_vec);
    T_total = layer*A + (layer-1)*G;
    B = eval_ag_quadratic(coef, A, G);
    B(T_total > T_max_opt) = NaN;
    [B_best, idx] = min(B(:), [], 'omitnan');
    if isnan(B_best)
        error('No feasible grid point found for layer %d with T_max_opt = %.4g mm.', layer, T_max_opt);
    end
    x_best = [A(idx), G(idx)];
end

function B = eval_ag_quadratic(coef, a, g)
    B = coef(1) + coef(2).*a + coef(3).*g + coef(4).*a.^2 + ...
        coef(5).*g.^2 + coef(6).*a.*g;
end

function ValidationPoints = write_validation_points(OptTable)
    if isempty(OptTable)
        ValidationPoints = table(strings(0,1), [], [], [], [], [], strings(0,1), ...
            'VariableNames', {'purpose','layer','a_mm','g_mm','T_mm','B_pred_fT','source'});
        return;
    end
    purpose = repmat("response_surface_optimum", height(OptTable), 1);
    source = repmat("quadratic_response_surface", height(OptTable), 1);
    ValidationPoints = table(purpose, OptTable.layer, OptTable.a_opt_mm, ...
        OptTable.g_opt_mm, OptTable.T_opt_mm, OptTable.B_pred_fT, source, ...
        'VariableNames', {'purpose','layer','a_mm','g_mm','T_mm','B_pred_fT','source'});
end

function plot_ag_heatmap(sub, layer, out_png)
    a_vals = unique(sub.a_mm);
    g_vals = unique(sub.g_mm);
    regular_grid = numel(a_vals)*numel(g_vals) == height(sub);

    fig = figure('Color', 'w', 'Name', sprintf('agmatrix heatmap %dceng', layer));
    if regular_grid
        Z = nan(numel(a_vals), numel(g_vals));
        for i = 1:height(sub)
            ia = find(abs(a_vals - sub.a_mm(i)) < 1e-9, 1);
            ig = find(abs(g_vals - sub.g_mm(i)) < 1e-9, 1);
            Z(ia, ig) = sub.B_avg_1_30_fT(i);
        end
        imagesc(g_vals, a_vals, Z);
        set(gca, 'YDir', 'normal');
    else
        gq = linspace(min(sub.g_mm), max(sub.g_mm), 120);
        aq = linspace(min(sub.a_mm), max(sub.a_mm), 120);
        [Gq, Aq] = meshgrid(gq, aq);
        Zq = griddata(sub.g_mm, sub.a_mm, sub.B_avg_1_30_fT, Gq, Aq, 'natural');
        imagesc(gq, aq, Zq);
        set(gca, 'YDir', 'normal');
        hold on;
        plot(sub.g_mm, sub.a_mm, 'ko', 'MarkerFaceColor', 'w', 'MarkerSize', 5);
        hold off;
    end
    xlabel('g (mm)');
    ylabel('a (mm)');
    title(sprintf('P\\_agmatrix %d-layer heatmap: B_{avg,1-30Hz}', layer));
    cb = colorbar;
    cb.Label.String = 'B_{avg} (fT/sqrt(Hz))';
    saveas(fig, out_png);
end

function plot_ag_response_contour(sub, CoefTable, OptTable, layer, T_max_opt, out_png)
    row = CoefTable(CoefTable.layer == layer, :);
    if isempty(row)
        return;
    end
    coef = [row.c0, row.c1, row.c2, row.c3, row.c4, row.c5];
    gq = linspace(min(sub.g_mm), max(sub.g_mm), 160);
    aq = linspace(min(sub.a_mm), max(sub.a_mm), 160);
    [Gq, Aq] = meshgrid(gq, aq);
    Zq = eval_ag_quadratic(coef, Aq, Gq);
    feasible = layer*Aq + (layer - 1)*Gq <= T_max_opt;
    Zq(~feasible) = NaN;

    fig = figure('Color', 'w', 'Name', sprintf('agmatrix response %dceng', layer));
    contourf(Gq, Aq, Zq, 20, 'LineStyle', 'none');
    hold on;
    plot(sub.g_mm, sub.a_mm, 'ko', 'MarkerFaceColor', 'w', 'MarkerSize', 6, ...
        'DisplayName', 'Maxwell points');

    aq_boundary = linspace(min(sub.a_mm), max(sub.a_mm), 200);
    if layer > 1
        g_boundary = (T_max_opt - layer*aq_boundary) ./ (layer - 1);
        keep = g_boundary >= min(sub.g_mm) & g_boundary <= max(sub.g_mm);
        if any(keep)
            plot(g_boundary(keep), aq_boundary(keep), 'w--', 'LineWidth', 1.8, ...
                'DisplayName', sprintf('T <= %.4g mm', T_max_opt));
        end
    end

    opt = OptTable(OptTable.layer == layer, :);
    if ~isempty(opt)
        plot(opt.g_opt_mm, opt.a_opt_mm, 'rp', 'MarkerFaceColor', 'r', ...
            'MarkerSize', 14, 'DisplayName', 'Fitted optimum');
    end
    hold off;
    xlabel('g (mm)');
    ylabel('a (mm)');
    title(sprintf('P\\_agmatrix %d-layer quadratic response surface', layer));
    cb = colorbar;
    cb.Label.String = 'Predicted B_{avg} (fT/sqrt(Hz))';
    legend('Location', 'best');
    saveas(fig, out_png);
end

function plot_layer_qratio_stacked(T, out_png)
    ratio_cols = string(T.Properties.VariableNames);
    ratio_cols = ratio_cols(startsWith(ratio_cols, "Qratio_L"));
    if isempty(ratio_cols)
        return;
    end

    idx = T.experiment == "Tcompare" | T.experiment == "layer_compare";
    if ~any(idx)
        return;
    end

    sub = sortrows(T(idx, :), {'T_mm','layer'});
    Y = zeros(height(sub), numel(ratio_cols));
    for i = 1:numel(ratio_cols)
        Y(:, i) = sub.(ratio_cols(i));
    end

    fig = figure('Color', 'w', 'Name', 'layer Q ratio stacked');
    bar(categorical(compose('T%.4g-L%d', sub.T_mm, sub.layer)), Y, 'stacked');
    grid on;
    xlabel('T-layer case');
    ylabel('Q ratio');
    title('Layer-wise Qint ratio');
    legend(ratio_cols, 'Location', 'best');
    saveas(fig, out_png);
end

function plot_sf_tradeoff(T, out_png)
    names = string(T.Properties.VariableNames);
    if ~all(ismember(["SF", "ResidualRatio"], names))
        return;
    end

    valid = isfinite(T.SF) & isfinite(T.B_avg_1_30_fT);
    if ~any(valid)
        return;
    end

    fig = figure('Color', 'w', 'Name', 'SF vs Bavg tradeoff');
    hold on; grid on;
    experiments = unique(T.experiment(valid), 'stable');
    for e = 1:numel(experiments)
        idx = valid & T.experiment == experiments(e);
        scatter(T.SF(idx), T.B_avg_1_30_fT(idx), 70, T.layer(idx), ...
            'filled', 'DisplayName', char(experiments(e)));
    end
    xlabel('Shielding factor SF = |B0| / |Bcenter|');
    ylabel('B_{avg,1-30Hz} (fT/sqrt(Hz))');
    title('Shielding-noise tradeoff');
    cb = colorbar;
    cb.Label.String = 'Layer number';
    legend('Location', 'best');
    hold off;
    saveas(fig, out_png);
end

function plot_residual_field_components(T, out_png)
    names = string(T.Properties.VariableNames);
    component_cols = ["Bcenter_Bx_T", "Bcenter_By_T", "Bcenter_Bz_T"];
    if ~all(ismember(component_cols, names))
        return;
    end

    valid = isfinite(T.Bcenter_Bx_T) & isfinite(T.Bcenter_By_T) & isfinite(T.Bcenter_Bz_T);
    if ~any(valid)
        return;
    end

    sub = T(valid, :);
    fig = figure('Color', 'w', 'Name', 'residual field components');
    tiledlayout(3, 1);

    nexttile;
    scatter(sub.layer, sub.Bcenter_Bx_T, 55, 'filled');
    grid on;
    ylabel('Bx (T)');
    title('Center residual field components');

    nexttile;
    scatter(sub.layer, sub.Bcenter_By_T, 55, 'filled');
    grid on;
    ylabel('By (T)');

    nexttile;
    scatter(sub.layer, sub.Bcenter_Bz_T, 55, 'filled');
    grid on;
    xlabel('Layer number');
    ylabel('Bz (T)');

    saveas(fig, out_png);
end
