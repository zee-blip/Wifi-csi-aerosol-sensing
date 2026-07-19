%% A function that converts the csi output buff to a combined csi seperated
% by the trial type. 
function [combined_csi] = my_csi_output_to_combined(csi_buff)

type_names = unique(string({csi_buff.type_name}));
test_name = csi_buff(1).test_name;
combined_csi = struct();
csi_field_names = fieldnames(csi_buff);

for type = 1:length(type_names)
    combined_csi(type).type_name = string(type_names(type));
    combined_csi(type).test_name = test_name;
    for field = 1:length(csi_field_names)
        if isnumeric(csi_buff(1).(string(csi_field_names(field))))
            combined_csi(type).(string(csi_field_names(field))) = [];
        end
    end
    combined_csi(type).source_macs = [];
    for count = 1:length(csi_buff)
        if strcmp(combined_csi(type).type_name, csi_buff(count).type_name)
            for field = 1:length(csi_field_names)
                if (isnumeric(csi_buff(count).(string(csi_field_names(field)))) ... 
                        || strcmp(csi_field_names(field), 'source_macs') || ...
                        strcmp(csi_field_names(field), 'frame_control'))
                    combined_csi(type).(string(csi_field_names(field))) = ...
                        [combined_csi(type).(string(csi_field_names(field))); ...
                        csi_buff(count).(string(csi_field_names(field)))];
                end
            end
        end
    end
end

return;