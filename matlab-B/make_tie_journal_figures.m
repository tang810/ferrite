%% make_tie_journal_figures.m
% Rebuild the paper figures in a restrained TIE/TIM journal style.
%
% Inputs are the current Maxwell/MATLAB evidence-chain CSV files.  The
% numerical conclusions are not changed; this script recomputes the plotted
% quantities and exports cleaner paper figures to paper/figures_tie.

clear; clc;

script_dir = fileparts(mfilename('fullpath'));
root_dir = fileparts(script_dir);
data_dir = fullfile(root_dir, 'analysis_ready', 'matlab_B_results');
out_dir = fullfile(root_dir, 'paper', 'figures_tie');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

set_journal_style();

colors.ferrite = [0.18 0.18 0.18];
colors.amorphous = [0.00 0.32 0.62];
colors.nano = [0.70 0.08 0.10];
colors.p0 = [0.10 0.50 0.24];
colors.cap = [0.43 0.27 0.58];
colors.gray = [0.55 0.55 0.55];
colors.lightGray = [0.86 0.86 0.86];

basis = readtable(fullfile(data_dir, 'current_paper_structure_basis.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
hybrid = readtable(fullfile(data_dir, 'current_paper_hybrid_enhancement.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
axial = readtable(fullfile(data_dir, 'current_paper_axial_cap_tradeoff.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
geomag = readtable(fullfile(data_dir, 'current_paper_geomagnetic_residual_estimates.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
loss = readtable(fullfile(data_dir, 'current_paper_material_loss_sensitivity.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
noise = readtable(fullfile(data_dir, 'current_paper_noise_proxy_1to30Hz.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
matrix = readtable(fullfile(root_dir, 'analysis_ready', 'manufacturable_thin_ferrite_sim_matrix.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');

make_fig01_concept(out_dir, colors);
make_fig02_ferrite_base(out_dir, colors, basis);
make_fig03_hybrid(out_dir, colors, hybrid);
make_fig04_axial(out_dir, colors, axial);
make_fig05_geomag(out_dir, colors, geomag);
make_fig06_loss(out_dir, colors, loss);
make_fig07_base_selection_matrix(out_dir, colors, matrix, basis);
make_fig08_sf_intH2_tradeoff_map(out_dir, colors, hybrid, axial);
make_fig09_layerwise_intH2_contribution(out_dir, colors, hybrid, axial);
make_fig10_noise_proxy_1to30Hz(out_dir, colors, noise);
write_manifest(out_dir);

fprintf('Rebuilt TIE-style figures in %s\n', out_dir);

%% Figure builders
function make_fig01_concept(out_dir, c)
    fig = newfig(7.16, 2.35);
    tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');

    ax = nexttile(tl, 1);
    hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
    xlim(ax, [-1.16 1.16]); ylim(ax, [-1.05 1.05]);
    theta = linspace(0, 2*pi, 360);
    radii = [0.55 0.68 0.81 0.94];
    for k = 1:numel(radii)
        plot(ax, radii(k)*cos(theta), radii(k)*sin(theta), '-', ...
            'Color', c.ferrite, 'LineWidth', 1.2);
        plot(ax, (radii(k)-0.055)*cos(theta), (radii(k)-0.055)*sin(theta), '-', ...
            'Color', c.lightGray, 'LineWidth', 0.7);
    end
    plot(ax, 0.38*cos(theta), 0.38*sin(theta), '--', 'Color', c.gray, 'LineWidth', 0.9);
    text(ax, 0, 0, {'sensor', 'volume'}, 'HorizontalAlignment', 'center', 'FontSize', 7);
    annotation_arrow(ax, [0.72 0.50], [0.48 0.82], c.ferrite);
    text(ax, 0.03, 0.88, 'four ferrite sheets', 'FontSize', 7);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on'); axis(ax, 'equal'); axis(ax, 'off');
    xlim(ax, [-1.16 1.16]); ylim(ax, [-1.05 1.05]);
    for k = 1:numel(radii)
        plot(ax, radii(k)*cos(theta), radii(k)*sin(theta), '-', ...
            'Color', c.ferrite, 'LineWidth', 0.9);
    end
    plot(ax, 1.05*cos(theta), 1.05*sin(theta), '-', 'Color', c.nano, 'LineWidth', 2.0);
    quiver(ax, -1.12, 0, 0.26, 0, 0, 'Color', [0 0 0], 'LineWidth', 0.9, 'MaxHeadSize', 0.9);
    text(ax, -1.10, 0.13, 'B_x', 'FontSize', 8);
    text(ax, 0, 0.92, 'outer high-\mu ribbon', 'HorizontalAlignment', 'center', 'FontSize', 7);
    panel_label(ax, '(b)');

    ax = nexttile(tl, 3);
    hold(ax, 'on'); axis(ax, 'off');
    xlim(ax, [0 3.2]); ylim(ax, [-0.95 0.95]);
    rectangle(ax, 'Position', [0.45 -0.48 1.75 0.96], 'EdgeColor', c.ferrite, 'LineWidth', 1.4);
    for x = [0.58 0.71 0.84 0.97]
        plot(ax, [x x], [-0.48 0.48], '-', 'Color', c.gray, 'LineWidth', 0.7);
    end
    rectangle(ax, 'Position', [2.35 -0.58 0.13 1.16], 'FaceColor', c.nano, ...
        'EdgeColor', c.nano, 'LineWidth', 0.8);
    plot(ax, 1.34, 0, 'ko', 'MarkerFaceColor', 'k', 'MarkerSize', 4);
    text(ax, 1.34, -0.20, 'magnetometer', 'HorizontalAlignment', 'center', 'FontSize', 7);
    quiver(ax, 1.34, 0.82, 0, -0.28, 0, 'Color', [0 0 0], 'LineWidth', 0.9, 'MaxHeadSize', 0.8);
    text(ax, 1.44, 0.76, 'B_z', 'FontSize', 8);
    text(ax, 2.42, 0.72, {'single', 'cap'}, 'HorizontalAlignment', 'center', 'FontSize', 7);
    panel_label(ax, '(c)');

    export_fig(fig, out_dir, 'Fig01_concept_hybrid_multilayer_shield');
end

function make_fig02_ferrite_base(out_dir, c, basis)
    fig = newfig(7.16, 2.35);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

    ax = nexttile(tl, 1);
    hold(ax, 'on'); axis(ax, 'off'); axis(ax, 'equal');
    xlim(ax, [0 2.6]); ylim(ax, [-0.1 1.45]);
    Rin = basis.Rin_mm(1);
    t = basis.layer_t_mm(1);
    g = basis.gap_mm(1);
    N = basis.N(1);
    x0 = 0.42;
    scale = 12;
    rectangle(ax, 'Position', [x0 0.22 1.25 0.82], 'EdgeColor', [0 0 0], 'LineWidth', 0.8);
    for k = 1:N
        xpos = x0 + 1.25 + (k-1)*(t+g)*scale/10;
        rectangle(ax, 'Position', [xpos 0.22 t*scale/10 0.82], ...
            'FaceColor', c.ferrite, 'EdgeColor', c.ferrite, 'LineWidth', 0.8);
    end
    plot(ax, [x0 x0+1.25], [1.15 1.15], 'k-', 'LineWidth', 0.8);
    text(ax, x0+0.62, 1.26, sprintf('R_{in} = %.0f mm', Rin), ...
        'HorizontalAlignment', 'center', 'FontSize', 8);
    text(ax, 1.95, 0.56, sprintf('N = %d, t = %.2f mm, g = %.2f mm', N, t, g), ...
        'HorizontalAlignment', 'center', 'FontSize', 8);
    text(ax, 1.95, 0.36, sprintf('radial space = %.2f mm', basis.radial_Tspace_mm(1)), ...
        'HorizontalAlignment', 'center', 'FontSize', 8);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    yyaxis(ax, 'left');
    plot(ax, 1, basis.SFx(1), 'o', 'Color', c.ferrite, 'MarkerFaceColor', c.ferrite, ...
        'MarkerSize', 5.5, 'LineWidth', 1.2);
    ylabel(ax, 'SF_x');
    ylim(ax, [0 max(4.5, basis.SFx(1)*1.25)]);
    ax.YAxis(1).Color = [0 0 0];
    yyaxis(ax, 'right');
    semilogy(ax, 1, basis.IntH2_total(1), 's', 'Color', c.gray, ...
        'MarkerFaceColor', c.gray, 'MarkerSize', 5.5, 'LineWidth', 1.2);
    set(ax, 'YScale', 'log');
    ylabel(ax, 'IntH2 total');
    ax.YAxis(2).Color = c.gray;
    xlim(ax, [0.65 1.35]);
    set(ax, 'XTick', 1, 'XTickLabel', {'4-layer base'});
    grid(ax, 'on');
    text(ax, 1.05, basis.IntH2_total(1)*1.3, sprintf('%.2e', basis.IntH2_total(1)), ...
        'FontSize', 7, 'Color', c.gray);
    yyaxis(ax, 'left');
    text(ax, 0.95, basis.SFx(1)+0.25, sprintf('SF_x = %.2f', basis.SFx(1)), ...
        'FontSize', 7, 'Color', c.ferrite, 'HorizontalAlignment', 'right');
    title(ax, 'validation-base metrics');
    clean_axes(ax);
    panel_label(ax, '(b)');

    export_fig(fig, out_dir, 'Fig02_ferrite_base_selection');
end

function make_fig03_hybrid(out_dir, c, hybrid)
    fig = newfig(7.16, 2.50);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
    labels = {'Ferrite', '+AM', '+NC'};
    x = 1:height(hybrid);
    col = [c.ferrite; c.amorphous; c.nano];

    ax = nexttile(tl, 1);
    hold(ax, 'on');
    plot(ax, x, hybrid.SFx, '-o', 'Color', [0 0 0], 'MarkerSize', 4.8, ...
        'MarkerFaceColor', 'w', 'LineWidth', 1.2);
    for k = 1:numel(x)
        plot(ax, x(k), hybrid.SFx(k), 'o', 'Color', col(k,:), 'MarkerFaceColor', col(k,:), ...
            'MarkerSize', 5.5);
        text(ax, x(k), hybrid.SFx(k)+0.8, sprintf('%.2f', hybrid.SFx(k)), ...
            'HorizontalAlignment', 'center', 'FontSize', 7);
    end
    set(ax, 'XTick', x, 'XTickLabel', labels);
    ylabel(ax, 'SF_x');
    title(ax, 'transverse shielding');
    ylim(ax, [0 max(hybrid.SFx)*1.17]);
    clean_axes(ax);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    semilogy(ax, x, hybrid.IntH2_total, '-s', 'Color', [0 0 0], 'MarkerSize', 4.8, ...
        'MarkerFaceColor', 'w', 'LineWidth', 1.2);
    set(ax, 'YScale', 'log');
    for k = 1:numel(x)
        semilogy(ax, x(k), hybrid.IntH2_total(k), 's', 'Color', col(k,:), ...
            'MarkerFaceColor', col(k,:), 'MarkerSize', 5.5);
        text(ax, x(k), hybrid.IntH2_total(k)*1.35, sprintf('%.1e', hybrid.IntH2_total(k)), ...
            'HorizontalAlignment', 'center', 'FontSize', 7);
    end
    set(ax, 'XTick', x, 'XTickLabel', labels);
    ylabel(ax, 'IntH2 total');
    title(ax, 'noise-related integral');
    clean_axes(ax);
    panel_label(ax, '(b)');

    export_fig(fig, out_dir, 'Fig03_hybrid_outer_layer_enhancement');
end

function make_fig04_axial(out_dir, c, axial)
    fig = newfig(7.16, 2.55);
    tl = tiledlayout(fig, 1, 3, 'TileSpacing', 'compact', 'Padding', 'compact');
    labels = {'Open', 'P0', '+NC cap'};
    x = 1:height(axial);
    col = [c.ferrite; c.p0; c.cap];

    ax = nexttile(tl, 1);
    hold(ax, 'on'); axis(ax, 'off');
    xlim(ax, [0 3.1]); ylim(ax, [0 1.8]);
    for k = 1:3
        y = 1.45 - (k-1)*0.55;
        rectangle(ax, 'Position', [0.45 y-0.18 1.20 0.36], 'EdgeColor', col(k,:), 'LineWidth', 1.0);
        if k > 1
            rectangle(ax, 'Position', [1.78 y-0.23 0.08 0.46], 'FaceColor', col(k,:), 'EdgeColor', col(k,:));
        end
        text(ax, 2.05, y, labels{k}, 'FontSize', 7, 'VerticalAlignment', 'middle');
    end
    title(ax, 'cap configurations');
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    plot(ax, x, axial.SFz, '-o', 'Color', [0 0 0], 'LineWidth', 1.2, 'MarkerFaceColor', 'w');
    for k = 1:numel(x)
        plot(ax, x(k), axial.SFz(k), 'o', 'Color', col(k,:), 'MarkerFaceColor', col(k,:), 'MarkerSize', 5.5);
        text(ax, x(k), axial.SFz(k)+0.045, sprintf('%.2f', axial.SFz(k)), ...
            'HorizontalAlignment', 'center', 'FontSize', 7);
    end
    set(ax, 'XTick', x, 'XTickLabel', labels);
    ylabel(ax, 'SF_z');
    title(ax, 'axial shielding');
    ylim(ax, [2.25 3.05]);
    clean_axes(ax);
    panel_label(ax, '(b)');

    ax = nexttile(tl, 3);
    hold(ax, 'on');
    yyaxis(ax, 'left');
    semilogy(ax, x, axial.IntH2_total, '-s', 'Color', [0 0 0], 'LineWidth', 1.2, 'MarkerFaceColor', 'w');
    set(ax, 'YScale', 'log');
    ylabel(ax, 'IntH2 total');
    ax.YAxis(1).Color = [0 0 0];
    yyaxis(ax, 'right');
    plot(ax, x, axial.LeakageRatioz, '--d', 'Color', c.gray, 'LineWidth', 1.0, 'MarkerFaceColor', 'w');
    ylabel(ax, 'leakage ratio');
    ax.YAxis(2).Color = c.gray;
    set(ax, 'XTick', x, 'XTickLabel', labels);
    title(ax, 'tradeoff');
    grid(ax, 'on');
    clean_axes(ax);
    panel_label(ax, '(c)');

    export_fig(fig, out_dir, 'Fig04_axial_cap_tradeoff');
end

function make_fig05_geomag(out_dir, c, geomag)
    fig = newfig(7.16, 2.45);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
    dirs = ["x", "z"];
    titles = ["transverse residual", "axial residual"];
    labels = {{'Ferrite', '+AM', '+NC'}, {'Open', 'P0', '+NC cap'}};
    cols = {[c.ferrite; c.amorphous; c.nano], [c.ferrite; c.p0; c.cap]};
    for i = 1:2
        ax = nexttile(tl, i);
        hold(ax, 'on');
        sub = geomag(geomag.field_dir == dirs(i), :);
        x = 1:height(sub);
        for k = 1:numel(x)
            line(ax, [x(k) x(k)], [0 sub.Bcenter_geo_uT(k)], ...
                'Color', cols{i}(k,:), 'LineWidth', 1.4);
            plot(ax, x(k), sub.Bcenter_geo_uT(k), 'o', 'Color', cols{i}(k,:), ...
                'MarkerFaceColor', cols{i}(k,:), 'MarkerSize', 5.2);
            text(ax, x(k), sub.Bcenter_geo_uT(k)+0.75, sprintf('%.2f', sub.Bcenter_geo_uT(k)), ...
                'HorizontalAlignment', 'center', 'FontSize', 7);
        end
        set(ax, 'XTick', x, 'XTickLabel', labels{i});
        ylabel(ax, 'residual field (\muT)');
        title(ax, titles(i));
        ylim(ax, [0 max(sub.Bcenter_geo_uT)*1.18]);
        clean_axes(ax);
        panel_label(ax, sprintf('(%c)', char('a'+i-1)));
    end
    export_fig(fig, out_dir, 'Fig05_geomagnetic_residual_estimate');
end

function make_fig06_loss(out_dir, c, loss)
    fig = newfig(3.50, 2.60);
    ax = axes(fig);
    hold(ax, 'on');
    cases = ["x_amorphous", "x_nanocrystalline", "z_p0_amorphous_shell_cap", "z_single_nanocrystalline_cap"];
    names = ["+AM outer", "+NC outer", "P0 AM cap", "NC cap"];
    cols = [c.amorphous; c.nano; c.p0; c.cap];
    marks = {'s', 'o', '^', 'd'};
    for k = 1:numel(cases)
        sub = loss(loss.case_label == cases(k), :);
        if isempty(sub)
            continue;
        end
        loglog(ax, sub.mu_pp_non_ferrite_over_ferrite, sub.noise_amp_ratio_vs_reference, ...
            ['-' marks{k}], 'Color', cols(k,:), 'MarkerFaceColor', 'w', ...
            'MarkerSize', 4.0, 'LineWidth', 1.2, 'DisplayName', names(k));
    end
    set(ax, 'XScale', 'log', 'YScale', 'log');
    yline(ax, 1, '--', 'Color', c.gray, 'LineWidth', 0.9, 'HandleVisibility', 'off');
    xlabel(ax, '\mu''''_{metal}/\mu''''_{ferrite}');
    ylabel(ax, 'noise amplitude ratio');
    title(ax, 'material-loss sensitivity');
    legend(ax, 'Location', 'northwest', 'Box', 'off');
    clean_axes(ax);
    export_fig(fig, out_dir, 'Fig06_material_loss_sensitivity');
end

function make_fig07_base_selection_matrix(out_dir, c, matrix, basis)
    fig = newfig(7.16, 2.65);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
    candidates = matrix(matrix.stage == "screen_continuous" & ...
        matrix.model_type == "continuous_shell" & matrix.external_field_direction == "x", :);
    candidates = candidates(candidates.N_layers <= 4, :);
    [~, order] = sortrows([candidates.N_layers candidates.T_space_mm]);
    candidates = candidates(order, :);
    labels = strings(height(candidates), 1);
    for k = 1:height(candidates)
        if candidates.N_layers(k) == 1
            labels(k) = sprintf('N1 %.2f', candidates.t_ferrite_mm(k));
        else
            labels(k) = sprintf('N%d %.2f/%.2f', candidates.N_layers(k), ...
                candidates.t_ferrite_mm(k), candidates.g_radial_mm(k));
        end
    end
    selected = candidates.case_id == "C2_N4_t015_g008_x";
    x = 1:height(candidates);

    ax = nexttile(tl, 1);
    hold(ax, 'on');
    bar(ax, x, candidates.T_ferrite_total_mm, 0.62, ...
        'FaceColor', c.lightGray, 'EdgeColor', c.gray, 'LineWidth', 0.7);
    plot(ax, x, candidates.T_space_mm, '-o', 'Color', c.amorphous, ...
        'MarkerFaceColor', 'w', 'MarkerSize', 4.5, 'LineWidth', 1.1);
    plot(ax, x(selected), candidates.T_space_mm(selected), 'o', ...
        'Color', c.nano, 'MarkerFaceColor', c.nano, 'MarkerSize', 6);
    ylabel(ax, 'thickness / radial space (mm)');
    set(ax, 'XTick', x, 'XTickLabel', labels);
    xtickangle(ax, 28);
    title(ax, 'manufacturable candidate matrix');
    legend(ax, {'ferrite thickness', 'radial space'}, 'Location', 'northwest', 'Box', 'off');
    clean_axes(ax);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    yyaxis(ax, 'left');
    plot(ax, 1, basis.SFx(1), 'o', 'Color', c.nano, 'MarkerFaceColor', c.nano, ...
        'MarkerSize', 6, 'LineWidth', 1.2);
    ylabel(ax, 'SF_x');
    ylim(ax, [0 max(4.5, basis.SFx(1)*1.35)]);
    ax.YAxis(1).Color = [0 0 0];
    yyaxis(ax, 'right');
    semilogy(ax, 1, basis.IntH2_total(1), 's', 'Color', c.gray, ...
        'MarkerFaceColor', c.gray, 'MarkerSize', 6, 'LineWidth', 1.2);
    set(ax, 'YScale', 'log');
    ylabel(ax, 'IntH2 total');
    ax.YAxis(2).Color = c.gray;
    set(ax, 'XTick', 1, 'XTickLabel', {'selected N4'});
    xlim(ax, [0.62 1.38]);
    title(ax, 'validated base metrics');
    text(ax, 1.08, basis.IntH2_total(1)*1.25, sprintf('%.2e', basis.IntH2_total(1)), ...
        'FontSize', 7, 'Color', c.gray);
    yyaxis(ax, 'left');
    text(ax, 0.96, basis.SFx(1)+0.25, sprintf('SF_x = %.2f', basis.SFx(1)), ...
        'FontSize', 7, 'HorizontalAlignment', 'right', 'Color', c.nano);
    clean_axes(ax);
    panel_label(ax, '(b)');

    export_fig(fig, out_dir, 'Fig07_ferrite_base_selection_matrix');
end

function make_fig08_sf_intH2_tradeoff_map(out_dir, c, hybrid, axial)
    fig = newfig(3.50, 2.75);
    ax = axes(fig);
    hold(ax, 'on');
    hlabels = {'Ferrite x', '+AM x', '+NC x'};
    hcols = [c.ferrite; c.amorphous; c.nano];
    for k = 1:height(hybrid)
        loglog(ax, hybrid.SFx(k), hybrid.IntH2_total(k), 'o', ...
            'Color', hcols(k,:), 'MarkerFaceColor', hcols(k,:), ...
            'MarkerSize', 5.8, 'LineWidth', 1.0);
        if k == height(hybrid)
            text(ax, hybrid.SFx(k)*0.93, hybrid.IntH2_total(k)*1.22, hlabels{k}, ...
                'FontSize', 7, 'Color', hcols(k,:), 'HorizontalAlignment', 'right');
        else
            text(ax, hybrid.SFx(k)*1.08, hybrid.IntH2_total(k)*1.12, hlabels{k}, ...
                'FontSize', 7, 'Color', hcols(k,:));
        end
    end
    alabels = {'Open z', 'P0 z', 'NC cap z'};
    acols = [c.gray; c.p0; c.cap];
    for k = 1:height(axial)
        loglog(ax, axial.SFz(k), axial.IntH2_total(k), 's', ...
            'Color', acols(k,:), 'MarkerFaceColor', 'w', ...
            'MarkerSize', 5.8, 'LineWidth', 1.1);
        text(ax, axial.SFz(k)*1.08, axial.IntH2_total(k)*0.82, alabels{k}, ...
            'FontSize', 7, 'Color', acols(k,:));
    end
    set(ax, 'XScale', 'log', 'YScale', 'log');
    xlim(ax, [1.8 34]);
    ylim(ax, [3.0e-8 7.0e-6]);
    xlabel(ax, 'shielding factor');
    ylabel(ax, 'IntH2 total');
    title(ax, 'SF-IntH2 tradeoff map');
    grid(ax, 'on');
    clean_axes(ax);
    export_fig(fig, out_dir, 'Fig08_SFx_IntH2_tradeoff_map');
end

function make_fig09_layerwise_intH2_contribution(out_dir, c, hybrid, axial)
    fig = newfig(7.16, 2.70);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

    ax = nexttile(tl, 1);
    hold(ax, 'on');
    ferrite = hybrid.IntH2_total;
    outer = zeros(height(hybrid), 1);
    has_outer = ~isnan(hybrid.IntH2_outer);
    outer(has_outer) = hybrid.IntH2_outer(has_outer);
    ferrite(has_outer) = hybrid.IntH2_total(has_outer) - hybrid.IntH2_outer(has_outer);
    vals = 100 * [ferrite outer] ./ hybrid.IntH2_total;
    bar(ax, vals, 'stacked', 'LineWidth', 0.6);
    ax.Children(2).FaceColor = c.lightGray;
    ax.Children(1).FaceColor = c.nano;
    set(ax, 'XTick', 1:height(hybrid), 'XTickLabel', {'Ferrite', '+AM', '+NC'});
    ylabel(ax, 'IntH2 contribution (%)');
    ylim(ax, [0 100]);
    title(ax, 'transverse hybrid cases');
    legend(ax, {'ferrite layers', 'outer layer'}, 'Location', 'southoutside', ...
        'Orientation', 'horizontal', 'Box', 'off');
    clean_axes(ax);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    vals = 100 * [axial.IntH2_ferrite axial.IntH2_cap] ./ axial.IntH2_total;
    vals(isnan(vals)) = 0;
    bar(ax, vals, 'stacked', 'LineWidth', 0.6);
    ax.Children(2).FaceColor = c.lightGray;
    ax.Children(1).FaceColor = c.cap;
    set(ax, 'XTick', 1:height(axial), 'XTickLabel', {'Open', 'P0', 'NC cap'});
    ylabel(ax, 'IntH2 contribution (%)');
    ylim(ax, [0 100]);
    title(ax, 'axial cap cases');
    legend(ax, {'ferrite shell', 'cap / non-ferrite'}, 'Location', 'southoutside', ...
        'Orientation', 'horizontal', 'Box', 'off');
    clean_axes(ax);
    panel_label(ax, '(b)');

    export_fig(fig, out_dir, 'Fig09_layerwise_IntH2_contribution');
end

function make_fig10_noise_proxy_1to30Hz(out_dir, c, noise)
    fig = newfig(7.16, 2.65);
    tl = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
    keep = ismember(noise.case_label, ["x_ferrite_only", "x_amorphous", ...
        "x_nanocrystalline", "z_open_ferrite_only", ...
        "z_p0_amorphous_shell_cap", "z_single_nanocrystalline_cap"]);
    noise = noise(keep, :);
    labels = {'Ferrite x', '+AM x', '+NC x', 'Open z', 'P0 z', 'NC cap z'};
    x = 1:height(noise);
    cols = [c.ferrite; c.amorphous; c.nano; c.gray; c.p0; c.cap];

    ax = nexttile(tl, 1);
    hold(ax, 'on');
    for k = 1:height(noise)
        bar(ax, x(k), noise.B_avg_1_30Hz_fT(k), 0.62, ...
            'FaceColor', cols(k,:), 'EdgeColor', cols(k,:), 'LineWidth', 0.6);
        text(ax, x(k), noise.B_avg_1_30Hz_fT(k)+0.005, ...
            sprintf('%.3f', noise.B_avg_1_30Hz_fT(k)), ...
            'HorizontalAlignment', 'center', 'FontSize', 7);
    end
    set(ax, 'XTick', x, 'XTickLabel', labels);
    xtickangle(ax, 28);
    ylabel(ax, 'B avg 1-30 Hz (fT)');
    title(ax, 'band-averaged noise proxy');
    clean_axes(ax);
    panel_label(ax, '(a)');

    ax = nexttile(tl, 2);
    hold(ax, 'on');
    for k = 1:height(noise)
        plot(ax, noise.SF(k), noise.B_1Hz_fT(k), 'o', ...
            'Color', cols(k,:), 'MarkerFaceColor', cols(k,:), ...
            'MarkerSize', 5.8, 'LineWidth', 1.0);
        yoff = 0.006;
        if noise.B_1Hz_fT(k) > 0.25
            yoff = -0.012;
        end
        text(ax, noise.SF(k)*1.05, noise.B_1Hz_fT(k)+yoff, labels{k}, ...
            'FontSize', 7, 'Color', cols(k,:));
    end
    xlim(ax, [0 31]);
    ylim(ax, [0 0.32]);
    xlabel(ax, 'shielding factor');
    ylabel(ax, 'B at 1 Hz (fT)');
    title(ax, '1 Hz proxy versus SF');
    clean_axes(ax);
    panel_label(ax, '(b)');

    export_fig(fig, out_dir, 'Fig10_noise_proxy_1to30Hz');
end

%% Helpers
function set_journal_style()
    set(0, 'DefaultFigureColor', 'w');
    set(0, 'DefaultAxesFontName', 'Times New Roman');
    set(0, 'DefaultTextFontName', 'Times New Roman');
    set(0, 'DefaultAxesFontSize', 8);
    set(0, 'DefaultTextFontSize', 8);
    set(0, 'DefaultLineLineWidth', 1.2);
    set(0, 'DefaultAxesLineWidth', 0.75);
    set(0, 'DefaultAxesBox', 'off');
    set(0, 'DefaultAxesTickDir', 'out');
end

function fig = newfig(w, h)
    fig = figure('Visible', 'off', 'Units', 'inches', 'Position', [0 0 w h], ...
        'PaperUnits', 'inches', 'PaperPosition', [0 0 w h]);
end

function clean_axes(ax)
    ax.Box = 'off';
    ax.TickDir = 'out';
    ax.GridColor = [0.82 0.82 0.82];
    ax.GridAlpha = 0.65;
    ax.YGrid = 'on';
    ax.YMinorGrid = 'off';
    ax.XGrid = 'off';
    ax.XMinorGrid = 'off';
end

function panel_label(ax, label)
    text(ax, 0.02, 0.98, label, 'Units', 'normalized', ...
        'FontWeight', 'bold', 'FontSize', 8, 'VerticalAlignment', 'bottom');
end

function annotation_arrow(ax, from_xy, to_xy, color)
    plot(ax, [from_xy(1) to_xy(1)], [from_xy(2) to_xy(2)], '-', ...
        'Color', color, 'LineWidth', 0.8);
    plot(ax, to_xy(1), to_xy(2), '>', 'Color', color, 'MarkerFaceColor', color, ...
        'MarkerSize', 4);
end

function export_fig(fig, out_dir, stem)
    png = fullfile(out_dir, stem + ".png");
    exportgraphics(fig, png, 'Resolution', 600);
    close(fig);
end

function write_manifest(out_dir)
    lines = [
        "# MATLAB rebuilt TIE-style figure manifest"
        ""
        "Generated by `matlab-B/make_tie_journal_figures.m`."
        ""
        "- `Fig01_concept_hybrid_multilayer_shield.png`: hybrid ferrite/ribbon concept and cap configuration."
        "- `Fig02_ferrite_base_selection.png`: four-layer ferrite geometry and validation-base metrics."
        "- `Fig03_hybrid_outer_layer_enhancement.png`: transverse SFx and IntH2 comparison for ferrite, amorphous, and nanocrystalline cases."
        "- `Fig04_axial_cap_tradeoff.png`: axial cap configuration, SFz, IntH2, and leakage-ratio tradeoff."
        "- `Fig05_geomagnetic_residual_estimate.png`: 50 uT linear residual-field scaling."
        "- `Fig06_material_loss_sensitivity.png`: parametric loss sensitivity for unknown metallic ribbon mu''."
        "- `Fig07_ferrite_base_selection_matrix.png`: manufacturable ferrite candidate matrix and selected-base metrics."
        "- `Fig08_SFx_IntH2_tradeoff_map.png`: combined transverse and axial SF-IntH2 tradeoff map."
        "- `Fig09_layerwise_IntH2_contribution.png`: material-separated IntH2 contributions for hybrid and cap cases."
        "- `Fig10_noise_proxy_1to30Hz.png`: 1-30 Hz magnetic-noise proxy based on current IntH2 assumptions."
    ];
    writelines(lines, fullfile(out_dir, "figure_manifest.md"));
end
