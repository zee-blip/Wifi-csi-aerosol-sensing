#!/usr/bin/env python3
"""
pcap_lsvm_matlab_style_publisher.py

Offline pcap replay version of the Wi-Fi CSI edge inference pipeline.

Pipeline:
    pcap file
        -> Nexmon CSI decoding
        -> 242-subcarrier CSI amplitude
        -> 128-packet windowing
        -> MATLAB-style 250D feature extraction
        -> NumPy LSVM inference
        -> MQTT publish
"""

import argparse
import json
import os
import struct
import time
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


def read_pcap_packets(pcap_path):
    """Minimal standard libpcap reader. Returns raw packet bytes."""
    with open(pcap_path, "rb") as f:
        global_header = f.read(24)
        if len(global_header) < 24:
            raise RuntimeError("Invalid pcap file.")

        magic = global_header[:4]
        if magic == b"\xd4\xc3\xb2\xa1":
            endian = "<"
        elif magic == b"\xa1\xb2\xc3\xd4":
            endian = ">"
        elif magic == b"\x4d\x3c\xb2\xa1":
            endian = "<"
        elif magic == b"\xa1\xb2\x3c\x4d":
            endian = ">"
        else:
            raise RuntimeError("Unsupported pcap format.")

        while True:
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break

            _, _, incl_len, _ = struct.unpack(endian + "IIII", pkt_header)
            packet = f.read(incl_len)
            if len(packet) < incl_len:
                break

            yield packet


def decode_nexmon_csi_packet(packet):
    """
    Decode one Nexmon CSI packet.

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


def decode_csi_from_pcap(pcap_path, max_frames=None):
    frames = []
    for packet in read_pcap_packets(pcap_path):
        amp = decode_nexmon_csi_packet(packet)
        if amp is None:
            continue

        frames.append(amp)

        if max_frames is not None and len(frames) >= max_frames:
            break

    if len(frames) == 0:
        raise RuntimeError("No valid Nexmon CSI packets decoded.")

    return np.vstack(frames).astype(np.float32)


def hampel_filter_matrix(x, k=3, t0=3.0):
    """Hampel filter along time/window axis for each subcarrier."""
    x = x.copy().astype(np.float32)
    n, d = x.shape

    for col in range(d):
        s = x[:, col]
        filtered = s.copy()

        for i in range(n):
            start = max(0, i - k)
            end = min(n, i + k + 1)
            window = s[start:end]

            median = np.median(window)
            mad = np.median(np.abs(window - median))

            if mad == 0:
                continue

            threshold = t0 * 1.4826 * mad

            if abs(s[i] - median) > threshold:
                filtered[i] = median

        x[:, col] = filtered

    return x


def moving_average_matrix(x, win=5):
    """Centered moving average along the time/window axis."""
    x = x.astype(np.float32)
    n, d = x.shape
    out = np.zeros_like(x)
    half = win // 2

    for i in range(n):
        start = max(0, i - half)
        end = min(n, i + half + 1)
        out[i, :] = np.mean(x[start:end, :], axis=0)

    return out


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


def build_matlab_style_features(csi_amp, window_packets=128):
    """Convert packet-level CSI amplitude into 250D MATLAB-style features."""
    num_frames = csi_amp.shape[0]
    num_windows = num_frames // window_packets

    if num_windows <= 0:
        raise RuntimeError("Not enough CSI frames for one window.")

    usable = csi_amp[:num_windows * window_packets, :]
    windows = usable.reshape(num_windows, window_packets, N_SUBCARRIERS)
    win_amp = np.mean(windows, axis=1).astype(np.float32)

    win_amp = hampel_filter_matrix(win_amp, k=3, t0=3.0)
    win_amp = moving_average_matrix(win_amp, win=SMOOTH_WINDOWS)

    features = []

    for i in range(num_windows):
        amp_feat = win_amp[i, :]
        stat_feat = calc_stats(amp_feat)
        feat = np.concatenate([amp_feat, stat_feat]).astype(np.float32)

        if feat.shape[0] != FEATURE_DIM:
            raise RuntimeError("Feature dimension mismatch.")

        features.append(feat)

    return np.vstack(features).astype(np.float32)


def create_mqtt_client(broker, port):
    if mqtt is None:
        print("WARNING: paho-mqtt is not installed. MQTT publish disabled.")
        return None

    client = mqtt.Client()
    client.connect(broker, port, 60)
    return client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pcap", required=True, help="Input Nexmon CSI pcap file")
    parser.add_argument("--broker", default="10.42.1.1", help="MQTT broker IP")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="csi/aerosol/pred", help="MQTT topic")
    parser.add_argument("--model", default="models/lsvm_edge_params.npz", help="LSVM parameter file")
    parser.add_argument("--limit_windows", type=int, default=0, help="Number of windows to process, 0 means all")
    parser.add_argument("--interval", type=float, default=0.2, help="Interval between published messages")
    args = parser.parse_args()

    print("Loading LSVM params:", args.model)
    model = load_lsvm_params(args.model)

    print("classes:", model["classes"])
    print("coef shape:", model["coef"].shape)
    print("window_packets:", WINDOW_PACKETS)
    print("smooth_windows:", SMOOTH_WINDOWS)

    max_frames = None
    if args.limit_windows > 0:
        max_frames = args.limit_windows * WINDOW_PACKETS
        print("Frames needed:", max_frames)

    print("Decoding CSI from pcap:", args.pcap)
    csi_amp = decode_csi_from_pcap(args.pcap, max_frames=max_frames)

    print("Decoded CSI frames:", csi_amp.shape[0])
    print("CSI amplitude shape:", csi_amp.shape)

    X = build_matlab_style_features(csi_amp, window_packets=WINDOW_PACKETS)

    if args.limit_windows > 0:
        X = X[:args.limit_windows, :]

    print("Feature matrix shape:", X.shape)

    client = create_mqtt_client(args.broker, args.port)

    for seq, feat in enumerate(X):
        t0 = time.time()
        pred_class, confidence, _ = predict_lsvm(feat, model)
        latency_ms = (time.time() - t0) * 1000.0

        msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seq": seq,
            "pred_class": pred_class,
            "confidence": round(confidence, 3),
            "model": "lsvm_numpy_params_from_pcap_matlab_style",
            "latency_ms": round(latency_ms, 3),
            "device": "rx-pi",
            "source": "pcap_nexmon_csi",
            "feature_dim": int(feat.shape[0]),
            "window_packets": WINDOW_PACKETS,
            "pcap": os.path.basename(args.pcap),
        }

        payload = json.dumps(msg)
        print(payload)

        if client is not None:
            client.publish(args.topic, payload)

        if args.interval > 0:
            time.sleep(args.interval)

    if client is not None:
        client.disconnect()


if __name__ == "__main__":
    main()
