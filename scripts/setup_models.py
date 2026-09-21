"""
DeepTrace AI - Model Initialization & Verification Script
Downloads, verifies, and runs inference health checks on required AI models.
"""
import os
import sys
import hashlib
import urllib.request
import torch
import cv2
import numpy as np
from PIL import Image

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
YUNET_PATH = os.path.join("models", "checkpoints", "face_detection_yunet_2023mar.onnx")
VIT_MODEL_ID = "dima806/deepfake_vs_real_image_detection"

def get_file_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            sha256.update(chunk)
    return sha256.hexdigest()

def setup_yunet() -> bool:
    print(f"[*] Setting up YuNet face detection model...")
    os.makedirs(os.path.dirname(YUNET_PATH), exist_ok=True)
    if not os.path.exists(YUNET_PATH) or os.path.getsize(YUNET_PATH) < 100000:
        print(f"    Downloading from {YUNET_URL}...")
        try:
            urllib.request.urlretrieve(YUNET_URL, YUNET_PATH)
        except Exception as e:
            print(f"[!] ERROR downloading YuNet model: {e}")
            return False
    size = os.path.getsize(YUNET_PATH)
    sha256 = get_file_sha256(YUNET_PATH)
    print(f"    YuNet checkpoint: {YUNET_PATH} ({size} bytes, SHA-256: {sha256[:16]}...)")
    
    # Test initialization
    try:
        detector = cv2.FaceDetectorYN_create(YUNET_PATH, "", (320, 320))
        dummy_img = np.zeros((320, 320, 3), dtype=np.uint8)
        detector.setInputSize((320, 320))
        _, faces = detector.detect(dummy_img)
        print("    [+] YuNet face detector initialized & verified successfully.")
        return True
    except Exception as e:
        print(f"[!] YuNet initialization failed: {e}")
        return False

def setup_vit_detector() -> bool:
    print(f"[*] Setting up Image Deepfake Detector: {VIT_MODEL_ID}...")
    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        processor = AutoImageProcessor.from_pretrained(VIT_MODEL_ID)
        model = AutoModelForImageClassification.from_pretrained(VIT_MODEL_ID)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        
        print(f"    Model loaded on device: {device}")
        print(f"    Model task: Binary Deepfake Classification ({model.config.id2label})")
        
        # Test inference with dummy synthetic tensor
        dummy = Image.fromarray(np.uint8(np.random.rand(224, 224, 3) * 255))
        inputs = processor(images=dummy, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
        
        print(f"    [+] Model test inference passed. Output logits shape: {outputs.logits.shape}")
        print(f"    [+] Sample inference probabilities: Real={probs[0]:.4f}, Fake={probs[1]:.4f}")
        return True
    except Exception as e:
        print(f"[!] ViT detector setup failed: {e}")
        return False

def main():
    print("==========================================================")
    print("       DEEPTRACE AI - MODEL SETUP & HEALTH CHECK           ")
    print("==========================================================")
    device_info = "CUDA (NVIDIA GPU)" if torch.cuda.is_available() else "CPU"
    print(f"Active Hardware Device: {device_info}")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"OpenCV Version: {cv2.__version__}")
    print("----------------------------------------------------------")

    yunet_ok = setup_yunet()
    vit_ok = setup_vit_detector()

    print("----------------------------------------------------------")
    if yunet_ok and vit_ok:
        print("[SUCCESS] All required core models are downloaded, verified, and operational.")
        sys.exit(0)
    else:
        print("[FAILURE] One or more core models failed initialization.")
        sys.exit(1)

if __name__ == "__main__":
    main()
