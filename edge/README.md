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
```

## Feature Format

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

The edge-side feature extraction follows the MATLAB offline processing style, including windowing, Hampel filtering, and moving average smoothing.

## Model Deployment

The LSVM model is not deployed as a scikit-learn joblib object.

Instead, the model is exported as lightweight numerical parameters:

- standardization mean
- standardization scale
- LSVM weights
- LSVM bias
- class labels

This avoids cross-platform compatibility issues between Windows/Docker and the 32-bit ARM Raspberry Pi.

Model files:

```text
models/lsvm_edge_params.npz
models/lsvm_edge_params_v2.npz
```

## Main Scripts

| Script | Purpose |
|---|---|
| `train_lsvm_export_params.py` | Train LSVM on sample feature data and export edge parameters |
| `train_lsvm_full_export_params.py` | Train LSVM on the full feature dataset and export v2 parameters |
| `lsvm_param_publisher.py` | Replay pre-extracted CSV features and publish predictions via MQTT |
| `pcap_lsvm_matlab_style_publisher.py` | Decode recorded Nexmon CSI pcap files, extract features, run LSVM inference, and publish results |
| `live_lsvm_matlab_style_publisher.py` | Capture live Nexmon CSI, extract features in real time, run LSVM inference, and publish results |
| `start_live_csi.sh` | Configure Nexmon CSI on the Rx Raspberry Pi for live inference |

## Live CSI Setup

On the Rx Raspberry Pi:

```bash
cd ~/Wifi-csi-aerosol-sensing
chmod +x edge/start_live_csi.sh
./edge/start_live_csi.sh
```

Verify that CSI packets are arriving:

```bash
sudo tcpdump -i wlan0 udp port 5500 -c 5
```

Expected CSI packet format:

```text
IP 10.10.10.10.5500 > 255.255.255.255.5500: UDP, length 1042
```

## Live Inference

After enabling Nexmon CSI, run:

```bash
sudo python3 edge/live_lsvm_matlab_style_publisher.py --broker 10.42.1.1 --topic csi/aerosol/pred
```

The script outputs JSON prediction messages such as:

```json
{
  "seq": 0,
  "pred_class": 3,
  "confidence": 0.906,
  "model": "lsvm_numpy_params_live_matlab_style",
  "latency_ms": 11.522,
  "window_time_ms": 987.448,
  "device": "rx-pi",
  "source": "live_nexmon_csi",
  "feature_dim": 250,
  "window_packets": 128
}
```

## pcap Replay Inference

For recorded pcap verification:

```bash
python3 edge/pcap_lsvm_matlab_style_publisher.py --pcap pcap_test/test8-5.pcap --broker 10.42.1.1 --topic csi/aerosol/pred --limit_windows 20 --interval 0.1
```

This is useful for checking whether the pcap-based feature extraction and edge inference pipeline are consistent with the offline MATLAB processing pipeline.

## MQTT Output

The Rx Pi publishes prediction messages to:

```text
csi/aerosol/pred
```

The AP Pi can subscribe using:

```bash
mosquitto_sub -h localhost -t csi/aerosol/pred -v
```

## Notes

- `start_live_csi.sh` enables live CSI extraction but does not save pcap files.
- The original pcap recording workflow uses `tcpdump -i wlan0 dst port 5500 -vv -w xxx.pcap`.
- The live inference script directly reads CSI packets from `wlan0`.
- The confidence value is derived from LSVM decision scores and should be treated as a relative confidence indicator, not a calibrated probability.
- The real-time feature pipeline uses a causal approximation for online filtering and smoothing, while the offline MATLAB pipeline can use the full recorded sequence.

## Current Limitations

The real-time inference pipeline is functional, but live prediction stability still depends on deployment conditions such as device placement, environment consistency, human motion, Tx traffic stability, and aerosol distribution.

Current work focuses on improving real-time generalization by comparing:

- training pcap replay results
- newly recorded live pcap replay results
- real-time live inference results

## Next Steps

- Record additional live CSI pcap data under controlled class conditions
- Compare live feature distributions with MATLAB offline features
- Add deployment-condition data to the training set
- Evaluate trial-wise generalization instead of only random train/test split
- Add gateway-side logging and dashboard visualization
