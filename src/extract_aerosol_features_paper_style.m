function [X, Y] = extract_aerosol_features_paper_style(combined_csi, Nmax)

X = [];
Y = strings(0,1);

win = 128;
hop = 128;

for i = 1:numel(combined_csi)

    label = string(combined_csi(i).type_name);
    fprintf("Extracting Class %s...\n", label);

    csi_i = combined_csi(i).raw_centred_csi;
    n_i = min(Nmax, size(csi_i, 1));

    amp_i = abs(csi_i(1:n_i, :));

    % Windowing: average every 128 packets
    nWin = floor(size(amp_i, 1) / win);
    Awin = zeros(nWin, size(amp_i, 2), "single");

    for w = 1:nWin
        idx1 = (w-1)*hop + 1;
        idx2 = idx1 + win - 1;
        Awin(w, :) = mean(amp_i(idx1:idx2, :), 1);
    end

    % Hampel filter for each subcarrier
    for sc = 1:size(Awin, 2)
        Awin(:, sc) = hampel(Awin(:, sc), 3);
    end

    % Moving average smoothing
    Awin = movmean(Awin, 5, 1);

    % Feature computation: 242 subcarriers + 8 statistical features = 250
    for w = 1:size(Awin, 1)

        subcarrier_features = Awin(w, :);

        stat_features = [
            mean(Awin(w, :)), ...
            max(Awin(w, :)), ...
            min(Awin(w, :)), ...
            std(Awin(w, :)), ...
            var(Awin(w, :)), ...
            mad(Awin(w, :), 1), ...
            skewness(Awin(w, :)), ...
            kurtosis(Awin(w, :))
            ];

        feature = [subcarrier_features, stat_features];

        X = [X; feature];
        Y = [Y; label];

    end
end

Y = categorical(Y);

end