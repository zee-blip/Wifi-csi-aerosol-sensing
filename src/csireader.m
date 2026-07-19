function [data_csi_amp, data_csi_phase, pilot_csi_amp, pilot_csi_phase, timestamps_ts_sec, timestamps_ts_usec, raw_centred_csi, source_macs, rssis, frame_controls] = csireader(pcap_path, trial_name, BW)
   %% csireader.m
   %
   % read and plot CSI from UDPs created using the nexmon CSI extractor (nexmon.org/csi)
   % modify the configuration section to your needs
   % make sure you run >mex unpack_float.c before reading values from bcm4358 or bcm4366c0 for the first time
   %
   % the example.pcap file contains 4(core 0-1, nss 0-1) packets captured on a bcm4358
   %
   
   %% configuration
   if contains(pcap_path, 'realtime') && contains(trial_name, 'test_')
      FILE = "C:\Users\ljy13\Desktop\temp\" + trial_name + ".pcap";
   else
      FILE = pcap_path+ "/" + trial_name + ".pcap";% capture file
   end
   
   % FILE = "example.pcap";
   % device_name = split(trial_name, '_');
   % device_name = string(device_name(end-2));
   % device_name = split(device_name,'-');
   % device_name = string(device_name(1));
   if contains(trial_name, 'asus')
      disp("I sense the CSI extracted from the ASUS router. Setting the Chipset as 4366c0.");
      CHIP = '4366c0';
   else
      CHIP = '43455c0';          % wifi chip (possible values 4339, 4358, 43455c0, 4366c0)
   end
   
   [PILOT_SUBCARRIER, DATA_SUBCARRIER] = my_get_subcar_index(BW);
   
   %% read file
   HOFFSET = 16;           % header offset
   NFFT = BW*3.2;          % fft size
   p = readpcap();
   p.open(FILE);
   % n = min(length(p.all()),NPKTS_MAX);
   all_frames = p.all();
   n = length(all_frames);
   % n = length(p.all());
   
   try
   [user_mem, ~] = memory;
   FAST_READ = n*NFFT*8 < user_mem.MaxPossibleArrayBytes*0.45;
   clear user_mem;
   catch ME
      if ME.identifier == "MATLAB:memory:unsupported"
         FAST_READ = true;
      else
         FAST_READ = false;
      end
   end
   
   if ~FAST_READ
      disp("Fast pcap read disabled due to memory limits.")
      clear all_frames;
      p.from_start();
   end
   
   raw_centred_csi = single(complex(zeros(n,NFFT),0));
   timestamps_ts_sec = zeros(n,1);
   timestamps_ts_usec = zeros(n,1);
   k = 1;
   skipped_frames = [];
   payload_length = 0;
   % source_macs = strings(n, 1);
   % frame_controls = strings(n, 1);
   % rssis = zeros(n, 1);
   flag_buffs = uint32(zeros(n, 2));
   
   while (k <= n)
      if ~ FAST_READ
         f = p.next();
         test = f;
      else
         f = all_frames{k};
         if ~isstruct(f)
             break;
         end
         test = f.header;
      end
   
      % if isempty(f.header)
      if isempty(test)
         disp('no more frames');
         break;
      end
      
      if length(f.header) < 4 || f.header(4)-(HOFFSET-1)*4 ~= NFFT*4
         %         disp('skipped frame with incorrect size');
         skipped_frames = [skipped_frames,k];
         k = k + 1;
         continue;
      end
   
      payload = f.payload;
      header = f.header;
   
      if payload_length == 0
         payload_length = length(payload);
      end
      if length(payload) ~= payload_length
         break;
      end
   
      flag_buffs(k, :) = (payload(12:13));
      % source_macs(k) = source_mac_extract(payload(12:13));
      % [rssis(k), frame_controls(k)] = rssi_fc_extract(payload(12));
   
      H = payload(HOFFSET:HOFFSET+NFFT-1);
      if (strcmp(CHIP,'4339') || strcmp(CHIP,'43455c0'))
         Hout = typecast(H, 'int16');
      elseif (strcmp(CHIP,'4358'))
         Hout = unpack_float(int32(0), int32(NFFT), H);
      elseif (strcmp(CHIP,'4366c0'))
         Hout = unpack_float(int32(1), int32(NFFT), H);
      else
         disp('invalid CHIP');
         break;
      end
      Hout = reshape(Hout,2,[]).';
      cmplx = double(Hout(1:NFFT,1))+1j*double(Hout(1:NFFT,2));
      raw_centred_csi(k,:) = single(cmplx.');
      timestamps_ts_sec(k) = header(1);
      timestamps_ts_usec(k) = header(2);
      k = k + 1;
   end
   
   clear all_frames;
   
   raw_centred_csi = raw_centred_csi(1:k-1, :);
   timestamps_ts_sec = timestamps_ts_sec(1:k-1);
   timestamps_ts_usec = timestamps_ts_usec(1:k-1);
   flag_buffs = flag_buffs(1:k-1,:);
   raw_centred_csi(skipped_frames,:) = [];
   timestamps_ts_sec(skipped_frames) = [];
   timestamps_ts_usec(skipped_frames) = [];
   flag_buffs(skipped_frames,:) = [];
   
   [rssis, frame_controls] = rssi_fc_extract(flag_buffs);

   % Source MAC is not used for CSI feature extraction / ML.
   % Use dummy values to avoid parsing errors from abnormal packets.
   source_macs = strings(size(flag_buffs, 1), 1);
   
   raw_centred_csi = fftshift(raw_centred_csi, 2);
   p.close();
   
   %% Outlier filtering
   subcar_offset = size(raw_centred_csi, 2)/2 + 1;
   raw_centred_csi = raw_centred_csi(:, union(DATA_SUBCARRIER, PILOT_SUBCARRIER)+subcar_offset);
   data_csi_amp = [];
   data_csi_phase = [];
   pilot_csi_amp = [];
   pilot_csi_phase = [];
   
   disp("Skipped " + length(skipped_frames) + " frames.");
   
   return; 
   
   %% No longed used code below
   % [effective_csi, timestamps_ts_sec, timestamps_ts_usec] = my_csi_remove_outlier(effective_csi, 'none', timestamps_ts_sec, timestamps_ts_usec);
   clear raw_centred_csi;
   transformed_phase = my_phase_transform(raw_centred_csi);
   
   % CSI Subcarrier Selection
   
   % unwrapped_phase = unwrap(angle(csi_centred)')';
   % csi_centred = abs(csi_centred).*exp(1i*unwrapped_phase);
   subcar_offset = size(raw_centred_csi, 2)/2 + 1;
   % Unused subcars at the centre
   if BW == 20
      centre_Unused = 1;
   elseif BW == 40 || BW == 80
      centre_Unused = 3;
      subcar_offset = subcar_offset + 1;
   end
   shifted_data_subcar = [DATA_SUBCARRIER(DATA_SUBCARRIER < 0), DATA_SUBCARRIER(DATA_SUBCARRIER > 0) - centre_Unused];
   shifted_pilot_subcar = [PILOT_SUBCARRIER(PILOT_SUBCARRIER < 0), PILOT_SUBCARRIER(PILOT_SUBCARRIER > 0) - centre_Unused];
   data_csi = raw_centred_csi(:,shifted_data_subcar+subcar_offset);
   pilot_csi = raw_centred_csi(:,shifted_pilot_subcar+subcar_offset);
   
   
   clear raw_centred_csi;
   data_csi_amp = abs(data_csi);
   data_csi_phase = transformed_phase(:,shifted_data_subcar+subcar_offset);
   clear data_csi;
   pilot_csi_amp = abs(pilot_csi);
   pilot_csi_phase = transformed_phase(:,shifted_pilot_subcar+subcar_offset);
   clear pilot_csi transformed_phase;
   % clear temp;
   
   end
   
   %% Local helpers
   % A function to extract the source MAC address from the hex payload data
   function [output] = source_mac_extract(payload)
      output = strings(size(payload,1),6);
      word1 = dec2hex(payload(:,1));
      word2 = dec2hex(payload(:,2));
      % word1 = buff(12, :);
      % word2 = buff(13, :);
      output(:,1) = word1(:,3:4);
      output(:,2) = word1(:,1:2);
      output(:,3) = word2(:,7:8);
      output(:,4) = word2(:,5:6);
      output(:,5) = word2(:,3:4);
      output(:,6) = word2(:,1:2);
      output = join(output, ':');
   end
   
   
   % A function that extracts the RSSI and frame control information
   function [rssi, fc] = rssi_fc_extract(payload)
   
   n = size(payload, 1);
   
   rssi = zeros(n, 1, "int8");
   fc = zeros(n, 1, "uint8");
   
   for i = 1:n
   
       try
           buff = dec2hex(swapbytes(payload(i, :)));
   
           % 如果这一行太短，跳过
           if size(buff, 2) < 4
               rssi(i) = int8(0);
               fc(i) = uint8(0);
               continue;
           end
   
           word = buff;
   
           rssi(i) = typecast(uint8(hex2dec(word(1,1:2))), "int8");
           fc(i) = uint8(hex2dec(word(1,3:4)));
   
       catch
           rssi(i) = int8(0);
           fc(i) = uint8(0);
       end
   
   end
   
   end