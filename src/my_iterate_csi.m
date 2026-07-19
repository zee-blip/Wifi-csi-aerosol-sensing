%% Iterates throught the CSI data folder and read everything to structs

%% Init
close all;
clearvars;

% Variables to be configured for each experiment as in ../pcap_files
test_name = "test10"; % CHANGE THIS VALUE FOR EACH EXPERIMENT
BW = 80; % BW config as per the WiFi config
pcap_src = "../pcap/" + test_name + "/"; % If this is different for your setup, change it accordingly. 

% No need to change the following usually
pcap_files = dir(pcap_src);
num_files = size(pcap_files);
num_files = num_files(1);
% figure_dst = "../figures/" + test_name + "/"; 
var_dst = "../vars/" + test_name + "/";

%% Read .pcap file list
limit = num_files;
for trial = 1:limit
    if (pcap_files(trial).bytes == 0)
        num_files = num_files - 1;
    end
end

file_names = strings(num_files, 1);
m = 1;
for trial = 1:limit
    if (pcap_files(trial).bytes ~= 0)
        file_names(m) = string(pcap_files(trial).name);
        trial_name = split(file_names(m), '.');
        if strcmp(trial_name(end), 'pcap')
            trial_names(m) = trial_name(1);
            m = m+1;
        end
    end
end
type_names = squeeze(split(trial_names, '-'));
type_names = unique(type_names(:,1));
num_types = length(type_names);

%% Init the csi output buff struct for all the CSI packets from .pcap files
combined_csi = struct();
for trial = 1:m-1
   combined_csi(trial).type_name = [];
   combined_csi(trial).test_name = test_name;
   %     csi_output_buff(trial).data_csi_amp = [];
   %     csi_output_buff(trial).data_csi_phase = [];
   %     csi_output_buff(trial).pilot_csi_amp = [];
   %     csi_output_buff(trial).pilot_csi_phase = [];
   combined_csi(trial).timestamp_sec = [];
   combined_csi(trial).timestamp_us = [];
   combined_csi(trial).raw_centred_csi = [];
   combined_csi(trial).source_macs = [];
   combined_csi(trial).rssi = [];
   combined_csi(trial).frame_control = [];
end

%% Read each .pcap files (trials)
empty_inds = [];
for trial = 1:m-1
   trial_name = trial_names(trial);
   [~, ~, ~, ~, timestamp_sec, timestamp_us, combined_csi(trial).raw_centred_csi, ...
      combined_csi(trial).source_macs, combined_csi(trial).rssi, ...
      combined_csi(trial).frame_control] = my_call_script(pcap_src, trial_name, BW);
   type_name = split(trial_name, '-');
   type_name = string(type_name(2));
   if isempty(combined_csi(trial).raw_centred_csi)
      empty_inds = [empty_inds, trial];
      continue;
   end
   combined_csi(trial).type_name = type_name;
   combined_csi(trial).trial_name = trial_name;
   %     csi_output_buff(trial).data_csi_amp = data_csi_amp;
   %     csi_output_buff(trial).data_csi_phase = data_csi_phase;
   %     csi_output_buff(trial).pilot_csi_amp = pilot_csi_amp;
   %     csi_output_buff(trial).pilot_csi_phase = pilot_csi_phase;
%    combined_csi(trial).timestamp_sec = timestamp_sec;
%    combined_csi(trial).timestamp_us = timestamp_us;
   combined_csi(trial).timestamp = my_combine_ts_sec_usec(timestamp_sec, timestamp_us);
   clear timestamp_sec timestamp_us;
end
combined_csi(empty_inds) = [];
% return;

%% Save the combined_csi 
% mkdir(var_dst);
if numel(combined_csi) > 1
    combined_csi = my_csi_output_to_combined(combined_csi);
end
% combined_csi_obj = combined_csi_class.read_combined_csi_struct(combined_csi);
% save(var_dst+"vars", "combined_csi_obj");
% return

%% Moved my_call_script here, since its only used by this script.
% This is a wrapper function for parallel execution. 
function [data_csi_amp, data_csi_phsae, pilot_csi_amp, pilot_csi_phase, timestamp_sec, timestamp_us, raw_centred_csi, source_macs, rssis, frame_controls] = my_call_script(pcap_path, trial_name, BW)
    [~, ~, ~, ~, timestamp_sec, timestamp_us, raw_centred_csi, source_macs, rssis, frame_controls] = csireader(pcap_path, trial_name, BW);
    data_csi_amp = [];
    data_csi_phsae = [];
    pilot_csi_amp = [];
    pilot_csi_phase = [];
end
    