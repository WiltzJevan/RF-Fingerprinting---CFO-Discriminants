function survey_rt29(center_freq_hz, sample_rate_hz, gain_db)
% Live spectrum survey for finding the RT29 signal.

    if nargin < 1, center_freq_hz = 462562500; end
    if nargin < 2, sample_rate_hz = 2.0e6; end
    if nargin < 3, gain_db = 20; end

    rx = comm.SDRRTLReceiver( ...
        'CenterFrequency', center_freq_hz, ...
        'SampleRate', sample_rate_hz, ...
        'EnableTunerAGC', false, ...
        'TunerGain', gain_db, ...
        'FrequencyCorrection', 0, ...
        'SamplesPerFrame', 4096, ...
        'OutputDataType', 'single');

    sa = dsp.SpectrumAnalyzer( ...
        'SampleRate', sample_rate_hz, ...
        'Title', 'RT29 Survey Spectrum', ...
        'SpectrumType', 'Power density', ...
        'ShowLegend', false);

    cleanupObj = onCleanup(@() cleanup(rx, sa));

    fprintf('Survey running. Close the spectrum window or Ctrl+C to stop.\n');

    while true
        try
            [x, len] = rx();
        catch
            [x, len, ~] = rx();
        end

        if len > 0
            sa(x(1:len));
        end

        drawnow limitrate;
        if ~isvalid(sa)
            break;
        end
    end
end

function cleanup(rx, sa)
    release(rx);
    release(sa);
end