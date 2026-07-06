# Low-Cost Wi-Fi CSI Based Aerosol Sensing Prototype

This project implements a low-cost Wi-Fi CSI aerosol sensing prototype using Raspberry Pi, Nexmon CSI, MATLAB-style CSI feature extraction, lightweight machine learning, and MQTT-based edge reporting.

The current version has been extended from offline CSI processing to real-time edge inference on the Rx Raspberry Pi.

## Project Overview

The system uses Wi-Fi Channel State Information (CSI) to characterize aerosol-related changes in the wireless channel.

The prototype consists of three main nodes:

- **Tx Raspberry Pi**: generates Wi-Fi traffic using continuous ping packets
- **Rx Raspberry Pi**: captures Nexmon CSI, extracts CSI features, and performs local inference
- **AP Raspberry Pi**: works as the gateway and MQTT broker

The Rx node performs local feature extraction and local model inference. Only compact prediction results are published to the AP gateway through MQTT.

## System Pipeline

```text
Tx Wi-Fi traffic
        ↓
Rx Nexmon CSI capture
        ↓
CSI amplitude extraction
        ↓
128-packet windowing
        ↓
MATLAB-style feature extraction
        ↓
NumPy-based LSVM inference
        ↓
MQTT prediction publishing
        ↓
AP gateway
```

## Feature Extraction

Each prediction sample is generated from a 128-packet CSI window.

The feature vector has 250 dimensions:

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

The Python edge-side feature extraction follows the MATLAB offline processing style, including windowing, Hampel filtering, and moving average smoothing.

## Edge Deployment

Instead of deploying a scikit-learn joblib object directly to the Raspberry Pi, the LSVM model is exported as lightweight numerical parameters:

- standardization mean
- standardization scale
- LSVM weights
- LSVM bias
- class labels

The Rx Raspberry Pi performs inference using NumPy only. This avoids cross-platform compatibility issues between Windows/Docker and the 32-bit ARM Raspberry Pi.

## Completed Milestones

- Offline MATLAB CSI feature extraction
- Docker-based LSVM training
- LSVM parameter export for edge deployment
- CSV feature replay inference on Rx Pi
- pcap-based CSI decoding and inference
- MATLAB-style feature extraction on Rx Pi
- Live Nexmon CSI inference on Rx Pi
- MQTT-based prediction publishing to AP gateway

## Current Status

The real-time edge inference pipeline is working.

The Rx Raspberry Pi can process live Nexmon CSI packets, generate 250-dimensional features, perform local LSVM classification, and publish JSON prediction results to the AP gateway.

The current focus has shifted from deployment feasibility to improving real-time prediction stability and generalization accuracy.

## Repository Structure

```text
edge/
├── train_lsvm_export_params.py
├── train_lsvm_full_export_params.py
├── lsvm_param_publisher.py
├── pcap_lsvm_matlab_style_publisher.py
├── live_lsvm_matlab_style_publisher.py
└── start_live_csi.sh

docs/
├── system_architecture.md
└── edge_deployment_summary.md

gateway/
└── mqtt_notes.md

results/
└── live_inference_sample.md
```

## Future Work

- Improve real-time prediction stability
- Validate live CSI features against MATLAB-generated features
- Add newly collected live deployment data to the training set
- Evaluate trial-wise generalization instead of only random train/test split
- Add dashboard visualization on the AP gateway
