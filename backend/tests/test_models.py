import os
import numpy as np
import cv2
import pytest
from backend.app.services.model_registry import registry

def test_model_registry_status():
    status_list = registry.get_status()
    assert len(status_list) >= 5
    names = [m["name"] for m in status_list]
    assert "yunet_face_detector" in names
    assert "vit_deepfake_detector" in names
    assert "temporal_consistency_analyzer" in names
    assert "signal_audio_forensics" in names

def test_vit_deepfake_detector_real_inference():
    ai_detector = registry.get_image_ai_detector()
    assert ai_detector is not None
    assert ai_detector.is_available() is True

    # 224x224 synthetic crop
    dummy_face = np.full((224, 224, 3), 150, dtype=np.uint8)
    res = ai_detector.predict(dummy_face)
    
    assert res["status"] == "READY"
    assert "manipulation_score" in res
    assert 0.0 <= res["manipulation_score"] <= 1.0
    assert "raw_logits" in res
    assert len(res["raw_logits"]) == 2  # Real and Fake logits
    assert "probabilities" in res
    assert "real" in res["probabilities"]
    assert "fake" in res["probabilities"]

def test_vit_saliency_heatmap_generation():
    ai_detector = registry.get_image_ai_detector()
    dummy_face = np.full((224, 224, 3), 150, dtype=np.uint8)
    heatmap, overlay = ai_detector.generate_saliency_heatmap(dummy_face)
    
    assert heatmap.shape == dummy_face.shape
    assert overlay.shape == dummy_face.shape
    assert heatmap.dtype == np.uint8
