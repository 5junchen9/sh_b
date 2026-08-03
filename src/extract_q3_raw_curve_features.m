function extract_q3_raw_curve_features()
%EXTRACT_Q3_RAW_CURVE_FEATURES Read-only low-dimensional RAW challenger features.
% Uses only Train cells and only cycles accepted by the six-field deep MAT mask.
% It never sorts t, edits MAT values, or replaces an unusable cycle.

script_path = mfilename('fullpath');
l1_root = fileparts(fileparts(script_path));
processed_dir = fullfile(l1_root, 'data', 'processed');
audit_dir = fullfile(l1_root, 'outputs', 'data_audit');
labels = readtable(fullfile(processed_dir, 'cell_labels.csv'), TextType='string');
view = readtable(fullfile(processed_dir, 'cycle_model_view.csv'), TextType='string');
flags = readtable(fullfile(audit_dir, 'mat_deep_cycle_flags.csv'), TextType='string');
train = labels(labels.dataset_table9 == "Train", :);
if height(train) ~= 41 || numel(unique(train.barcode)) ~= 41
    error('Expected exactly 41 unique Train barcodes.');
end

% Verify P0's copied raw flag against the original deep-audit key for all Train rows.
view_train = view(view.dataset_table9 == "Train" & view.global_cycle_index >= 2 & view.global_cycle_index <= 100, :);
key_view = strcat(view_train.source_file, "|", string(view_train.batch_index), "|", string(view_train.cycle_index));
key_flags = strcat(flags.source_file, "|", string(flags.batch_index), "|", string(flags.cycle_index));
[is_found, positions] = ismember(key_view, key_flags);
if ~all(is_found)
    error('Some Train cycles have no matching deep MAT audit flag.');
end
if any(as_logical(view_train.raw_usable_for_curve_features) ~= as_logical(flags.usable_for_curve_features(positions)))
    error('P0 raw curve mask does not match mat_deep_cycle_flags.csv.');
end

sources = cell(3, 1);
for source_id = 1:3
    sources{source_id} = matfile(fullfile(l1_root, sprintf('data_%d.mat', source_id)));
end
% Cache each required MAT record once. Directly indexing matfile.batch for every
% cycle repeatedly transfers the whole nested record and is unnecessarily slow.
record_cache = cell(3, max(view_train.batch_index));

cycles = (2:100)';
cell_count = height(train);
raw_v_mean = nan(cell_count, numel(cycles));
raw_v_p95 = nan(cell_count, numel(cycles));
usable = false(cell_count, numel(cycles));
for cell_id = 1:cell_count
    barcode = train.barcode(cell_id);
    rows = view_train(view_train.barcode == barcode, :);
    for row_id = 1:height(rows)
        global_cycle = rows.global_cycle_index(row_id);
        cycle_position = global_cycle - 1;
        if ~as_logical(rows.raw_usable_for_curve_features(row_id))
            continue;
        end
        source_id = sscanf(char(rows.source_file(row_id)), 'data_%d.xlsx');
        batch_id = rows.batch_index(row_id);
        if isempty(record_cache{source_id, batch_id})
            record_cache{source_id, batch_id} = sources{source_id}.batch(1, batch_id);
        end
        raw_record = record_cache{source_id, batch_id};
        raw_cycle = raw_record.cycles(rows.cycle_index(row_id));
        charge_points = raw_cycle.I(:) > 0.1;
        charge_voltage = raw_cycle.V(charge_points);
        if isempty(charge_voltage) || any(~isfinite(charge_voltage))
            continue;
        end
        raw_v_mean(cell_id, cycle_position) = mean(charge_voltage);
        raw_v_p95(cell_id, cycle_position) = prctile(charge_voltage, 95);
        usable(cell_id, cycle_position) = true;
    end
end

windows = [5, 10, 20, 50, 100];
summary = struct();
summary.scope = 'Train-only read-only RAW curve challenger features; I>0.1 A charge points; six-field deep MAT mask required.';
summary.features = {'raw_charge_v_mean_mean', 'raw_charge_v_p95_mean', 'raw_charge_v_p95_slope'};
summary.windows = windows;
summary.source_mask = 'outputs/data_audit/mat_deep_cycle_flags.csv';
summary.output_files = cell(numel(windows), 1);
for window_id = 1:numel(windows)
    k = windows(window_id);
    indices = 1:(k - 1); % global cycles 2...k
    expected_count = numel(indices);
    raw_valid_count = sum(usable(:, indices), 2);
    raw_valid_ratio = raw_valid_count ./ expected_count;
    mean_feature = nan(cell_count, 1);
    p95_feature = nan(cell_count, 1);
    p95_slope = nan(cell_count, 1);
    for cell_id = 1:cell_count
        valid_indices = indices(usable(cell_id, indices));
        if isempty(valid_indices)
            continue;
        end
        mean_feature(cell_id) = mean(raw_v_mean(cell_id, valid_indices));
        p95_feature(cell_id) = mean(raw_v_p95(cell_id, valid_indices));
        if numel(valid_indices) >= 2
            coefficient = polyfit(cycles(valid_indices), raw_v_p95(cell_id, valid_indices)', 1);
            p95_slope(cell_id) = coefficient(1);
        end
    end
    feature_table = table(train.barcode, repmat(k, cell_count, 1), repmat(expected_count, cell_count, 1), raw_valid_count, raw_valid_ratio, ...
        mean_feature, p95_feature, p95_slope, ...
        VariableNames=["barcode", "window_k", "raw_expected_cycle_count", "raw_valid_count", "raw_valid_ratio", ...
        "raw_charge_v_mean_mean", "raw_charge_v_p95_mean", "raw_charge_v_p95_slope"]);
    output_file = fullfile(processed_dir, sprintf('raw_curve_features_train_k%d.csv', k));
    writetable(feature_table, output_file, Encoding='UTF-8');
    summary.output_files{window_id} = strrep(output_file, [l1_root filesep], '');
    summary.(sprintf('k%d', k)) = struct('cells', height(feature_table), 'min_valid_ratio', min(raw_valid_ratio), ...
        'cells_below_80pct_valid', sum(raw_valid_ratio < 0.8), 'all_feature_missing', sum(isnan(mean_feature) | isnan(p95_feature) | isnan(p95_slope)));
end
file_id = fopen(fullfile(processed_dir, 'raw_curve_features_train_summary.json'), 'w', 'n', 'UTF-8');
assert(file_id ~= -1, 'Could not create raw curve feature summary.');
cleanup = onCleanup(@() fclose(file_id));
fprintf(file_id, '%s', jsonencode(summary, PrettyPrint=true));
fprintf('Wrote Train-only RAW curve challenger features for k=5/10/20/50/100.\n');
end

function result = as_logical(value)
% CSV import may produce logical or string columns on different MATLAB versions.
if islogical(value)
    result = value;
else
    result = lower(string(value)) == "true" | string(value) == "1";
end
end
