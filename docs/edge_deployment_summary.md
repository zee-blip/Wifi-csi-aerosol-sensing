# Edge Deployment Summary

This document summarizes the edge deployment progress of the Wi-Fi CSI based aerosol sensing prototype.

## Objective

The goal is to move beyond offline MATLAB classification and deploy a lightweight inference pipeline on the Rx Raspberry Pi.

The Rx node captures Wi-Fi CSI, extracts CSI-based features locally, performs model inference on-device, and publishes prediction results to the AP gateway via MQTT.

## Completed Milestones

### 1. Offline MATLAB Feature Extraction

Raw Nexmon CSI pcap files were processed in MATLAB to generate CSI-based feature vectors.

Each feature sample is generated from a 128-packet CSI window and contains 250 dimensions:

- 242 CSI amplitude features from effective OFDM subcarriers
- 8 statistical features:
  - mean
  - max
  - min
  - standard deviation
  - variance
  - MAD
  - skewness
  - kurtosis

The full dataset contains:

- `X_all_features.csv`: 84348 × 250
- `Y_all_labels.csv`: 84348 × 1

The dataset is balanced across six aerosol-related classes.

### 2. Docker-based LSVM Training

The LSVM model was trained in a Docker-controlled environment on Windows.

Instead of deploying a scikit-learn joblib object, the trained LSVM model is exported as lightweight numerical parameters:

- standardization mean
- standardization scale
- LSVM weights
- LSVM bias
- class labels

This avoids cross-platform compatibility issues between Windows/Docker and the 32-bit ARM Raspberry Pi.

### 3. CSV Feature Replay on Rx Pi

The first edge deployment test used pre-extracted CSV features.

The Rx Raspberry Pi loaded the LSVM parameters, performed local NumPy-based inference, and published prediction results to the AP gateway via MQTT.

### 4. pcap Replay Inference on Rx Pi

The second stage replaced CSV feature input with recorded Nexmon CSI pcap files.

The Rx Pi can:

1. read recorded pcap files,
2. decode UDP 5500 Nexmon CSI packets,
3. extract 242-subcarrier CSI amplitude,
4. generate 250-dimensional MATLAB-style features,
5. perform LSVM inference locally,
6. publish prediction JSON messages through MQTT.

### 5. Live Nexmon CSI Inference

The final real-time stage captures live CSI directly from `wlan0`.

The live pipeline is:

```text
Tx Wi-Fi traffic
        ↓
Rx Nexmon CSI capture
        ↓
128-packet CSI window
        ↓
MATLAB-style 250-dimensional feature extraction
        ↓
NumPy-based LSVM inference
        ↓
MQTT publish to AP gateway
```

The Rx Pi is not only forwarding data. It performs local feature extraction and local model inference. Only the prediction result is sent to the gateway.

## Current Status

The real-time edge inference pipeline is working.

The Rx Raspberry Pi can process live Nexmon CSI packets, generate 250-dimensional features, run local LSVM inference, and publish prediction results to the AP gateway.

The current focus has shifted from deployment feasibility to improving real-time prediction stability and generalization accuracy.

## Future Work

- Validate live CSI features against MATLAB-generated features
- Add newly collected live deployment data to the training set
- Improve model robustness under different deployment conditions
- Evaluate trial-wise generalization instead of only random train/test split
- Add AP-side dashboard visualization
