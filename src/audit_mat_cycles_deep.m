% Read-only deep audit of raw cycle arrays in all L1 MAT records.
% Creates one row per source record/cycle; never alters a MAT value or drops a cell.
script_path = mfilename('fullpath');
l1_root = fileparts(fileparts(script_path));
output_dir = fullfile(l1_root, 'outputs', 'data_audit');
if ~isfolder(output_dir)
    mkdir(output_dir);
end

roster = readtable(fullfile(output_dir, 'clean_cell_roster.csv'), TextType='string');
official_barcodes = upper(string(roster.barcode));
field_names = ["t", "Qc", "I", "V", "T", "Qd"];
estimated_rows = 120000;

source_file = strings(estimated_rows, 1);
mat_file = strings(estimated_rows, 1);
barcode = strings(estimated_rows, 1);
source_index = zeros(estimated_rows, 1);
batch_index = zeros(estimated_rows, 1);
cycle_index = zeros(estimated_rows, 1);
in_official_roster = false(estimated_rows, 1);
lengths = zeros(estimated_rows, numel(field_names));
lengths_match = false(estimated_rows, 1);
all_fields_empty = false(estimated_rows, 1);
has_nan_inf = false(estimated_rows, 1);
t_negative = false(estimated_rows, 1);
t_reverse = false(estimated_rows, 1);
capacity_negative = false(estimated_rows, 1);
current_out_of_range = false(estimated_rows, 1);
voltage_out_of_range = false(estimated_rows, 1);
temperature_out_of_range = false(estimated_rows, 1);
usable_for_curve_features = false(estimated_rows, 1);
failure_reason = strings(estimated_rows, 1);
row_count = 0;

for source_id = 1:3
    current_mat = sprintf('data_%d.mat', source_id);
    current_xlsx = sprintf('data_%d.xlsx', source_id);
    source = matfile(fullfile(l1_root, current_mat));
    source_size = size(source, 'batch');
    for record_id = 1:source_size(2)
        record = source.batch(1, record_id);
        record_barcode = upper(string(record.barcode));
        cycle_count = numel(record.cycles);
        for local_cycle = 1:cycle_count
            row_count = row_count + 1;
            if row_count > numel(source_index)
                error('Estimated audit row capacity exceeded. Increase estimated_rows.');
            end
            cycle = record.cycles(local_cycle);
            values = {cycle.t, cycle.Qc, cycle.I, cycle.V, cycle.T, cycle.Qd};
            current_lengths = cellfun(@numel, values);
            reasons = strings(8, 1);
            reason_count = 0;

            source_file(row_count) = current_xlsx;
            mat_file(row_count) = current_mat;
            barcode(row_count) = record_barcode;
            source_index(row_count) = source_id;
            batch_index(row_count) = record_id;
            cycle_index(row_count) = local_cycle;
            in_official_roster(row_count) = ismember(record_barcode, official_barcodes);
            lengths(row_count, :) = current_lengths;
            lengths_match(row_count) = all(current_lengths == current_lengths(1));
            all_fields_empty(row_count) = all(current_lengths == 0);
            if ~lengths_match(row_count)
                reason_count = reason_count + 1;
                reasons(reason_count) = "length_mismatch";
            end
            if all_fields_empty(row_count)
                reason_count = reason_count + 1;
                reasons(reason_count) = "all_fields_empty";
            end

            for field_id = 1:numel(values)
                value = values{field_id};
                if any(~isfinite(value(:)))
                    has_nan_inf(row_count) = true;
                end
            end
            if has_nan_inf(row_count)
                reason_count = reason_count + 1;
                reasons(reason_count) = "nan_or_inf";
            end

            t = cycle.t(:);
            qc = cycle.Qc(:);
            qd = cycle.Qd(:);
            current = cycle.I(:);
            v = cycle.V(:);
            temp = cycle.T(:);
            t_negative(row_count) = any(t < 0);
            t_reverse(row_count) = numel(t) >= 2 && any(diff(t) < 0);
            capacity_negative(row_count) = any(qc < 0) || any(qd < 0);
            % 8 C × 1.1 Ah = 8.8 A; 12 A is a deliberately generous physical guardrail.
            current_out_of_range(row_count) = any(abs(current) > 12);
            voltage_out_of_range(row_count) = any(v < 0 | v > 5);
            temperature_out_of_range(row_count) = any(temp < -40 | temp > 100);
            if t_negative(row_count), reason_count = reason_count + 1; reasons(reason_count) = "negative_time"; end
            if t_reverse(row_count), reason_count = reason_count + 1; reasons(reason_count) = "time_reverse"; end
            if capacity_negative(row_count), reason_count = reason_count + 1; reasons(reason_count) = "negative_capacity"; end
            if current_out_of_range(row_count), reason_count = reason_count + 1; reasons(reason_count) = "abs_I_over_12A"; end
            if voltage_out_of_range(row_count), reason_count = reason_count + 1; reasons(reason_count) = "voltage_out_of_0_5V"; end
            if temperature_out_of_range(row_count), reason_count = reason_count + 1; reasons(reason_count) = "temperature_out_of_-40_100C"; end

            usable_for_curve_features(row_count) = lengths_match(row_count) && ~all_fields_empty(row_count) && ...
                ~has_nan_inf(row_count) && ~t_negative(row_count) && ~t_reverse(row_count) && ...
                ~capacity_negative(row_count) && ~current_out_of_range(row_count) && ...
                ~voltage_out_of_range(row_count) && ~temperature_out_of_range(row_count);
            failure_reason(row_count) = strjoin(reasons(1:reason_count), ';');
        end
    end
end

rows = 1:row_count;
audit_table = table(source_file(rows), mat_file(rows), barcode(rows), source_index(rows), batch_index(rows), cycle_index(rows), ...
    in_official_roster(rows), lengths(rows, 1), lengths(rows, 2), lengths(rows, 3), lengths(rows, 4), lengths(rows, 5), lengths(rows, 6), ...
    lengths_match(rows), all_fields_empty(rows), has_nan_inf(rows), t_negative(rows), t_reverse(rows), capacity_negative(rows), current_out_of_range(rows), ...
    voltage_out_of_range(rows), temperature_out_of_range(rows), usable_for_curve_features(rows), failure_reason(rows), ...
    VariableNames=["source_file", "mat_file", "barcode", "source_index", "batch_index", "cycle_index", ...
    "in_official_roster", "t_length", "Qc_length", "I_length", "V_length", "T_length", "Qd_length", ...
    "lengths_match", "all_fields_empty", "has_nan_inf", "t_negative", "t_reverse", "capacity_negative", "current_out_of_range", ...
    "voltage_out_of_range", "temperature_out_of_range", "usable_for_curve_features", "failure_reason"]);

flags_path = fullfile(output_dir, 'mat_deep_cycle_flags.csv');
writetable(audit_table, flags_path, Encoding='UTF-8');

summary = struct();
summary.scope = 'read-only scan of raw t/Qc/I/V/T/Qd arrays; no records or values removed';
summary.total_cycles = height(audit_table);
summary.official_roster_cycles = sum(audit_table.in_official_roster);
summary.length_mismatch_count = sum(~audit_table.lengths_match);
summary.all_fields_empty_count = sum(audit_table.all_fields_empty);
summary.nan_inf_count = sum(audit_table.has_nan_inf);
summary.negative_time_count = sum(audit_table.t_negative);
summary.time_reverse_count = sum(audit_table.t_reverse);
summary.negative_capacity_count = sum(audit_table.capacity_negative);
summary.current_out_of_range_count = sum(audit_table.current_out_of_range);
summary.voltage_out_of_range_count = sum(audit_table.voltage_out_of_range);
summary.temperature_out_of_range_count = sum(audit_table.temperature_out_of_range);
summary.usable_for_curve_features_count = sum(audit_table.usable_for_curve_features & audit_table.in_official_roster);
summary.unusable_official_cycle_count = sum(~audit_table.usable_for_curve_features & audit_table.in_official_roster);
summary.boundaries = struct('time_min', 0, 'capacity_min', 0, 'current_abs_max', 12, 'voltage_min', 0, 'voltage_max', 5, 'temperature_min', -40, 'temperature_max', 100);
summary.output_flags_csv = 'outputs/data_audit/mat_deep_cycle_flags.csv';

summary_path = fullfile(output_dir, 'mat_deep_cycle_summary.json');
file_id = fopen(summary_path, 'w', 'n', 'UTF-8');
assert(file_id ~= -1, 'Unable to open output: %s', summary_path);
cleanup = onCleanup(@() fclose(file_id));
fprintf(file_id, '%s', jsonencode(summary, PrettyPrint=true));
fprintf('Wrote %s\nWrote %s\n', flags_path, summary_path);
