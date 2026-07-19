function timestamp = my_combine_ts_sec_usec(timestamp_sec, timestamp_us)

% Combine seconds and microseconds into one timestamp vector
timestamp = double(timestamp_sec) + double(timestamp_us) * 1e-6;

% Normalize timestamp to start from 0
if ~isempty(timestamp)
    timestamp = timestamp - timestamp(1);
end

end