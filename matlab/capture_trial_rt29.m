function capture_trial_rt29(radio_id, trial_num, center_freq_hz, sample_rate_hz, gain_db, duration_s, note)
% Fixed-duration RTL-SDR capture for the RT29 fingerprinting project.
%
% Example:
% capture_trial_rt29("radio_A", 1, 462562500, 2.0e6, 20, 12, "tone_burst")

    if nargin < 1, radio_id = "radio_A"; end
    if nargin < 2, trial_num = 1; end
    if nargin < 3, center_freq_hz = 462562500; end
    if nargin < 4, sample_rate_hz = 2.0e6; end
    if nargin < 5, gain_db = 20; end
    if nargin < 6, duration_s = 12; end
    if nargin < 7, note = ""; end

    this_file = mfilename('fullpath');
    matlab_dir = fileparts(this_file);
    project_root = fileparts(matlab_dir);
    raw_dir = fullfile(project_root, 'data', 'raw');
    logs_dir = fullfile(project_root, 'logs');

    if ~exist(raw_dir, 'dir'), mkdir(raw_dir); end
    if ~exist(logs_dir, 'dir'), mkdir(logs_dir); end

    timestamp = string(datetime('now', 'Format', 'yyyyMMdd_HHmmss'));
    out_file = fullfile(raw_dir, sprintf('%s_trial%03d_%s.mat', radio_id, trial_num, timestamp));

    samples_per_frame = 2^15;
    total_samples = round(sample_rate_hz * duration_s);

    rx = comm.SDRRTLReceiver( ...
        'CenterFrequency', center_freq_hz, ...
        'SampleRate', sample_rate_hz, ...
        'EnableTunerAGC', false, ...
        'TunerGain', gain_db, ...
        'FrequencyCorrection', 0, ...
        'SamplesPerFrame', samples_per_frame, ...
        'OutputDataType', 'single');

    cleanupObj = onCleanup(@() release(rx));

    iq = complex(zeros(total_samples, 1, 'single'));
    idx = 1;
    dropped_total = 0;

    %fprintf('Starting capture: %s\n', out_file);
    %fprintf('Center freq: %.0f Hz | Sample rate: %.0f S/s | Gain: %.1f dB\n', ...
    %    center_freq_hz, sample_rate_hz, gain_db);

    %DELAY FOR SINGLE USER
    fprintf('Starting capture: %s\n', out_file);
    fprintf('You have 5 seconds to get into position...\n');
    for countdown = 5:-1:1
        fprintf('%d...\n', countdown);
        pause(1); 
    end
    fprintf('LIVE! Key the radio now.\n');
    t0 = datetime('now');

    while idx <= total_samples
        try
            [data, len, lost] = rx();
        catch
            % Some installs return only [data, len]
            [data, len] = rx();
            lost = 0;
        end

        if len > 0
            ncopy = min(len, total_samples - idx + 1);
            iq(idx:idx+ncopy-1) = data(1:ncopy);
            idx = idx + ncopy;
        end

        dropped_total = dropped_total + lost;
    end

    t1 = datetime('now');

    iq = iq(1:idx-1);
    radio_id = char(radio_id);
    note = char(note);

    save(out_file, ...
        'iq', 'radio_id', 'trial_num', 'timestamp', ...
        'center_freq_hz', 'sample_rate_hz', 'gain_db', ...
        'duration_s', 'note', 't0', 't1', 'dropped_total', ...
        '-v7');

    log_file = fullfile(logs_dir, 'capture_log.csv');
    append_capture_log(log_file, string(out_file), radio_id, trial_num, center_freq_hz, sample_rate_hz, gain_db, duration_s, note);

    fprintf('Saved %d complex samples to %s\n', numel(iq), out_file);
end

function append_capture_log(log_file, file_path, radio_id, trial_num, center_freq_hz, sample_rate_hz, gain_db, duration_s, note)
    header = "timestamp,file,radio_id,trial,center_freq_hz,sample_rate_hz,gain_db,duration_s,note";
    row = sprintf('%s,"%s",%s,%d,%.0f,%.0f,%.1f,%.3f,"%s"\n', ...
        char(string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss'))), ...
        char(file_path), char(string(radio_id)), trial_num, ...
        center_freq_hz, sample_rate_hz, gain_db, duration_s, char(string(note)));

    if ~isfile(log_file)
        fid = fopen(log_file, 'w');
        fprintf(fid, '%s\n', header);
        fclose(fid);
    end

    fid = fopen(log_file, 'a');
    fprintf(fid, '%s', row);
    fclose(fid);
end