import argparse
import json
import os
import time
from datetime import datetime, timezone

import numpy as np
import paho.mqtt.client as mqtt


def softmax(z):
    z = z - np.max(z)
    exp_z = np.exp(z)
    return exp_z / np.sum(exp_z)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", required=True)
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="csi/aerosol/pred")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--interval", type=float, default=1.0)

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    x_path = os.path.join(base_dir, "data_sample", "X_sample_features.csv")
    y_path = os.path.join(base_dir, "data_sample", "Y_sample_labels.csv")
    param_path = os.path.join(base_dir, "models", "lsvm_edge_params.npz")

    print("Loading LSVM parameter model...")
    params = np.load(param_path)

    mean = params["mean"]
    scale = params["scale"]
    coef = params["coef"]
    intercept = params["intercept"]
    classes = params["classes"]

    print("mean shape:", mean.shape)
    print("scale shape:", scale.shape)
    print("coef shape:", coef.shape)
    print("intercept shape:", intercept.shape)
    print("classes:", classes)

    print("Loading sample features...")
    X = np.loadtxt(x_path, delimiter=",", dtype=np.float32)
    y = np.loadtxt(y_path, delimiter=",", dtype=np.int32).ravel()

    print("X shape:", X.shape)
    print("y shape:", y.shape)

    print(f"Connecting to MQTT broker {args.broker}:{args.port} ...")
    client = mqtt.Client()
    client.connect(args.broker, args.port, 60)

    print(f"Publishing to topic: {args.topic}")
    print("Press Ctrl+C to stop.")

    try:
        n = min(args.limit, len(X))

        for seq in range(n):
            start = time.time()

            x = X[seq]
            true_class = int(y[seq])

            x_scaled = (x - mean) / scale
            scores = coef.dot(x_scaled) + intercept

            probs = softmax(scores)
            pred_index = int(np.argmax(scores))
            pred_class = int(classes[pred_index])
            confidence = float(probs[pred_index])

            latency_ms = (time.time() - start) * 1000.0

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "seq": seq,
                "pred_class": pred_class,
                "true_class": true_class,
                "confidence": round(confidence, 3),
                "model": "lsvm_numpy_params",
                "latency_ms": round(latency_ms, 3),
                "device": "rx-pi",
                "source": "sample_feature_csv"
            }

            msg = json.dumps(payload)
            client.publish(args.topic, msg)
            print(msg)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nPublisher stopped by user.")

    finally:
        client.disconnect()
        print("Disconnected from MQTT broker.")


if __name__ == "__main__":
    main()
