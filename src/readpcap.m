classdef readpcap < handle
    %READPCAP Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        fid;
        global_header;
        prev_len;
    end
    
    methods
        function open(obj, filename)
            obj.fid = fopen(filename);
            
            % should be 0xA1B2C3D4
            obj.global_header.magic_number = fread(obj.fid, 1, '*uint32');

            % major version number
            obj.global_header.version_major = fread(obj.fid, 1, '*uint16');

            % minor version number
            obj.global_header.version_minor = fread(obj.fid, 1, '*uint16');

            % GMT to local correction
            obj.global_header.thiszone = fread(obj.fid, 1, '*int32');

            % accuracy of timestamps
            obj.global_header.sigfigs = fread(obj.fid, 1, '*uint32');

            % max length of captured packets, in octets
            obj.global_header.snaplen = fread(obj.fid, 1, '*uint32');

            % data link type
            obj.global_header.network = fread(obj.fid, 1, '*uint32');
        end
        
        function frame = next(obj)
            % timestamp seconds
            % frame.header.ts_sec = fread(obj.fid, 1, '*uint32');

            % timestamp microseconds
            % frame.header.ts_usec = fread(obj.fid, 1, '*uint32');

            % number of octets of packet saved in file
            % frame.header.incl_len = fread(obj.fid, 1, '*uint32');

            % actual length of packet
            % frame.header.orig_len = fread(obj.fid, 1, '*uint32');

            frame.header = fread(obj.fid, 4, '*uint32');
            % if isempty(frame.header.incl_len)
            if isempty(frame.header)
                frame = [];
                return;
            end
            
            % frame.header.ts_sec = test(1);
            % frame.header.ts_usec = test(2);
            % frame.header.incl_len = test(3);
            % frame.header.orig_len = test(4);

            % packet data
            if (mod(frame.header(3),4)==0)
                frame.payload = fread(obj.fid, frame.header(3)/4, '*uint32');
            else
                frame.payload = fread(obj.fid, frame.header(3), '*uint8');
            end
        end
        
        function frames = next_fast(obj)
            % assert(mod(incl_len,4)==0, "Fast pcap reading not supported on this format yet.");
            i = 1;
            frames = cell(i);
            while true
                frames{i}.header = fread(obj.fid, 4, '*uint32');

                % if isempty(frame.header.incl_len)
                if isempty(frames{i}.header)
                    % frame = [];
                    break;
                end

                if (mod(frames{i}.header(3),4)==0)
                    frames{i}.payload = fread(obj.fid, frames{i}.header(3)/4, '*uint32');
                else
                    frames{i}.payload = fread(obj.fid, frames{i}.header(3), '*uint8');
                end
                
                i = i + 1;
            end
            frames = (frames(1:i-1));
            % frames = cellfun(@pcap_mat2frame, frames);
        end

        function from_start(obj)
            fseek(obj.fid, 24, -1);
        end
        
        function frames = all(obj)
            obj.from_start();
            try
                % assert(0);
                frames = obj.next_fast();
            catch ME
                i = 1;
                frames = cell(1);
                frame = obj.next();
                if isempty(frame)
                    return;
                end
                while true
                    if isempty(frame)
                        break;
                    end

                    frames{i} = frame;
                    i = i + 1;

                    frame = obj.next();
                end
            end
        end
        
        function close(obj)
            fclose(obj.fid);
        end
    end
    
end


function frame = pcap_mat2frame(input)
    frame.header.ts_sec = input.header(1);
    frame.header.ts_usec = input.header(2);
    frame.header.incl_len = input.header(3);
    frame.header.orig_len = input.header(4);
    frame.payload = input.payload;
    frame = {frame};
end