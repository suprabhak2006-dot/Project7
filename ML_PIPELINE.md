# DeepTrace AI - Machine Learning Pipeline

DeepTrace AI employs a multi-tiered architecture that combines real deep neural networks with signal-processing algorithms.

---

## 1. Computer Vision & Face Localization

### Face Detection: OpenCV YuNet (`face_detection_yunet_2023mar.onnx`)
* **Framework**: OpenCV DNN / ONNX Runtime.
* **Weights**: Verified ONNX checkpoint (`8f2383e4dd3cfbb4...`).
* **Input**: BGR image with dynamic input sizing.
* **Output**: Bounding boxes `[x, y, w, h]`, detection confidence, and 5 facial landmarks:
  1. Right Eye (`[x, y]`)
  2. Left Eye (`[x, y]`)
  3. Nose Tip (`[x, y]`)
  4. Right Mouth Corner (`[x, y]`)
  5. Left Mouth Corner (`[x, y]`)
* **Alignment**: Euclidean affine rotation matrix aligning eyes to horizontal axis before crop extraction.

---

## 2. Vision AI Deepfake Detection

### Model: Vision Transformer (`dima806/deepfake_vs_real_image_detection`)
* **Framework**: PyTorch / HuggingFace Transformers.
* **Architecture**: ViT fine-tuned on binary classification (`Real` vs `Fake`).
* **Preprocessing**: Resized to 224x224 RGB, normalized with ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`.
* **Output**:
  * Raw Logits: `[logit_real, logit_fake]`
  * Softmax Probabilities: `p_fake`, `p_real`
  * Confidence: Difference margin between predicted class and 0.5 baseline.
* **Explainability Saliency Heatmap**:
  * Computes gradient magnitude of the `Fake` logit w.r.t. input pixel values: $\nabla_X \mathcal{L}_{\text{fake}}$.
  * Maximum channel intensity projected to 2D saliency map, normalized to `[0, 255]`, and blended with original face crop using OpenCV Jet colormap.
* **Documented Limitations**:
  * Specialized in facial region manipulation (DeepFaceLab, FaceSwap, SimSwap, etc.).
  * Does not classify full-body diffusion or background generation without localized face features.

---

## 3. Video Temporal Dynamics

* **Frame Sampling**: Configurable rates (Fast = 1 fps, Balanced = 3 fps, Deep = 8+ fps).
* **Face Tracking**: Bounding box Intersection-over-Union (IoU $\ge 0.25$) and spatial landmark proximity maintain continuous facial track IDs across sequential frames.
* **Temporal Consistency Metrics**:
  * **Normalized Landmark Drift**: Mean displacement of facial landmarks across consecutive frames normalized by face bounding box diagonal:
    $$\text{Drift}_t = \frac{1}{D_t} \sum_{k=1}^5 \|\mathbf{L}_{t, k} - \mathbf{L}_{t-1, k}\|_2$$
  * **Score Volatility**: Inter-frame fluctuation in manipulation probability $\Delta s_t = |s_t - s_{t-1}|$.
  * **Anomaly Spike Detection**: Flags frames where $\Delta s_t \ge 0.35$ or $s_t \ge 0.75$.

---

## 4. Acoustic Signal Forensics

* **Signal Normalization**: Audio extracted via FFmpeg to 16kHz 16-bit PCM mono WAV.
* **Spectral Flatness**: Ratio of geometric mean to arithmetic mean of STFT power spectrum:
  $$\text{Flatness} = \frac{\exp\left(\frac{1}{N} \sum \ln P_k\right)}{\frac{1}{N} \sum P_k}$$
  High flatness (> 0.40) indicates vocoder white noise or synthetic acoustic artifacts.
* **Autocorrelation Pitch Tracking ($f_0$)**: Fundamental frequency estimation across 100ms windows between 70Hz and 400Hz. Lack of natural micro-tremor variance indicates robotic synthetic speech.
* **Spectral Rolloff**: 85% energy concentration frequency.

---

## 5. Audio-Visual Synchronization

* Tracks vertical distance from nose tip to mouth midpoint across video frames to derive mouth aperture velocity.
* Aligns audio RMS energy envelope to identical frame timestamps.
* Computes normalized cross-correlation across lag window $[-15, +15]$ frames.
* Reports measured correlation, estimated lag in milliseconds, and identifies speech intervals lacking corresponding lip motion.
