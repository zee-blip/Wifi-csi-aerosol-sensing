# Gateway Closed Loop

This folder contains the gateway-side implementation for receiving edge inference results through MQTT, visualizing aerosol predictions, and logging system status.

The gateway is designed to connect the Raspberry Pi edge inference node with a dashboard or monitoring system.

## Planned Workflow

```text
Rx Raspberry Pi edge inference
→ MQTT publish
→ Gateway MQTT broker
→ Dashboard visualization
→ Logging and alert
```

## MQTT Topics

| Topic | Direction | Description |
|---|---|---|
| `csi/aerosol/pred` | Rx → Gateway | Aerosol prediction result |
| `csi/aerosol/status` | Rx → Gateway | Rx device status |
| `csi/aerosol/cmd` | Gateway → Rx | Control command from gateway |
| `csi/aerosol/alert` | Rx/Gateway → User | Alert message |

## Example Prediction Payload

```json
{
  "timestamp": "2026-06-03T16:30:00",
  "seq": 128,
  "pred_class": 3,
  "confidence": 0.87,
  "model": "standardized_lsvm",
  "latency_ms": 18.4,
  "fps": 1.0,
  "device": "rx-pi"
}
```

## Current Status

- MQTT topic design: completed
- Fake prediction publisher: planned
- Mosquitto broker setup: planned
- Dashboard visualization: planned
- Logging and alert: planned
