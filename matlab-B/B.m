%% calc_deltaB_magn_1to30Hz.m
% 功能：
% 1) 计算 1~30 Hz 下的磁化噪声幅值谱密度 deltaB_magn
% 2) 面积固定采用 A = 4*pi^2*R*r
% 3) 输出图像、逐频点表格、平均值表格
% 4) 所有函数定义均放在文件末尾

clear; clc; close all;

%% =========================
% 1. 用户可修改参数区
% =========================

% 频率范围 [Hz]
f_vec = (1:30).';

% 温度 [K]
T = 300;

% 线圈参数
N = 1;              % 匝数
I = 1e-3;           % 电流幅值 [A]
R = 5e-3;           % 主半径 [m]，例如 5 mm
r = 0.5e-3;         % 截面半径 [m]，例如 0.5 mm

% 材料参数
mu_pp_over_mu0 = 6.1;   % mu'' / mu0

% 来自 Ansys 的积分结果
Qint = 5.4464984407578e-18;   % Qint = \int H^2 dV

% 输出文件名前缀
file_prefix = 'deltaB_1to30Hz';

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
% 4. 主计算
% =========================
[B_T, P_hyst, omega] = calc_deltaB_from_Qint(f_vec, T, N, I, A, mu_pp, Qint, kB);
B_fT = B_T * 1e15;   % 转成 fT/sqrt(Hz)

% 平均值
B_avg_T  = mean(B_T);
B_avg_fT = mean(B_fT);

% 最大值、最小值
[B_max_fT, idx_max] = max(B_fT);
[B_min_fT, idx_min] = min(B_fT);

%% =========================
% 5. 生成逐频点结果表
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
    'VariableNames', { ...
    'f_Hz', ...
    'omega_rad_per_s', ...
    'A_m2', ...
    'mu_pp_H_per_m', ...
    'Qint', ...
    'P_hyst_W', ...
    'deltaB_T_per_sqrtHz', ...
    'deltaB_fT_per_sqrtHz'});

%% =========================
% 6. 生成平均值与摘要表
% =========================
SummaryTable = table( ...
    T, ...
    N, ...
    I, ...
    R, ...
    r, ...
    A, ...
    mu_pp_over_mu0, ...
    mu_pp, ...
    Qint, ...
    B_avg_T, ...
    B_avg_fT, ...
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
    'mu_pp_over_mu0', ...
    'mu_pp_H_per_m', ...
    'Qint', ...
    'B_avg_T_per_sqrtHz', ...
    'B_avg_fT_per_sqrtHz', ...
    'B_max_fT_per_sqrtHz', ...
    'f_at_B_max_Hz', ...
    'B_min_fT_per_sqrtHz', ...
    'f_at_B_min_Hz'});

%% =========================
% 7. 命令行显示
% =========================
disp('===== 1~30 Hz 逐频点计算结果 =====');
disp(ResultTable);

disp('===== 平均值与摘要 =====');
disp(SummaryTable);

fprintf('\n===== 关键结果 =====\n');
fprintf('面积 A = 4*pi^2*R*r      = %.12e m^2\n', A);
fprintf('绝对虚部磁导率 mu''''     = %.12e H/m\n', mu_pp);
fprintf('Qint = int(H^2 dV)       = %.12e\n', Qint);
fprintf('1~30 Hz 平均 B 值        = %.12e T/sqrt(Hz)\n', B_avg_T);
fprintf('1~30 Hz 平均 B 值        = %.6f fT/sqrt(Hz)\n', B_avg_fT);
fprintf('最大 B 值                = %.6f fT/sqrt(Hz) @ %d Hz\n', B_max_fT, f_vec(idx_max));
fprintf('最小 B 值                = %.6f fT/sqrt(Hz) @ %d Hz\n', B_min_fT, f_vec(idx_min));

B_avg_current = 1.0741;     % 当前平均值，单位 fT/sqrt(Hz)
mu_pp_over_mu0_current = 6.1;

B_target = 1.0;             % 目标平均值，单位 fT/sqrt(Hz)

mu_pp_over_mu0_required = mu_pp_over_mu0_current * (B_target / B_avg_current)^2;

fprintf('若要使平均值达到 %.4f fT/sqrt(Hz)，则需要 mu''''/mu0 = %.6f\n', ...
    B_target, mu_pp_over_mu0_required);

%% =========================
% 8. 绘图
% =========================
fig = figure('Color', 'w', 'Name', 'deltaB magn from 1 to 30 Hz');
plot(f_vec, B_fT, 'o-', 'LineWidth', 1.8, 'MarkerSize', 7);
grid on;
xlabel('Frequency (Hz)', 'FontSize', 14);
ylabel('\delta B_{magn} (fT/\surdHz)', 'FontSize', 14);
title('\delta B_{magn} from 1 to 30 Hz', 'FontSize', 16);

% 在图中添加平均值参考线
hold on;
yline(B_avg_fT, '--r', 'LineWidth', 1.5, ...
    'Label', sprintf('Mean = %.4f fT/\\surdHz', B_avg_fT), ...
    'LabelHorizontalAlignment', 'left', ...
    'LabelVerticalAlignment', 'bottom');
hold off;

%% =========================
% 9. 导出文件
% =========================

% 9.1 导出 Excel 文件（两个 sheet）
xlsx_name = [file_prefix, '_results.xlsx'];
try
    writetable(ResultTable, xlsx_name, 'Sheet', 'B_1to30Hz');
    writetable(SummaryTable, xlsx_name, 'Sheet', 'Summary');
    fprintf('已导出 Excel 文件：%s\n', xlsx_name);
catch ME
    warning('Excel 导出失败：%s', ME.message);
end

% 9.2 导出 CSV 文件
csv_result_name  = [file_prefix, '_B_1to30Hz.csv'];
csv_summary_name = [file_prefix, '_Summary.csv'];
writetable(ResultTable, csv_result_name);
writetable(SummaryTable, csv_summary_name);
fprintf('已导出 CSV 文件：%s\n', csv_result_name);
fprintf('已导出 CSV 文件：%s\n', csv_summary_name);

% 9.3 导出图片
png_name = [file_prefix, '_plot.png'];
saveas(fig, png_name);
fprintf('已导出图片文件：%s\n', png_name);

%% =========================
% 10. 函数定义区
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