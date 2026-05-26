%% calc_deltaB_and_inverse_mu.m
% 功能：
% 1) 计算 1~30 Hz 下的磁化噪声幅值谱密度 deltaB_magn
% 2) 计算 1~30 Hz 下 deltaB_magn 的平均值
% 3) 根据目标平均值反求所需的 mu''/mu0 和 mu''
% 4) 面积固定采用 A = 4*pi^2*R*r
% 5) 导出图像、逐频点结果表、汇总表
%
% 说明：
% 本脚本假设来自 Ansys 的 Qint = \int H^2 dV 已知，
% 并采用：
%   P_hyst = pi*f*mu_pp*Qint
%   deltaB = sqrt(8*kB*T*P_hyst) / (A*N*I*omega)
%
% 注意：
% 脚本中的所有函数定义均放在文件末尾。

clear; clc; close all;

%% =========================
% 1. 用户可修改参数区
% =========================

% 频率范围 [Hz]
f_vec = (1:30).';

% 温度 [K]
T = 300;

% 线圈参数
N = 1;                  % 匝数
I = 1e-3;               % 电流幅值 [A]
R = 5e-3;               % 主半径 [m]，例如 5 mm
r = 0.5e-3;             % 截面半径 [m]，例如 0.5 mm

% 材料参数（当前值）
mu_pp_over_mu0 = 6.1;   % 当前 mu''/mu0

% 来自 Ansys 的积分结果
Qint = 3.45825559217975E-18;  % Qint = \int H^2 dV

% 目标平均值 [fT/sqrt(Hz)]，用于反求 mu''
B_avg_target_fT = 1.0;

% 输出文件名前缀
file_prefix = 'deltaB_1to30Hz_with_inverse_mu';

%% =========================
% 2. 固定常数区（写死）
% =========================
kB  = 1.380649e-23;     % 玻尔兹曼常数 [J/K]
mu0 = 4*pi*1e-7;        % 真空磁导率 [H/m]

%% =========================
% 3. 参数预处理
% =========================
A = calc_torus_surface_area(R, r);   % A = 4*pi^2*R*r
mu_pp = mu_pp_over_mu0 * mu0;        % 绝对虚部磁导率 mu'' [H/m]

%% =========================
% 4. 主计算：1~30 Hz 下的 deltaB
% =========================
[B_T, P_hyst, omega] = calc_deltaB_from_Qint(f_vec, T, N, I, A, mu_pp, Qint, kB);
B_fT = B_T * 1e15;   % 转成 fT/sqrt(Hz)

% 平均值、最大值、最小值
B_avg_T  = mean(B_T);
B_avg_fT = mean(B_fT);

[B_max_fT, idx_max] = max(B_fT);
[B_min_fT, idx_min] = min(B_fT);

%% =========================
% 5. 反求满足目标平均值所需的 mu''
% =========================
[mu_pp_over_mu0_required, mu_pp_required] = inverse_mu_pp_from_target( ...
    mu_pp_over_mu0, B_avg_fT, B_avg_target_fT, mu0);

% 用反求出来的 mu'' 再计算一次，作为校核
[B_T_required, P_hyst_required, omega_required] = calc_deltaB_from_Qint( ...
    f_vec, T, N, I, A, mu_pp_required, Qint, kB);

B_fT_required = B_T_required * 1e15;
B_avg_required_fT = mean(B_fT_required);

%% =========================
% 6. 生成逐频点结果表
% =========================
ResultTable = table( ...
    f_vec, ...
    omega, ...
    repmat(A, numel(f_vec), 1), ...
    repmat(mu_pp, numel(f_vec), 1), ...
    repmat(Qint, numel(f_vec), 1), ...
    P_hyst, ...
    B_T, ...
    B_fT, ...
    B_T_required, ...
    B_fT_required, ...
    'VariableNames', { ...
    'f_Hz', ...
    'omega_rad_per_s', ...
    'A_m2', ...
    'mu_pp_current_H_per_m', ...
    'Qint', ...
    'P_hyst_current_W', ...
    'deltaB_current_T_per_sqrtHz', ...
    'deltaB_current_fT_per_sqrtHz', ...
    'deltaB_required_T_per_sqrtHz', ...
    'deltaB_required_fT_per_sqrtHz'});

%% =========================
% 7. 生成汇总表
% =========================
SummaryTable = table( ...
    T, ...
    N, ...
    I, ...
    R, ...
    r, ...
    A, ...
    Qint, ...
    mu_pp_over_mu0, ...
    mu_pp, ...
    B_avg_T, ...
    B_avg_fT, ...
    B_avg_target_fT, ...
    mu_pp_over_mu0_required, ...
    mu_pp_required, ...
    B_avg_required_fT, ...
    B_max_fT, ...
    f_vec(idx_max), ...
    B_min_fT, ...
    f_vec(idx_min), ...
    'VariableNames', { ...
    'T_K', ...
    'N', ...
    'I_A', ...
    'R_m', ...
    'r_m', ...
    'A_m2', ...
    'Qint', ...
    'mu_pp_over_mu0_current', ...
    'mu_pp_current_H_per_m', ...
    'B_avg_current_T_per_sqrtHz', ...
    'B_avg_current_fT_per_sqrtHz', ...
    'B_avg_target_fT_per_sqrtHz', ...
    'mu_pp_over_mu0_required', ...
    'mu_pp_required_H_per_m', ...
    'B_avg_check_fT_per_sqrtHz', ...
    'B_max_current_fT_per_sqrtHz', ...
    'f_at_B_max_Hz', ...
    'B_min_current_fT_per_sqrtHz', ...
    'f_at_B_min_Hz'});

%% =========================
% 8. 命令行显示
% =========================
disp('===== 1~30 Hz 逐频点计算结果 =====');
disp(ResultTable);

disp('===== 汇总结果 =====');
disp(SummaryTable);

fprintf('\n===== 关键结果 =====\n');
fprintf('面积 A = 4*pi^2*R*r         = %.12e m^2\n', A);
fprintf('当前 mu''''/mu0             = %.12f\n', mu_pp_over_mu0);
fprintf('当前 mu''''                 = %.12e H/m\n', mu_pp);
fprintf('Qint = int(H^2 dV)          = %.12e\n', Qint);
fprintf('当前 1~30 Hz 平均值         = %.12e T/sqrt(Hz)\n', B_avg_T);
fprintf('当前 1~30 Hz 平均值         = %.6f fT/sqrt(Hz)\n', B_avg_fT);
fprintf('目标平均值                  = %.6f fT/sqrt(Hz)\n', B_avg_target_fT);
fprintf('反求所需 mu''''/mu0         = %.12f\n', mu_pp_over_mu0_required);
fprintf('反求所需 mu''''             = %.12e H/m\n', mu_pp_required);
fprintf('反求后平均值校核            = %.6f fT/sqrt(Hz)\n', B_avg_required_fT);
fprintf('当前最大值                  = %.6f fT/sqrt(Hz) @ %d Hz\n', B_max_fT, f_vec(idx_max));
fprintf('当前最小值                  = %.6f fT/sqrt(Hz) @ %d Hz\n', B_min_fT, f_vec(idx_min));

%% =========================
% 9. 绘图
% =========================
fig = figure('Color', 'w', 'Name', 'deltaB magn from 1 to 30 Hz');

plot(f_vec, B_fT, 'o-', 'LineWidth', 1.8, 'MarkerSize', 7);
grid on;
hold on;

% 当前平均值
yline(B_avg_fT, '--r', 'LineWidth', 1.5, ...
    'Label', sprintf('Current Mean = %.4f fT/\\surdHz', B_avg_fT), ...
    'LabelHorizontalAlignment', 'left', ...
    'LabelVerticalAlignment', 'bottom');

% 目标平均值
yline(B_avg_target_fT, '--k', 'LineWidth', 1.5, ...
    'Label', sprintf('Target Mean = %.4f fT/\\surdHz', B_avg_target_fT), ...
    'LabelHorizontalAlignment', 'left', ...
    'LabelVerticalAlignment', 'top');

xlabel('Frequency (Hz)', 'FontSize', 14);
ylabel('\delta B_{magn} (fT/\surdHz)', 'FontSize', 14);
title('\delta B_{magn} from 1 to 30 Hz', 'FontSize', 16);

legend('Current \deltaB_{magn}', 'Location', 'northeast');
hold off;

%% =========================
% 10. 导出文件
% =========================

% 10.1 Excel
xlsx_name = [file_prefix, '_results.xlsx'];
try
    writetable(ResultTable, xlsx_name, 'Sheet', 'B_1to30Hz');
    writetable(SummaryTable, xlsx_name, 'Sheet', 'Summary');
    fprintf('已导出 Excel 文件：%s\n', xlsx_name);
catch ME
    warning('Excel 导出失败：%s', ME.message);
end

% 10.2 CSV
csv_result_name  = [file_prefix, '_B_1to30Hz.csv'];
csv_summary_name = [file_prefix, '_Summary.csv'];
writetable(ResultTable, csv_result_name);
writetable(SummaryTable, csv_summary_name);
fprintf('已导出 CSV 文件：%s\n', csv_result_name);
fprintf('已导出 CSV 文件：%s\n', csv_summary_name);

% 10.3 PNG
png_name = [file_prefix, '_plot.png'];
saveas(fig, png_name);
fprintf('已导出图片文件：%s\n', png_name);

%% =========================
% 函数定义区
% =========================

function A = calc_torus_surface_area(R, r)
    % 环面表面积
    % A = 4*pi^2*R*r
    A = 4*pi^2*R*r;
end

function [deltaB, P_hyst, omega] = calc_deltaB_from_Qint(f_vec, T, N, I, A, mu_pp, Qint, kB)
    % 根据 Qint = \int H^2 dV 计算：
    % P_hyst = pi*f*mu_pp*Qint
    % deltaB = sqrt(8*kB*T*P_hyst) / (A*N*I*omega)

    omega = 2*pi*f_vec;
    P_hyst = pi .* f_vec .* mu_pp .* Qint;
    deltaB = sqrt(8*kB*T .* P_hyst) ./ (A*N*I .* omega);
end

function [mu_pp_over_mu0_required, mu_pp_required] = inverse_mu_pp_from_target(mu_pp_over_mu0_current, B_avg_current_fT, B_avg_target_fT, mu0)
    % 反求满足目标平均值所需的 mu''/mu0 和 mu''
    %
    % 由于 deltaB ∝ sqrt(mu'')，
    % 所以平均值也满足 B_avg ∝ sqrt(mu'')
    % 因而：
    % mu_pp_new = mu_pp_old * (B_target / B_old)^2

    mu_pp_over_mu0_required = mu_pp_over_mu0_current * (B_avg_target_fT / B_avg_current_fT)^2;
    mu_pp_required = mu_pp_over_mu0_required * mu0;
end