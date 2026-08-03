% Reproducible, read-only metadata audit for the three MATLAB v7.3 files.
script_path = mfilename('fullpath');
l1_root = fileparts(fileparts(script_path));
output_dir = fullfile(l1_root, 'outputs', 'data_audit');
if ~isfolder(output_dir)
    mkdir(output_dir);
end

sources = repmat(struct(), 1, 3);
for source_index = 1:3
    mat_name = sprintf('data_%d.mat', source_index);
    mat_path = fullfile(l1_root, mat_name);
    variables = whos('-file', mat_path);
    batch_info = variables(strcmp({variables.name}, 'batch'));
    source = matfile(mat_path);
    first_record = source.batch(1, 1);

    sources(source_index).mat_file = mat_name;
    sources(source_index).xlsx_file = sprintf('data_%d.xlsx', source_index);
    sources(source_index).batch_date = char(source.batch_date);
    sources(source_index).batch_records = batch_info.size(2);
    sources(source_index).top_level_variables = {variables.name};
    sources(source_index).record_fields = fieldnames(first_record)';
    sources(source_index).cycle_fields = fieldnames(first_record.cycles(1))';
    sources(source_index).summary_fields = fieldnames(first_record.summary)';
    sources(source_index).vdlin_length = numel(first_record.Vdlin);
end

audit = struct();
audit.scope = 'read-only MAT metadata; representative nested schema from first record of each source';
audit.sources = sources;
json_text = jsonencode(audit, PrettyPrint=true);
output_path = fullfile(output_dir, 'mat_metadata.json');
file_id = fopen(output_path, 'w', 'n', 'UTF-8');
assert(file_id ~= -1, 'Unable to open output: %s', output_path);
cleanup = onCleanup(@() fclose(file_id));
fprintf(file_id, '%s', json_text);
fprintf('Wrote %s\n', output_path);
