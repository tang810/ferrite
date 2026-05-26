%% optimize_t_from_Qint_csv.m
% 功能：
% 1) 读取 Ansys 导出的 t-Qint CSV
% 2) 计算每个 t 对应的 deltaB(1 Hz)、1~30 Hz 平均值、1~30 Hz 最大值
% 3) 自动找出最优 t
% 4) 导出结果表和图
%
% 说明：
% 当前模型假设：
%   P_hyst = pi*f*mu_pp*Qint
%   deltaB = sqrt(8*kB*T*P_hyst) / (A*N*I*omega)
%
% 当前建议：
%   objective_mode = 'f1'
% 也可选：
%   'avg_1_30'
%   'max_1_30'
%
% 注意：
% 脚本中的函数定义均放在文件末尾。

clear; clc; close all;

%% =========================
% 1. 用户参数区
% =========================

% 输入 CSV 文件名（Ansys 导出的 t-Qint 表）
csv_file = 't_Qint_total.csv';

% 优化目标：
% 'f1'       -> 最小化 1 Hz 下的 B
% 'avg_1_30' -> 最小化 1~30 Hz 平均值
% 'max_1_30' -> 最小化 1~30 Hz 最大值
objective_mode = 'f1';

% 频率范围 [Hz]
f_vec = (1:30).';

% 温度 [K]
T = 300;

% 线圈参数
N = 1;                  % 匝数
I = 1e-3;               % 电流幅值 [A]
R = 5e-3;               % 主半径 [m]
r = 0.5e-3;             % 截面半径 [m]

% 材料参数
mu_pp_over_mu0 = 6.1;   % mu''/mu0

% 输出文件前缀
file_prefix = 'optimize_t_result';

%% =========================
% 2. 固定常数区
% =========================
kB  = 1.380649e-23;     % 玻尔兹曼常数 [J/K]
mu0 = 4*pi*1e-7;        % 真空磁导率 [H/m]

%% =========================
% 3. 读取 CSV
% =========================
rawTable = readtable(csv_file);

% 兼容不同表头写法：直接取前两列
t_mm  = rawTable{:,1};
Qint  = rawTable{:,2};

% 转列向量
t_mm = t_mm(:);
Qint = Qint(:);

% 按 t 从小到大排序
[t_mm, sortIdx] = sort(t_mm);
Qint = Qint(sortIdx);

%% =========================
% 4. 参数预处理
% =========================
A = calc_torus_surface_area(R, r);
mu_pp = mu_pp_over_mu0 * mu0;

num_t = numel(t_mm);
num_f = numel(f_vec);

B_T_all   = zeros(num_t, num_f);
B_fT_all  = zeros(num_t, num_f);
P_hyst_all = zeros(num_t, num_f);

B_1Hz_fT      = zeros(num_t, 1);
B_avg_1_30_fT = zeros(num_t, 1);
B_max_1_30_fT = zeros(num_t, 1);

%% =========================
% 5. 对每个 t 计算 B(f)
% =========================
for i = 1:num_t
    [B_T, P_hyst, ~] = calc_deltaB_from_Qint(f_vec, T, N, I, A, mu_pp, Qint(i), kB);
    B_fT = B_T * 1e15;

    B_T_all(i, :)    = B_T.';
    B_fT_all(i, :)   = B_fT.';
    P_hyst_all(i, :) = P_hyst.';

    % 1 Hz 对应第一项
    B_1Hz_fT(i) = B_fT(1);

    % 1~30 Hz 平均值
    B_avg_1_30_fT(i) = mean(B_fT);

    % 1~30 Hz 最大值
    B_max_1_30_fT(i) = max(B_fT);
end

%% =========================
% 6. 找最优解
% =========================
switch lower(objective_mode)
    case 'f1'
        objective_value = B_1Hz_fT;
        objective_name = 'B at 1 Hz (fT/sqrtHz)';
    case 'avg_1_30'
        objective_value = B_avg_1_30_fT;
        objective_name = 'Average B from 1 to 30 Hz (fT/sqrtHz)';
    case 'max_1_30'
        objective_value = B_max_1_30_fT;
        objective_name = 'Maximum B from 1 to 30 Hz (fT/sqrtHz)';
    otherwise
        error('未知 objective_mode：%s', objective_mode);
end

[objective_best, idx_opt] = min(objective_value);

t_opt_mm   = t_mm(idx_opt);
Qint_opt   = Qint(idx_opt);
B1_opt     = B_1Hz_fT(idx_opt);
Bavg_opt   = B_avg_1_30_fT(idx_opt);
Bmax_opt   = B_max_1_30_fT(idx_opt);

%% =========================
% 7. 输出结果表
% =========================
SummaryTable = table( ...
    t_mm, ...
    Qint, ...
    B_1Hz_fT, ...
    B_avg_1_30_fT, ...
    B_max_1_30_fT, ...
    'VariableNames', { ...
    't_mm', ...
    'Qint', ...
    'B_1Hz_fT_per_sqrtHz', ...
    'B_avg_1_30_fT_per_sqrtHz', ...
    'B_max_1_30_fT_per_sqrtHz'});

OptTable = table( ...
    string(objective_mode), ...
    string(objective_name), ...
    t_opt_mm, ...
    Qint_opt, ...
    B1_opt, ...
    Bavg_opt, ...
    Bmax_opt, ...
    'VariableNames', { ...
    'objective_mode', ...
    'objective_name', ...
    't_opt_mm', ...
    'Qint_opt', ...
    'B_1Hz_opt_fT_per_sqrtHz', ...
    'B_avg_1_30_opt_fT_per_sqrtHz', ...
    'B_max_1_30_opt_fT_per_sqrtHz'});

%% =========================
% 8. 命令行显示
% =========================
disp('===== 各 t 对应结果 =====');
disp(SummaryTable);

disp('===== 最优解 =====');
disp(OptTable);

fprintf('\n===== 最优解摘要 =====\n');
fprintf('优化目标                     = %s\n', objective_name);
fprintf('最优 t                       = %.6f mm\n', t_opt_mm);
fprintf('对应 Qint                    = %.12e\n', Qint_opt);
fprintf('对应 B(1 Hz)                 = %.6f fT/sqrt(Hz)\n', B1_opt);
fprintf('对应 B_avg(1~30 Hz)          = %.6f fT/sqrt(Hz)\n', Bavg_opt);
fprintf('对应 B_max(1~30 Hz)          = %.6f fT/sqrt(Hz)\n', Bmax_opt);

%% =========================
% 9. 绘图
% =========================
fig1 = figure('Color', 'w', 'Name', 'Qint vs t');
plot(t_mm, Qint, 'o-', 'LineWidth', 1.8, 'MarkerSize', 7);
grid on;
xlabel('t (mm)', 'FontSize', 13);
ylabel('Qint = \int H^2 dV', 'FontSize', 13);
title('Qint vs t', 'FontSize', 15);

fig2 = figure('Color', 'w', 'Name', 'B metrics vs t');
plot(t_mm, B_1Hz_fT, 'o-', 'LineWidth', 1.8, 'MarkerSize', 7);
hold on;
plot(t_mm, B_avg_1_30_fT, 's-', 'LineWidth', 1.8, 'MarkerSize', 7);
plot(t_mm, B_max_1_30_fT, 'd-', 'LineWidth', 1.8, 'MarkerSize', 7);
grid on;
xlabel('t (mm)', 'FontSize', 13);
ylabel('\delta B (fT/\surdHz)', 'FontSize', 13);
title('B metrics vs t', 'FontSize', 15);
legend('B at 1 Hz', 'B avg from 1 to 30 Hz', 'B max from 1 to 30 Hz', ...
    'Location', 'northeast');
hold off;

%% =========================
% 10. 导出
% =========================
summary_csv = [file_prefix, '_summary.csv'];
opt_csv     = [file_prefix, '_optimal.csv'];
writetable(SummaryTable, summary_csv);
writetable(OptTable, opt_csv);

saveas(fig1, [file_prefix, '_Qint_vs_t.png']);
saveas(fig2, [file_prefix, '_Bmetrics_vs_t.png']);

fprintf('已导出：%s\n', summary_csv);
fprintf('已导出：%s\n', opt_csv);

%% =========================
% 函数定义区
% =========================

function A = calc_torus_surface_area(R, r)
    A = 4*pi^2*R*r;
end

function [deltaB, P_hyst, omega] = calc_deltaB_from_Qint(f_vec, T, N, I, A, mu_pp, Qint, kB)
    omega = 2*pi*f_vec;
    P_hyst = pi .* f_vec .* mu_pp .* Qint;
    deltaB = sqrt(8*kB*T .* P_hyst) ./ (A*N*I .* omega);
end