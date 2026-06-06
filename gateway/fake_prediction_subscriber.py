import argparse
import json

import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(userdata["topic"])
        print(f"Subscribed to topic: {userdata['topic']}")
    else:
        print(f"Failed to connect, return code: {rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")

    try:
        data = json.loads(payload)
        print(
            f"[RX] seq={data.get('seq')} "
            f"class={data.get('pred_class')} "
            f"confidence={data.get('confidence')} "
            f"latency={data.get('latency_ms')} ms "
            f"device={data.get('device')}"
        )
    except json.JSONDecodeError:
        print(f"[RX] Raw message: {payload}")


def main():
    parser = argparse.ArgumentParser(
        description="Fake MQTT subscriber for Wi-Fi CSI aerosol sensing demo."
    )

    parser.add_argument("--broker", default="localhost", help="MQTT broker IP address or hostname.")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port.")
    parser.add_argument("--topic", default="csi/aerosol/pred", help="MQTT topic to subscribe.")

    args = parser.parse_args()

    client = mqtt.Client(userdata={"topic": args.topic})
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to broker: {args.broker}:{args.port}")
    client.connect(args.broker, args.port, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nSubscriber stopped by user.")
        client.disconnect()


if __name__ == "__main__":
    main()
