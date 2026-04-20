function survey_rt29(center_freq_hz, sample_rate_hz, gain_db)
% Live spectrum survey for finding the RT29 signal.
% Uses the newer spectrumAnalyzer object instead of dsp.SpectrumAnalyzer.
%
% Example:
%   survey_rt29(462515000, 2.4e6, 35)

    if nargin < 1, center_freq_hz = 462515000; end
    if nargin < 2, sample_rate_hz = 2.4e6; end
    if nargin < 3, gain_db = 35; end

    rx = comm.SDRRTLReceiver( ...
        'CenterFrequency', center_freq_hz, ...
        'SampleRate', sample_rate_hz, ...
        'EnableTunerAGC', false, ...
        'TunerGain', gain_db, ...
        'FrequencyCorrection', 0, ...
        'SamplesPerFrame', 4096, ...
        'OutputDataType', 'single');

    % For complex baseband input, use a two-sided spectrum.
    % Use FrequencyOffset to shift the x-axis to absolute RF frequency.
    sa = spectrumAnalyzer( ...
        'Name', 'RT29 Survey Spectrum', ...
        'Title', 'RT29 Survey Spectrum', ...
        'InputDomain', 'time', ...
        'SampleRate', sample_rate_hz, ...
        'PlotAsTwoSidedSpectrum', true, ...
        'SpectrumType', 'power-density', ...
        'ViewType', 'spectrum-and-spectrogram', ...
        'FrequencySpan', 'full', ...
        'FrequencyOffset', center_freq_hz, ...
        'ShowLegend', false, ...
        'ShowGrid', true);

    cleanupObj = onCleanup(@() cleanup(rx, sa)); %#ok<NASGU>

    fprintf('Survey running.\n');
    fprintf('Center frequency: %.0f Hz | Sample rate: %.0f S/s | Gain: %.1f dB\n', ...
        center_freq_hz, sample_rate_hz, gain_db);
    fprintf('Close the spectrum window or press Ctrl+C to stop.\n');

    while true
        try
            [x, len, lost] = rx();
        catch
            try
                [x, len] = rx();
                lost = 0;
            catch
                x = rx();
                len = numel(x);
                lost = 0;
            end
        end

        if len > 0
            sa(x(1:len));
        end

        if lost > 0
            fprintf('Warning: lost %d samples\n', lost);
        end

        drawnow limitrate;

        % Break if user closes the scope
        if ~isOpen(sa)
            break;
        end
    end
end

function cleanup(rx, sa)
    release(rx);
    release(sa);
end