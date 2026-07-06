#!/usr/bin/env python3
"""
live_lsvm_matlab_style_publisher.py

Real-time Wi-Fi CSI edge inference script.

Pipeline:
    live Nexmon CSI packets from wlan0
        -> 242-subcarrier CSI amplitude
        -> 128-packet window
        -> causal MATLAB-style feature extraction
        -> NumPy LSVM inference
        -> MQTT publish

Run on Rx Raspberry Pi:

    sudo python3 edge/live_lsvm_matlab_style_publisher.py --broker 10.42.1.1 --topic csi/aerosol/pred
"""

import argparse
import json
import socket
import time
from collections import deque
from datetime import datetime, timezone

import numpy as np

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


WINDOW_PACKETS = 128
SMOOTH_WINDOWS = 5
N_SUBCARRIERS = 242
FEATURE_DIM = 250
ETH_P_ALL = 0x0003


def softmax(scores):
    scores = np.asarray(scores, dtype=np.float64)
    scores = scores - np.max(scores)
    exp_scores = np.exp(scores)
    return exp_scores / np.sum(exp_scores)


def load_lsvm_params(model_path):
    params = np.load(model_path)
    return {
        "mean": params["mean"].astype(np.float32),
        "scale": params["scale"].astype(np.float32),
        "coef": params["coef"].astype(np.float32),
        "intercept": params["intercept"].astype(np.float32),
        "classes": params["classes"],
    }


def predict_lsvm(feature, model):
    feature = feature.astype(np.float32)
    x = (feature - model["mean"]) / model["scale"]
    scores = np.dot(model["coef"], x) + model["intercept"]
    pred_idx = int(np.argmax(scores))
    pred_class = int(model["classes"][pred_idx])
    probs = softmax(scores)
    confidence = float(probs[pred_idx])
    return pred_class, confidence, scores


def decode_nexmon_csi_packet(packet):
    """
    Decode one Nexmon CSI packet from raw socket bytes.

    The working setup uses Nexmon CSI packets containing the magic string
    'NEXMON'. For the Raspberry Pi 4B Nexmon CSI 80 MHz setup, the CSI section
    is decoded as 256 complex int16 values. Then 242 effective subcarriers are
    retained by dropping 7 bins at each edge.
    """
    magic = b"NEXMON"
    pos = packet.find(magic)
    if pos < 0:
        return None

    csi_start = pos + 18
    csi_bytes = packet[csi_start:csi_start + 1024]
    if len(csi_bytes) < 1024:
        return None

    raw = np.frombuffer(csi_bytes, dtype="<i2")
    if raw.size < 512:
        return None

    raw = raw[:512]
    real = raw[0::2].astype(np.float32)
    imag = raw[1::2].astype(np.float32)
    csi_complex = real + 1j * imag
    amp_256 = np.abs(csi_complex).astype(np.float32)
    amp_242 = amp_256[7:-7]

    if amp_242.shape[0] != N_SUBCARRIERS:
        return None

    return amp_242


def calc_stats(v):
    """8 statistical features: mean, max, min, std, var, mad, skewness, kurtosis."""
    v = np.asarray(v, dtype=np.float32)

    mean_v = float(np.mean(v))
    max_v = float(np.max(v))
    min_v = float(np.min(v))
    std_v = float(np.std(v))
    var_v = float(np.var(v))
    mad_v = float(np.mean(np.abs(v - mean_v)))

    if std_v < 1e-12:
        skew_v = 0.0
        kurt_v = 0.0
    else:
        z = (v - mean_v) / std_v
        skew_v = float(np.mean(z ** 3))
        kurt_v = float(np.mean(z ** 4))

    return np.array(
        [mean_v, max_v, min_v, std_v, var_v, mad_v, skew_v, kurt_v],
        dtype=np.float32,
    )


def causal_hampel_current(history, k=3, t0=3.0):
    """
    Causal Hampel approximation for the current 242D window vector.

    Offline MATLAB processing can use future windows. Real-time inference cannot.
    Therefore, this function uses the current and previous windows only.
    """
    arr = np.vstack(history).astype(np.float32)
    current = arr[-1].copy()

    start = max(0, arr.shape[0] - (2 * k + 1))
    local = arr[start:, :]

    med = np.median(local, axis=0)
    mad = np.median(np.abs(local - med), axis=0)
    threshold = t0 * 1.4826 * mad

    mask = (mad > 0) & (np.abs(current - med) > threshold)
    current[mask] = med[mask]

    return current.astype(np.float32)


def causal_moving_average(history, win=5):
    """Causal moving average using current and previous windows."""
    arr = np.vstack(list(history)[-win:]).astype(np.float32)
    return np.mean(arr, axis=0).astype(np.float32)


def build_live_feature(packet_window, window_history, smooth_history):
    """
    Build one 250D feature from one 128-packet CSI window.
    """
    packet_window = np.vstack(packet_window).astype(np.float32)
    amp_mean = np.mean(packet_window, axis=0).astype(np.float32)

    window_history.append(amp_mean)

    filtered_current = causal_hampel_current(window_history, k=3, t0=3.0)
    smooth_history.append(filtered_current)

    smoothed = causal_moving_average(smooth_history, win=SMOOTH_WINDOWS)

    stat_feat = calc_stats(smoothed)
    feature = np.concatenate([smoothed, stat_feat]).astype(np.float32)

    if feature.shape[0] != FEATURE_DIM:
        raise RuntimeError("Feature dimension mismatch.")

    return feature


def create_mqtt_client(broker, port):
    if mqtt is None:
        print("WARNING: paho-mqtt is not installed. MQTT publish disabled.")
        return None

    client = mqtt.Client()
    client.connect(broker, port, 60)
    return client


def open_raw_socket(interface):
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_P_ALL))
    sock.bind((interface, 0))
    return sock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="10.42.1.1", help="MQTT broker IP")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="csi/aerosol/pred", help="MQTT topic")
    parser.add_argument("--model", default="models/lsvm_edge_params.npz", help="LSVM parameter file")
    parser.add_argument("--interface", default="wlan0", help="CSI capture interface")
    parser.add_argument("--window_packets", type=int, default=WINDOW_PACKETS, help="CSI packets per prediction window")
    args = parser.parse_args()

    print("Loading LSVM params:", args.model)
    model = load_lsvm_params(args.model)

    print("classes:", model["classes"])
    print("coef shape:", model["coef"].shape)
    print("window_packets:", args.window_packets)
    print("smooth_windows:", SMOOTH_WINDOWS)

    print("Connecting to MQTT broker {}:{} ...".format(args.broker, args.port))
    client = create_mqtt_client(args.broker, args.port)

    print("Opening raw socket on interface:", args.interface)
    sock = open_raw_socket(args.interface)

    print("Live CSI inference started.")
    print("Make sure Tx is generating traffic, for example continuous ping.")
    print("Press Ctrl+C to stop.")

    packet_window = []
    window_history = deque(maxlen=32)
    smooth_history = deque(maxlen=SMOOTH_WINDOWS)

    seq = 0
    window_start_time = time.time()

    try:
        while True:
            packet, addr = sock.recvfrom(4096)

            # Keep packets from the selected interface when address info is available.
            if addr and len(addr) > 0 and addr[0] != args.interface:
                continue

            amp = decode_nexmon_csi_packet(packet)
            if amp is None:
                continue

            packet_window.append(amp)

            if len(packet_window) < args.window_packets:
                continue

            window_end_time = time.time()
            window_time_ms = (window_end_time - window_start_time) * 1000.0

            feature = build_live_feature(packet_window, window_history, smooth_history)
            packet_window = []
            window_start_time = time.time()

            t0 = time.time()
            pred_class, confidence, _ = predict_lsvm(feature, model)
            latency_ms = (time.time() - t0) * 1000.0

            msg = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "seq": seq,
                "pred_class": pred_class,
                "confidence": round(confidence, 3),
                "model": "lsvm_numpy_params_live_matlab_style",
                "latency_ms": round(latency_ms, 3),
                "window_time_ms": round(window_time_ms, 3),
                "device": "rx-pi",
                "source": "live_nexmon_csi",
                "feature_dim": int(feature.shape[0]),
                "window_packets": args.window_packets,
            }

            payload = json.dumps(msg)
            print(payload)

            if client is not None:
                client.publish(args.topic, payload)

            seq += 1

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        if client is not None:
            client.disconnect()
            print("Disconnected from MQTT broker.")

        sock.close()


if __name__ == "__main__":
    main()
