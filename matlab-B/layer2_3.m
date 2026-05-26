%% compare_2layer_3layer_balance.m
% 功能：
% 1) 读取二层壳、三层壳的 Qint CSV
% 2) 计算 B(1Hz)、B_avg(1~30Hz)、B_max(1~30Hz)
% 3) 计算材料体积和最小间隙
% 4) 过滤不可制造设计点
% 5) 给出性能-材料平衡下的综合最优点
%
% 说明：
% - 二层壳 CSV：第一列为 t[mm]，第二列为 IntH2_total
% - 三层壳 CSV：第一列为 a[mm]，第二列为 IntH2_intotal
% - 所有函数定义均放在文件末尾

clear; clc; close all;

%% =========================
% 1. 用户参数区
% =========================

% 输入文件
csv_2layer = 'csv_2layer.csv';
csv_3layer = 'csv_3layer.csv';

% 主性能指标：
% 'Bavg' / 'B1Hz' / 'Bmax'
main_metric = 'Bavg';

% 综合评分权重
% Score = wB * 性能归一化 + wV * 材料体积归一化
wB = 0.7;
wV = 0.3;

% 工艺约束：最小间隙下限 [mm]
g_min_req_mm = 0.5;

% 频率范围 [Hz]
f_vec = (1:30).';

% 物理参数
T = 300;                  % [K]
N = 1;                    % 匝数
I = 1e-3;                 % [A]
R = 5e-3;                 % pickup torus 主半径 [m]
r = 0.5e-3;               % pickup torus 截面半径 [m]
mu_pp_over_mu0 = 6.1;     % mu''/mu0

% 壳体高度 [mm]
H_mm = 400;

% 输出文件前缀
file_prefix = 'balance_compare_2layer_3layer';

%% =========================
% 2. 固定常数
% =========================
kB  = 1.380649e-23;
mu0 = 4*pi*1e-7;
A_pickup = calc_torus_surface_area(R, r);
mu_pp = mu_pp_over_mu0 * mu0;

%% =========================
% 3. 读取二层壳数据
% =========================
T2_raw = readtable(csv_2layer);

t2_mm = T2_raw{:,1};
Q2 = T2_raw{:,2};

t2_mm = t2_mm(:);
Q2 = Q2(:);

% 排序
[t2_mm, idx2] = sort(t2_mm);
Q2 = Q2(idx2);

% 二层壳：
% 内层 200~200+t，外层 205-t~205
% 总材料截面积 = 810*t
% 总体积 = pi * H * 810*t
V2_mm3 = pi * H_mm .* (810 .* t2_mm);

% 二层壳最小间隙
gap2_mm = 5 - 2 .* t2_mm;

[B2_1Hz, B2_avg, B2_max] = calc_B_metrics_from_Qint(Q2, f_vec, T, N, I, A_pickup, mu_pp, kB);

Design2 = table( ...
    repmat("2-layer", numel(t2_mm), 1), ...
    t2_mm, ...
    Q2, ...
    V2_mm3, ...
    gap2_mm, ...
    B2_1Hz, ...
    B2_avg, ...
    B2_max, ...
    'VariableNames', { ...
    'DesignType', ...
    'DesignVar_mm', ...
    'Qint', ...
    'MaterialVolume_mm3', ...
    'MinGap_mm', ...
    'B_1Hz_fT', ...
    'B_avg_1_30_fT', ...
    'B_max_1_30_fT'});

%% =========================
% 4. 读取三层壳数据
% =========================
T3_raw = readtable(csv_3layer);

a3_mm = T3_raw{:,1};
Q3 = T3_raw{:,2};

a3_mm = a3_mm(:);
Q3 = Q3(:);

% 排序
[a3_mm, idx3] = sort(a3_mm);
Q3 = Q3(idx3);

% 三层壳：
% g = (5 - 3a)/2
% 三层总材料截面积 = 1215*a
% 总体积 = pi * H * 1215*a
V3_mm3 = pi * H_mm .* (1215 .* a3_mm);

% 三层壳最小间隙
gap3_mm = (5 - 3 .* a3_mm) ./ 2;

[B3_1Hz, B3_avg, B3_max] = calc_B_metrics_from_Qint(Q3, f_vec, T, N, I, A_pickup, mu_pp, kB);

Design3 = table( ...
    repmat("3-layer", numel(a3_mm), 1), ...
    a3_mm, ...
    Q3, ...
    V3_mm3, ...
    gap3_mm, ...
    B3_1Hz, ...
    B3_avg, ...
    B3_max, ...
    'VariableNames', { ...
    'DesignType', ...
    'DesignVar_mm', ...
    'Qint', ...
    'MaterialVolume_mm3', ...
    'MinGap_mm', ...
    'B_1Hz_fT', ...
    'B_avg_1_30_fT', ...
    'B_max_1_30_fT'});

%% =========================
% 5. 合并候选集
% =========================
AllDesigns = [Design2; Design3];

% 工艺可行性过滤
is_feasible = AllDesigns.MinGap_mm >= g_min_req_mm;
FeasibleDesigns = AllDesigns(is_feasible, :);

if isempty(FeasibleDesigns)
    error('没有满足最小间隙约束的设计点，请降低 g_min_req_mm 或检查输入数据。');
end

%% =========================
% 6. 选择主性能指标
% =========================
switch lower(main_metric)
    case 'bavg'
        Perf = FeasibleDesigns.B_avg_1_30_fT;
        perf_name = 'B_{avg,1-30Hz}';
    case 'b1hz'
        Perf = FeasibleDesigns.B_1Hz_fT;
        perf_name = 'B_{1Hz}';
    case 'bmax'
        Perf = FeasibleDesigns.B_max_1_30_fT;
        perf_name = 'B_{max,1-30Hz}';
    otherwise
        error('未知 main_metric，请使用 Bavg / B1Hz / Bmax');
end

MatVol = FeasibleDesigns.MaterialVolume_mm3;

%% =========================
% 7. 归一化综合评分
% =========================
Perf_norm = normalize_to_01(Perf);
Mat_norm  = normalize_to_01(MatVol);

Score = wB .* Perf_norm + wV .* Mat_norm;
FeasibleDesigns.Score = Score;

[best_score, idx_best] = min(Score);
BestDesign = FeasibleDesigns(idx_best, :);

%% =========================
% 8. Pareto 前沿
% =========================
is_pareto = get_pareto_front(MatVol, Perf);
ParetoDesigns = FeasibleDesigns(is_pareto, :);

%% =========================
% 9. 输出结果
% =========================
disp('===== 所有可行设计点 =====');
disp(FeasibleDesigns);

disp('===== Pareto 前沿设计点 =====');
disp(ParetoDesigns);

disp('===== 综合最优设计点 =====');
disp(BestDesign);

fprintf('\n===== 综合最优摘要 =====\n');
fprintf('主性能指标          = %s\n', perf_name);
fprintf('性能权重 wB         = %.2f\n', wB);
fprintf('材料权重 wV         = %.2f\n', wV);
fprintf('最小间隙约束        = %.2f mm\n', g_min_req_mm);
fprintf('最优结构类型        = %s\n', BestDesign.DesignType{1});
fprintf('最优设计变量        = %.6f mm\n', BestDesign.DesignVar_mm);
fprintf('Qint                = %.12e\n', BestDesign.Qint);
fprintf('材料体积            = %.6f mm^3\n', BestDesign.MaterialVolume_mm3);
fprintf('最小间隙            = %.6f mm\n', BestDesign.MinGap_mm);
fprintf('B(1Hz)              = %.6f fT/sqrt(Hz)\n', BestDesign.B_1Hz_fT);
fprintf('B_avg(1~30Hz)       = %.6f fT/sqrt(Hz)\n', BestDesign.B_avg_1_30_fT);
fprintf('B_max(1~30Hz)       = %.6f fT/sqrt(Hz)\n', BestDesign.B_max_1_30_fT);
fprintf('综合评分            = %.6f\n', best_score);

%% =========================
% 10. 画图：Pareto 图
% =========================
fig1 = figure('Color', 'w', 'Name', 'Pareto tradeoff');
hold on; grid on;

idx2_plot = FeasibleDesigns.DesignType == "2-layer";
idx3_plot = FeasibleDesigns.DesignType == "3-layer";

plot(FeasibleDesigns.MaterialVolume_mm3(idx2_plot), Perf(idx2_plot), ...
    'o', 'LineWidth', 1.8, 'MarkerSize', 8);
plot(FeasibleDesigns.MaterialVolume_mm3(idx3_plot), Perf(idx3_plot), ...
    's', 'LineWidth', 1.8, 'MarkerSize', 8);

plot(ParetoDesigns.MaterialVolume_mm3, ...
     get_perf_from_table(ParetoDesigns, main_metric), ...
     'd-', 'LineWidth', 1.8, 'MarkerSize', 8);

plot(BestDesign.MaterialVolume_mm3, ...
     get_perf_from_table(BestDesign, main_metric), ...
     'p', 'LineWidth', 2.2, 'MarkerSize', 14);

xlabel('Material volume (mm^3)', 'FontSize', 13);
ylabel([perf_name, ' (fT/\surdHz)'], 'FontSize', 13);
title('Pareto tradeoff: performance vs material', 'FontSize', 15);
legend('2-layer feasible', '3-layer feasible', 'Pareto front', 'Chosen best', ...
    'Location', 'best');
hold off;

%% =========================
% 11. 画图：综合评分
% =========================
fig2 = figure('Color', 'w', 'Name', 'Score comparison');
bar(categorical(strcat(FeasibleDesigns.DesignType, "_", string(FeasibleDesigns.DesignVar_mm))), Score);
grid on;
xlabel('Candidate design', 'FontSize', 12);
ylabel('Weighted score', 'FontSize', 12);
title('Weighted score comparison', 'FontSize', 15);
xtickangle(45);

%% =========================
% 12. 导出
% =========================
writetable(FeasibleDesigns, [file_prefix, '_feasible.csv']);
writetable(ParetoDesigns, [file_prefix, '_pareto.csv']);
writetable(BestDesign, [file_prefix, '_best.csv']);

saveas(fig1, [file_prefix, '_pareto.png']);
saveas(fig2, [file_prefix, '_score.png']);

fprintf('\n已导出结果文件。\n');

%% =========================
% 函数定义区
% =========================

function A = calc_torus_surface_area(R, r)
    A = 4*pi^2*R*r;
end

function [B1, Bavg, Bmax] = calc_B_metrics_from_Qint(Qint_vec, f_vec, T, N, I, A, mu_pp, kB)
    num_case = numel(Qint_vec);
    B1   = zeros(num_case,1);
    Bavg = zeros(num_case,1);
    Bmax = zeros(num_case,1);

    for i = 1:num_case
        omega = 2*pi*f_vec;
        P_hyst = pi .* f_vec .* mu_pp .* Qint_vec(i);
        deltaB = sqrt(8*kB*T .* P_hyst) ./ (A*N*I .* omega);
        deltaB_fT = deltaB * 1e15;

        B1(i)   = deltaB_fT(1);
        Bavg(i) = mean(deltaB_fT);
        Bmax(i) = max(deltaB_fT);
    end
end

function x_norm = normalize_to_01(x)
    x = x(:);
    xmin = min(x);
    xmax = max(x);
    if abs(xmax - xmin) < 1e-15
        x_norm = zeros(size(x));
    else
        x_norm = (x - xmin) ./ (xmax - xmin);
    end
end

function is_pareto = get_pareto_front(x_cost, y_perf)
    n = numel(x_cost);
    is_pareto = true(n,1);
    for i = 1:n
        for j = 1:n
            if j ~= i
                if (x_cost(j) <= x_cost(i)) && (y_perf(j) <= y_perf(i)) && ...
                   ((x_cost(j) < x_cost(i)) || (y_perf(j) < y_perf(i)))
                    is_pareto(i) = false;
                    break;
                end
            end
        end
    end
end

function perf = get_perf_from_table(TB, main_metric)
    switch lower(main_metric)
        case 'bavg'
            perf = TB.B_avg_1_30_fT;
        case 'b1hz'
            perf = TB.B_1Hz_fT;
        case 'bmax'
            perf = TB.B_max_1_30_fT;
        otherwise
            error('未知 main_metric');
    end
end