# Gateway and MQTT Integration

This folder contains the gateway-side documentation for receiving Wi-Fi CSI edge inference results through MQTT.

In the current prototype, the AP Raspberry Pi works as the network gateway and MQTT broker. The Rx Raspberry Pi performs local CSI feature extraction and local LSVM inference, then publishes compact prediction results to the AP gateway.

## Gateway Role

The AP Raspberry Pi is responsible for:

- providing network connectivity for the sensing system
- running the Mosquitto MQTT broker
- receiving prediction messages from the Rx edge node
- supporting future dashboard visualization and logging

The gateway does not process raw CSI data. Raw CSI is handled locally on the Rx Raspberry Pi.

## Implemented Workflow

```text
Tx Raspberry Pi
        ↓
generates Wi-Fi traffic

Rx Raspberry Pi
        ↓
captures live Nexmon CSI
extracts 250-dimensional CSI features
runs local LSVM inference
publishes prediction JSON through MQTT

AP Raspberry Pi
        ↓
runs Mosquitto broker
receives prediction messages
can be extended with dashboard and logging
```

## MQTT Broker

The Mosquitto broker runs on the AP Raspberry Pi.

```text
Broker IP: 10.42.1.1
Port: 1883
Main topic: csi/aerosol/pred
```

## Main MQTT Topic

| Topic | Direction | Current Status | Description |
|---|---|---|---|
| `csi/aerosol/pred` | Rx → AP | Implemented | Real-time aerosol prediction result |
| `csi/aerosol/status` | Rx → AP | Planned | Rx device status and heartbeat |
| `csi/aerosol/cmd` | AP → Rx | Planned | Optional control command from gateway |
| `csi/aerosol/alert` | AP/User | Planned | Optional alert message |

The implemented topic in the current prototype is:

```text
csi/aerosol/pred
```

## Subscribe on AP

On the AP Raspberry Pi, prediction messages can be received using:

```bash
mosquitto_sub -h localhost -t csi/aerosol/pred -v
```

Example output:

```text
csi/aerosol/pred {"timestamp":"2026-06-18T22:05:47.252189+00:00","seq":119,"pred_class":1,"confidence":0.464,"model":"lsvm_numpy_params_live_matlab_style","latency_ms":5.535,"window_time_ms":391.204,"device":"rx-pi","source":"live_nexmon_csi","feature_dim":250,"window_packets":128}
```

## Example Prediction Payload

```json
{
  "timestamp": "2026-06-18T22:05:47.252189+00:00",
  "seq": 119,
  "pred_class": 1,
  "confidence": 0.464,
  "model": "lsvm_numpy_params_live_matlab_style",
  "latency_ms": 5.535,
  "window_time_ms": 391.204,
  "device": "rx-pi",
  "source": "live_nexmon_csi",
  "feature_dim": 250,
  "window_packets": 128
}
```

## Field Description

| Field | Description |
|---|---|
| `timestamp` | UTC timestamp of the prediction |
| `seq` | Prediction sequence number |
| `pred_class` | Predicted aerosol class |
| `confidence` | Relative confidence derived from LSVM decision scores |
| `model` | Model or inference pipeline name |
| `latency_ms` | Local inference latency after feature extraction |
| `window_time_ms` | Time required to collect one CSI window |
| `device` | Edge device name |
| `source` | CSI data source |
| `feature_dim` | Feature vector dimension |
| `window_packets` | Number of CSI packets per feature window |

## Current Status

Completed:

- Mosquitto broker setup on AP Pi
- MQTT communication between Rx Pi and AP Pi
- Real-time prediction publishing from Rx Pi
- AP-side subscription to `csi/aerosol/pred`
- JSON-based edge inference result format

In progress / future work:

- persistent logging of MQTT prediction results
- dashboard visualization on the AP gateway
- optional status heartbeat topic
- optional command and alert topics

## Notes

The gateway is intentionally lightweight. The Rx Pi performs the sensing and inference workload locally, while the AP Pi receives and organizes the prediction results.

This design reduces network load because raw CSI data is not transmitted to the gateway.
