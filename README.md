# Low-Cost Wi-Fi CSI Based Aerosol Sensing Prototype

This project implements an offline MATLAB reproduction of a Wi-Fi CSI-based aerosol sensing pipeline. It uses Channel State Information (CSI) extracted from commodity Wi-Fi hardware to classify aerosol concentration levels.

The current implementation focuses on CSI processing, feature extraction, and machine learning evaluation. A future extension will port the trained model to Raspberry Pi for edge inference.

## Current Status

- Offline MATLAB CSI processing: completed
- Feature extraction from CSI amplitude: completed
- KNN and standardized LSVM evaluation: completed
- Raspberry Pi edge deployment: in progress
- Robustness testing: planned

## Processing Pipeline

Raw PCAP files are processed through the following pipeline:

```text
PCAP parsing
→ CSI amplitude extraction
→ Windowing
→ Hampel filtering
→ Moving average smoothing
→ Statistical feature extraction
→ Machine learning classification
```

## Dataset Summary

Nine valid experimental trials were used after excluding one incomplete trial.

| Item | Value |
|---|---:|
| Valid trials | 9 |
| Classes | 6 |
| Total samples | 84,348 |
| Samples per class | 14,058 |
| Feature dimension | 250 |

## Machine Learning Results

The dataset was evaluated using 100 random splits. In each split, 10% of the samples were used for training and 90% were used for verification.

| Model | Average Accuracy | Minimum Accuracy | Maximum Accuracy |
|---|---:|---:|---:|
| KNN | 99.22% | 99.04% | 99.37% |
| Standardized LSVM | 96.06% | 92.12% | 97.72% |

## Key Findings

- KNN achieved the highest and most stable classification performance.
- Standardized LSVM also achieved high accuracy and provides a lighter model structure for potential edge deployment.
- The LSVM model was sensitive to feature scaling, so feature standardization was required before training.
- The results suggest that Wi-Fi CSI amplitude features contain distinguishable information related to aerosol concentration levels.

## Planned Edge Deployment

The next stage is to deploy a trained lightweight classifier to Raspberry Pi. The planned edge workflow is:

```text
Extracted 250-dimensional CSI feature vector
→ Load trained model on Raspberry Pi
→ Predict aerosol class
→ Output concentration level
```

## Repository Structure

```text
Wifi-csi-aerosol-sensing/
├── README.md
├── src/
├── scripts/
├── edge/
├── results/
├── docs/
└── data_sample/
```

## Notes

Raw PCAP files and full MATLAB datasets are not included due to file size limitations. This repository focuses on the processing workflow, code structure, machine learning results, and future edge deployment.

## Skills Demonstrated

- Wi-Fi CSI sensing
- Raspberry Pi-based wireless sensing
- Nexmon CSI data collection
- MATLAB signal processing
- CSI amplitude feature extraction
- KNN and LSVM classification
- Model evaluation over repeated random splits
- GitHub project documentation
- Planned Raspberry Pi edge inference
