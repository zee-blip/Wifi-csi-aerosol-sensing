# System Architecture

## Hardware Roles

### Tx Raspberry Pi

The Tx node generates Wi-Fi traffic, typically using continuous ping packets.

Example:

```bash
ping 10.42.0.1
```

### Rx Raspberry Pi

The Rx node is the edge sensing and inference device.

It runs Nexmon CSI and performs local inference.

Responsibilities:

- capture live Nexmon CSI packets
- decode CSI amplitude from 242 effective subcarriers
- generate 250-dimensional CSI-based feature vectors
- load LSVM numerical parameters
- perform local NumPy-based inference
- publish prediction results via MQTT

### AP Raspberry Pi

The AP node works as the gateway and MQTT broker.

Responsibilities:

- provide network connectivity
- run Mosquitto broker
- receive prediction JSON messages from Rx
- optionally host dashboard or logging services

## Network Topology

```text
Tx Pi  --Wi-Fi-->  AP Pi / Router  <--Ethernet-->  Rx Pi
                                  MQTT broker
```

The Rx Pi uses:

- `wlan0` for Nexmon CSI capture
- `eth0` for management and MQTT communication

## MQTT Topic

```text
csi/aerosol/pred
```

## Example Prediction Message

```json
{
  "timestamp": "2026-06-xxTxx:xx:xxZ",
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

## Main Edge Scripts

```text
edge/train_lsvm_full_export_params.py
edge/pcap_lsvm_matlab_style_publisher.py
edge/live_lsvm_matlab_style_publisher.py
edge/start_live_csi.sh
```
