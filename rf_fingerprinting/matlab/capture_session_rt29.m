function capture_session_rt29(center_freq_hz, sample_rate_hz, gain_db, duration_s, n_trials)
% Guided capture session:
% 1 baseline
% then alternating radio_A / radio_B captures

    if nargin < 1, center_freq_hz = 462562500; end
    if nargin < 2, sample_rate_hz = 2.0e6; end
    if nargin < 3, gain_db = 20; end
    if nargin < 4, duration_s = 12; end
    if nargin < 5, n_trials = 5; end

    fprintf('\n=== RT29 Fingerprinting Capture Session ===\n');
    fprintf('Center frequency: %.0f Hz\n', center_freq_hz);
    fprintf('Sample rate:      %.0f S/s\n', sample_rate_hz);
    fprintf('Gain:             %.1f dB\n', gain_db);
    fprintf('Duration:         %.1f s\n', duration_s);
    fprintf('Trials/radio:     %d\n\n', n_trials);

    input('Press Enter to capture baseline noise...', 's');
    capture_trial_rt29("baseline_noise", 1, center_freq_hz, sample_rate_hz, gain_db, duration_s, "noise_floor");

    for k = 1:n_trials
        fprintf('\nTrial set %d of %d\n', k, n_trials);

        input('Key RADIO A when ready, then press Enter...', 's');
        capture_trial_rt29("radio_A", k, center_freq_hz, sample_rate_hz, gain_db, duration_s, "session_capture");

        input('Key RADIO B when ready, then press Enter...', 's');
        capture_trial_rt29("radio_B", k, center_freq_hz, sample_rate_hz, gain_db, duration_s, "session_capture");
    end

    fprintf('\nSession complete.\n');
end