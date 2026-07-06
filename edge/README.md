@
# Edge Deployment

This folder contains the Raspberry Pi edge-side scripts for Wi-Fi CSI based aerosol sensing and classification.

The edge pipeline has been extended from offline feature replay to recorded pcap replay and real-time Nexmon CSI inference.

## Current Status

The edge deployment pipeline is working.

Completed milestones:

- LSVM model training in Docker
- LSVM parameter export for Raspberry Pi deployment
- CSV feature replay inference on Rx Pi
- pcap-based Nexmon CSI decoding and inference on Rx Pi
- MATLAB-style 250-dimensional feature extraction on Rx Pi
- Live Nexmon CSI inference on Rx Pi
- MQTT prediction publishing from Rx Pi to AP gateway

The Rx Raspberry Pi is not only forwarding data. It performs local CSI feature extraction and local model inference. Only the prediction result is sent to the AP gateway.

## Edge Inference Pipeline

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
MQTT publish to AP gateway
