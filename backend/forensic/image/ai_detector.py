import os
from typing import Dict, Any, Tuple, Optional
import torch
import numpy as np
from PIL import Image
import cv2
from transformers import AutoImageProcessor, AutoModelForImageClassification

class ViTDeepfakeDetector:
    def __init__(self, model_id: str = "dima806/deepfake_vs_real_image_detection", enable_gpu: bool = True):
        self.model_id = model_id
        self.device = "cuda" if (enable_gpu and torch.cuda.is_available()) else "cpu"
        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            self.processor = AutoImageProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_id)
            self.model.to(self.device)
            self.model.eval()
            print(f"[+] ViT Deepfake model loaded successfully on {self.device}")
        except Exception as e:
            print(f"[!] Error loading ViT Deepfake model {self.model_id}: {e}")
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def predict(self, face_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Executes real ViT inference on face crop.
        Returns actual raw logits, probabilities, and manipulation score.
        """
        if not self.is_available():
            return {
                "status": "UNAVAILABLE",
                "error": "ViT Deepfake model not loaded",
                "manipulation_score": 0.0,
                "confidence": 0.0,
                "raw_logits": [],
                "probabilities": {},
                "model_name": "vit_deepfake_detector",
                "model_version": "1.0",
                "device": self.device,
            }

        # Convert BGR to RGB PIL Image
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(face_rgb)

        inputs = self.processor(images=pil_img, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0].cpu().numpy()

        raw_logits = logits[0].cpu().tolist()
        
        # ID 0 is 'Real', ID 1 is 'Fake' for dima806/deepfake_vs_real_image_detection
        prob_real = float(probs[0])
        prob_fake = float(probs[1])
        
        # Confidence is the margin between top prediction and 0.5 baseline
        confidence = float(abs(prob_fake - 0.5) * 2.0)

        return {
            "status": "READY",
            "manipulation_score": prob_fake,
            "confidence": confidence,
            "raw_logits": raw_logits,
            "probabilities": {
                "real": prob_real,
                "fake": prob_fake
            },
            "model_name": "vit_deepfake_detector",
            "model_version": "1.0",
            "device": self.device,
        }

    def generate_saliency_heatmap(self, face_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates real gradient-based saliency attribution heatmap from model weights.
        Returns:
            heatmap_colormap: BGR heatmap image
            overlay: BGR image blended with original face
        """
        if not self.is_available():
            # Return blank if model unavailable
            h, w = face_bgr.shape[:2]
            return np.zeros((h, w, 3), dtype=np.uint8), face_bgr.copy()

        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(face_rgb)
        
        inputs = self.processor(images=pil_img, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)
        pixel_values.requires_grad = True

        outputs = self.model(pixel_values=pixel_values)
        logits = outputs.logits
        # Backprop w.r.t the "Fake" class (index 1)
        score = logits[0, 1]
        score.backward()

        # Compute gradient magnitude
        gradients = pixel_values.grad.data.abs()[0].cpu().numpy() # [3, H, W]
        saliency = np.max(gradients, axis=0) # [H, W]

        # Normalize to 0 - 255
        s_min, s_max = saliency.min(), saliency.max()
        if s_max - s_min > 1e-6:
            saliency_norm = ((saliency - s_min) / (s_max - s_min) * 255).astype(np.uint8)
        else:
            saliency_norm = np.zeros_like(saliency, dtype=np.uint8)

        # Resize to original face crop dimensions
        h, w = face_bgr.shape[:2]
        saliency_resized = cv2.resize(saliency_norm, (w, h), interpolation=cv2.INTER_CUBIC)
        
        # Apply Jet colormap
        heatmap_colored = cv2.applyColorMap(saliency_resized, cv2.COLORMAP_JET)
        
        # Blend overlay (60% original, 40% heatmap)
        overlay = cv2.addWeighted(face_bgr, 0.6, heatmap_colored, 0.4, 0)

        return heatmap_colored, overlay
