import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def build_payload(seq: int, pred_class: int, model_name: str, device_name: str, interval: float) -> dict:
    """
    Build one simulated aerosol prediction message.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seq": seq,
        "pred_class": pred_class,
        "confidence": round(random.uniform(0.80, 0.99), 3),
        "model": model_name,
        "latency_ms": round(random.uniform(10.0, 30.0), 2),
        "fps": round(1.0 / interval, 2),
        "device": device_name
    }


def main():
    parser = argparse.ArgumentParser(description="Fake MQTT publisher for Wi-Fi CSI aerosol sensing demo.")

    parser.add_argument("--broker", default="localhost", help="MQTT broker IP address or hostname.")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port.")
    parser.add_argument("--topic", default="csi/aerosol/pred", help="MQTT topic for prediction results.")
    parser.add_argument("--interval", type=float, default=1.0, help="Publishing interval in seconds.")
    parser.add_argument("--device", default="rx-pi", help="Device name.")
    parser.add_argument("--model", default="fake_demo", help="Model name.")

    args = parser.parse_args()

    client = mqtt.Client()
    client.connect(args.broker, args.port, keepalive=60)

    print("Connected to MQTT broker.")
    print(f"Broker: {args.broker}:{args.port}")
    print(f"Topic: {args.topic}")
    print("Press Ctrl+C to stop.")

    seq = 0

    try:
        while True:
            pred_class = seq % 6

            payload = build_payload(
                seq=seq,
                pred_class=pred_class,
                model_name=args.model,
                device_name=args.device,
                interval=args.interval
            )

            message = json.dumps(payload)
            client.publish(args.topic, message)

            print(message)

            seq += 1
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nPublisher stopped by user.")

    finally:
        client.disconnect()
        print("Disconnected from MQTT broker.")


if __name__ == "__main__":
    main()
