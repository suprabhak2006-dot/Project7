# DeepTrace AI - Forensic Methodology

## 1. Evidence Preservation & Chain of Custody

The integrity of forensic media rests upon strict non-destructive handling:
1. **Ingestion Hashing**: As raw bytes stream into the platform, the SHA-256 cryptographic digest is calculated immediately.
2. **Immutable Storage**: Original evidence is stored in read-only directories (`storage/cases/CASE-XXXX/original/`). Filesystem permissions and application logic prevent overwriting or in-place modifications.
3. **Derivation Tracking**: All downstream artifacts (face crops, spectrograms, normalized frames, heatmaps) are saved in dedicated subdirectories with deterministic naming linked to the original evidence number.
4. **Integrity Audits**: Investigators can re-hash the original storage file at any time via `POST /api/evidence/{id}/verify-integrity`.

---

## 2. Scientific Image Forensics

In addition to neural network inference, DeepTrace AI implements physics-based forensic measurements:

### A. JPEG Compression Error Level Analysis (ELA)
* Re-compresses the image at 90% quality and computes the standard deviation of pixel deltas across color channels.
* Spliced or regionally re-saved elements exhibit divergent compression error levels compared to original camera sensor blocks.

### B. High-Frequency Noise Residual Variance
* Extracts sensor pattern noise using a $3 \times 3$ median filter residual:
  $$N(x, y) = |I(x, y) - \text{median}(I(x, y))|$$
* Calculates local noise variance across the facial ROI versus background context. An inconsistent noise variance ratio indicates composite splicing or generative denoising.

### C. 2D FFT Azimuthal Frequency Decay
* Generates the 2D Fast Fourier Transform power spectrum with a Hanning window.
* Analyzes the high-frequency to mid-frequency radial energy ratio. Generative adversarial networks (GANs) and diffusion models exhibit abnormal high-frequency spectral spikes or altered radial power-law slopes.

### D. Illumination Normal Gradient Disparity
* Calculates Sobel first-order directional gradient vectors across the face boundary versus surrounding background scene.
* Angular disparity exceeding 45 degrees indicates inconsistent light source positioning.

---

## 3. Multimodal Evidence Fusion & Conflict Detection

DeepTrace AI aggregates evidence using a documented, confidence-weighted framework rather than opaque averaging:

$$S_{\text{final}} = \frac{\sum w_i \cdot c_i \cdot s_i}{\sum w_i \cdot c_i}$$

Where:
* $w_i$: Intrinsic weight assigned to module $i$.
* $c_i$: Measured certainty / confidence of module $i$.
* $s_i$: Raw anomaly score of module $i$.

### Automated Conflict Detection:
If the maximum divergence between reliable modules ($\max(s_i) - \min(s_i)$) exceeds $0.55$ (e.g., Vision AI indicates high likelihood while noise, compression, and metadata indicate authentic camera capture), the system explicitly flags:
```
EVIDENCE CONFLICT DETECTED
```
and classifies the assessment as `EVIDENCE_CONFLICT`. This prevents false certainty when scientific modalities disagree.

---

## 4. Probabilistic Interpretation Standards

DeepTrace AI enforces strict terminology:
* **Low Manipulation Likelihood**: Forensic measurements and neural outputs fall within standard camera capture distributions.
* **Moderate Manipulation Likelihood**: Anomalous signals detected in one modality without strong multi-signal corroboration.
* **High Manipulation Likelihood**: Multiple independent modalities (AI vision, temporal drift, acoustic anomalies) corroborate manipulation.
* **Inconclusive**: Insufficient resolution, heavy degradation, or model unavailability prevents reliable measurement.
* **Evidence Conflict**: Disparate forensic modules produce contradictory results; manual investigation required.
