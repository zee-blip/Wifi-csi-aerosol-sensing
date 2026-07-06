# MQTT Notes

The AP Raspberry Pi runs the Mosquitto MQTT broker.

## Broker

```text
AP Pi broker IP: 10.42.1.1
Port: 1883
Topic: csi/aerosol/pred
```

## Subscribe on AP Pi

```bash
mosquitto_sub -h localhost -t csi/aerosol/pred -v
```

## Publish from Rx Pi

The Rx Pi publishes JSON prediction messages to:

```text
csi/aerosol/pred
```

## Purpose

MQTT is used as the lightweight communication layer between the edge sensing node and the AP gateway.

The Rx Pi performs local inference and only sends compact prediction results, not raw CSI data.
