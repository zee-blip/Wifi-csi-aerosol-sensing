# Live Inference Sample Output

Example output from the live edge inference pipeline:

```json
{
  "timestamp": "2026-06-xxTxx:xx:xxZ",
  "seq": 0,
  "pred_class": 2,
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

The `window_time_ms` field represents the time needed to collect one 128-packet CSI window. In the current setup, the system outputs approximately one prediction per second.

The `latency_ms` field represents the LSVM inference time after the feature vector has been generated.

Note: The `confidence` value is derived from LSVM decision scores and is used as a relative confidence indicator, not a calibrated probability.
