# Edge Deployment

This folder contains Python scripts for Raspberry Pi-based edge inference.

The current goal is to deploy a lightweight classifier trained from CSI features. The first edge deployment version will use pre-extracted 250-dimensional CSI feature vectors as input.

## Planned Edge Workflow

```text
Load trained model
→ Load 250-dimensional CSI feature vector
→ Predict aerosol class
→ Output concentration level
```

## Current Status

- MATLAB offline model evaluation: completed
- Python edge inference script: planned
- Raspberry Pi deployment test: planned
