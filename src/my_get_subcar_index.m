function [PILOT_SUBCARRIER, DATA_SUBCARRIER] = my_get_subcar_index(BW)

switch BW

    case 20
        DATA_SUBCARRIER = [-28:-1 1:28];

    case 40
        DATA_SUBCARRIER = [-58:-2 2:58];

    case 80
        DATA_SUBCARRIER = [-122:-2 2:122];

    otherwise
        error("Unsupported bandwidth");

end

PILOT_SUBCARRIER = [];

end