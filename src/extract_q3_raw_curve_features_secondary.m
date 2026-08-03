function extract_q3_raw_curve_features_secondary()
%EXTRACT_Q3_RAW_CURVE_FEATURES_SECONDARY Frozen raw features for one final test.
% Writes only to results/Secondary_final_pressure_test/inputs.  It does not
% alter the Train-only feature files or any raw MAT source.

script_path = mfilename('fullpath');
l1_root = fileparts(fileparts(script_path));
processed_dir = fullfile(l1_root, 'data', 'processed');
audit_dir = fullfile(l1_root, 'outputs', 'data_audit');
output_dir = fullfile(l1_root, 'results', 'Secondary_final_pressure_test', 'inputs');
if ~isfolder(output_dir), mkdir(output_dir); end

labels = readtable(fullfile(processed_dir, 'cell_labels.csv'), TextType='string');
view = readtable(fullfile(processed_dir, 'cycle_model_view.csv'), TextType='string');
flags = readtable(fullfile(audit_dir, 'mat_deep_cycle_flags.csv'), TextType='string');
secondary = labels(labels.dataset_table9 == "Sec. test", :);
if height(secondary) ~= 40 || numel(unique(secondary.barcode)) ~= 40
    error('Expected exactly 40 unique Secondary barcodes.');
end

needed = view.dataset_table9 == "Sec. test" & view.global_cycle_index >= 2 & view.global_cycle_index <= 100;
view_secondary = view(needed, :);
key_view = strcat(view_secondary.source_file, "|", string(view_secondary.batch_index), "|", string(view_secondary.cycle_index));
key_flags = strcat(flags.source_file, "|", string(flags.batch_index), "|", string(flags.cycle_index));
[is_found, positions] = ismember(key_view, key_flags);
if ~all(is_found)
    error('Some Secondary cycles have no matching deep MAT audit flag.');
end
if any(as_logical(view_secondary.raw_usable_for_curve_features) ~= as_logical(flags.usable_for_curve_features(positions)))
    error('P0 raw curve mask does not match mat_deep_cycle_flags.csv for Secondary.');
end

sources = cell(3, 1);
for source_id = 1:3
    sources{source_id} = matfile(fullfile(l1_root, sprintf('data_%d.mat', source_id)));
end
record_cache = cell(3, max(view_secondary.batch_index));
cycles = (2:100)';
cell_count = height(secondary);
raw_v_mean = nan(cell_count, numel(cycles));
raw_v_p95 = nan(cell_count, numel(cycles));
usable = false(cell_count, numel(cycles));
for cell_id = 1:cell_count
    barcode = secondary.barcode(cell_id);
    rows = view_secondary(view_secondary.barcode == barcode, :);
    for row_id = 1:height(rows)
        global_cycle = rows.global_cycle_index(row_id);
        cycle_position = global_cycle - 1;
        if ~as_logical(rows.raw_usable_for_curve_features(row_id)), continue; end
        source_id = sscanf(char(rows.source_file(row_id)), 'data_%d.xlsx');
        batch_id = rows.batch_index(row_id);
        if isempty(record_cache{source_id, batch_id})
            record_cache{source_id, batch_id} = sources{source_id}.batch(1, batch_id);
        end
        raw_record = record_cache{source_id, batch_id};
        raw_cycle = raw_record.cycles(rows.cycle_index(row_id));
        charge_voltage = raw_cycle.V(raw_cycle.I(:) > 0.1);
        if isempty(charge_voltage) || any(~isfinite(charge_voltage)), continue; end
        raw_v_mean(cell_id, cycle_position) = mean(charge_voltage);
        raw_v_p95(cell_id, cycle_position) = prctile(charge_voltage, 95);
        usable(cell_id, cycle_position) = true;
    end
end

windows = [5, 100];
summary = struct('scope', 'One-time frozen Secondary raw features; I>0.1 A charge points; six-field deep MAT mask required.', ...
    'features', {{'raw_charge_v_mean_mean', 'raw_charge_v_p95_mean', 'raw_charge_v_p95_slope'}}, ...
    'windows', windows, 'source_mask', 'outputs/data_audit/mat_deep_cycle_flags.csv');
for window_id = 1:numel(windows)
    k = windows(window_id);
    indices = 1:(k - 1);
    valid_count = sum(usable(:, indices), 2);
    valid_ratio = valid_count ./ numel(indices);
    mean_feature = nan(cell_count, 1); p95_feature = nan(cell_count, 1); p95_slope = nan(cell_count, 1);
    for cell_id = 1:cell_count
        valid_indices = indices(usable(cell_id, indices));
        if isempty(valid_indices), continue; end
        mean_feature(cell_id) = mean(raw_v_mean(cell_id, valid_indices));
        p95_feature(cell_id) = mean(raw_v_p95(cell_id, valid_indices));
        if numel(valid_indices) >= 2
            coefficient = polyfit(cycles(valid_indices), raw_v_p95(cell_id, valid_indices)', 1);
            p95_slope(cell_id) = coefficient(1);
        end
    end
    if any(valid_ratio < 0.8) || any(isnan(mean_feature) | isnan(p95_feature) | isnan(p95_slope))
        error('Secondary RAW feature gate failed: raw_valid_ratio must be at least 0.8 and all features finite.');
    end
    table_out = table(secondary.barcode, repmat(k, cell_count, 1), repmat(numel(indices), cell_count, 1), valid_count, valid_ratio, mean_feature, p95_feature, p95_slope, ...
        VariableNames=["barcode", "window_k", "raw_expected_cycle_count", "raw_valid_count", "raw_valid_ratio", "raw_charge_v_mean_mean", "raw_charge_v_p95_mean", "raw_charge_v_p95_slope"]);
    filename = fullfile(output_dir, sprintf('raw_curve_features_secondary_k%d.csv', k));
    writetable(table_out, filename, Encoding='UTF-8');
    summary.(sprintf('k%d', k)) = struct('cells', height(table_out), 'min_valid_ratio', min(valid_ratio), 'cells_below_80pct_valid', sum(valid_ratio < 0.8));
end

file_id = fopen(fullfile(output_dir, 'raw_curve_features_secondary_summary.json'), 'w', 'n', 'UTF-8');
assert(file_id ~= -1, 'Could not write Secondary RAW summary.');
cleanup = onCleanup(@() fclose(file_id));
fprintf(file_id, '%s', jsonencode(summary, PrettyPrint=true));
fprintf('Wrote frozen Secondary RAW features for k=5 and k=100.\n');
end

function result = as_logical(value)
if islogical(value)
    result = value;
else
    result = lower(string(value)) == "true" | string(value) == "1";
end
end
