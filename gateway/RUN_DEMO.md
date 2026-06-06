# MQTT Closed-loop Demo

This demo verifies the MQTT communication loop between a simulated edge inference node and a gateway-side subscriber.

## Workflow

```text
Fake edge inference publisher
→ MQTT broker
→ Gateway subscriber
→ Real-time prediction message parsing
```

## Install Dependencies

```bash
pip install -r gateway/requirements.txt
```

## Run Subscriber

Open the first terminal:

```bash
python gateway/fake_prediction_subscriber.py --broker test.mosquitto.org --topic csi/aerosol/zee_blip/pred
```

## Run Publisher

Open the second terminal:

```bash
python gateway/fake_prediction_publisher.py --broker test.mosquitto.org --topic csi/aerosol/zee_blip/pred
```

## Expected Output

The publisher sends simulated aerosol prediction messages in JSON format:

```json
{
  "timestamp": "2026-06-06T00:00:00Z",
  "seq": 0,
  "pred_class": 0,
  "confidence": 0.91,
  "model": "fake_demo",
  "latency_ms": 18.2,
  "fps": 1.0,
  "device": "rx-pi"
}
```

The subscriber receives and prints parsed messages:

```text
[RX] seq=0 class=0 confidence=0.91 latency=18.2 ms device=rx-pi
[RX] seq=1 class=1 confidence=0.86 latency=22.4 ms device=rx-pi
```

## Current Status

- Fake MQTT publisher: completed
- Gateway MQTT subscriber: completed
- Public MQTT broker test: completed
- Local gateway broker setup: planned
- Dashboard visualization: planned
