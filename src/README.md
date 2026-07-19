# Source Code

This folder contains reusable MATLAB source files for Wi-Fi CSI parsing, preprocessing, and feature extraction.

## Main Files

| File | Purpose |
|---|---|
| `readpcap.m` | Read Nexmon CSI pcap files |
| `csireader.m` | Parse CSI frame data |
| `my_iterate_csi.m` | Iterate through CSI packets/frames |
| `my_get_subcar_index.m` | Get effective CSI subcarrier indices |
| `my_csi_output_to_combined.m` | Convert CSI output into combined matrix format |
| `my_combine_ts_sec_usec.m` | Combine timestamp seconds and microseconds |
| `extract_aerosol_features_paper_style.m` | Extract aerosol sensing features using the paper-style processing pipeline |
| `unpack_float.c` | C source file for MATLAB MEX support |

## Notes

The compiled `unpack_float.mexw64` file is not included in the repository because it is platform-specific. It should be rebuilt locally if required.

These source functions support the offline MATLAB pipeline for generating CSI amplitude features and preparing machine learning datasets.
