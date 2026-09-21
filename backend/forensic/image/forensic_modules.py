import io
from typing import Dict, Any, List, Optional
import numpy as np
import cv2
from PIL import Image

def analyze_jpeg_compression(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Error Level Analysis (ELA) and JPEG compression artifact measurement.
    Re-compresses image at 90% quality and computes pixel delta variance.
    """
    h, w = image_bgr.shape[:2]
    pil_img = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
    
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    recompressed = cv2.cvtColor(np.array(Image.open(buffer)), cv2.COLOR_RGB2BGR)

    diff = cv2.absdiff(image_bgr, recompressed).astype(np.float32)
    mean_diff = float(np.mean(diff))
    max_diff = float(np.max(diff))
    std_diff = float(np.std(diff))

    # Standard ELA scale
    ela_scale = 15.0
    scaled_diff = np.clip(diff * ela_scale, 0, 255).astype(np.uint8)

    # Anomaly metric: high standard deviation in error level indicates splicing/inconsistent compression
    anomaly_score = min(1.0, (std_diff / 15.0))
    
    return {
        "mean_error": round(mean_diff, 4),
        "max_error": round(max_diff, 4),
        "error_std_dev": round(std_diff, 4),
        "anomaly_score": round(anomaly_score, 4),
        "confidence": 0.85,
        "methodology": "JPEG Error Level Analysis (ELA, Q=90) and residual variance"
    }

def analyze_noise_distribution(image_bgr: np.ndarray, face_box: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Analyzes high-frequency residual noise patterns using a Laplacian operator.
    Compares face region noise variance to background context noise variance.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Extract noise via difference with median blur
    denoised = cv2.medianBlur(gray, 3)
    noise_residual = cv2.absdiff(gray, denoised).astype(np.float32)

    h, w = gray.shape
    global_noise_var = float(np.var(noise_residual))

    face_noise_var = global_noise_var
    bg_noise_var = global_noise_var
    variance_ratio = 1.0

    if face_box and len(face_box) == 4:
        fx, fy, fw, fh = face_box
        fx2, fy2 = min(w, fx + fw), min(h, fy + fh)
        if fx2 > fx and fy2 > fy:
            face_roi = noise_residual[fy:fy2, fx:fx2]
            if face_roi.size > 0:
                face_noise_var = float(np.var(face_roi))
                
                # Mask out face to compute background
                bg_mask = np.ones((h, w), dtype=bool)
                bg_mask[fy:fy2, fx:fx2] = False
                if np.any(bg_mask):
                    bg_noise_var = float(np.var(noise_residual[bg_mask]))
                    
                if bg_noise_var > 1e-4:
                    variance_ratio = face_noise_var / bg_noise_var

    # Variance ratio deviating significantly from 1.0 indicates mismatched noise/splicing
    noise_inconsistency = min(1.0, abs(np.log(max(variance_ratio, 1e-4))) / 2.0)

    return {
        "global_noise_variance": round(global_noise_var, 4),
        "face_noise_variance": round(face_noise_var, 4),
        "background_noise_variance": round(bg_noise_var, 4),
        "noise_variance_ratio": round(variance_ratio, 4),
        "anomaly_score": round(noise_inconsistency, 4),
        "confidence": 0.80,
        "methodology": "Median-filtered residual noise variance across facial ROI vs background"
    }

def analyze_frequency_spectrum(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Computes 2D Fast Fourier Transform (FFT) power spectrum and analyzes high-frequency decay.
    Generative models exhibit synthetic spectral peaks and altered radial power-law decay.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # 2D FFT with Hanning window to reduce boundary artifacts
    win = np.outer(np.hanning(h), np.hanning(w))
    fft2 = np.fft.fftshift(np.fft.fft2(gray * win))
    magnitude_spectrum = np.abs(fft2)
    power_spectrum = magnitude_spectrum ** 2

    cy, cx = h // 2, w // 2
    # Radial frequency distribution
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx)**2 + (y - cy)**2).astype(int)
    
    max_r = min(cx, cy)
    radial_profile = np.zeros(max_r, dtype=np.float32)
    for i in range(1, max_r):
        mask = (r == i)
        if np.any(mask):
            radial_profile[i] = np.mean(power_spectrum[mask])
            
    # Measure high-frequency to mid-frequency energy ratio
    mid_freq_energy = float(np.sum(radial_profile[max_r // 4 : max_r // 2]))
    high_freq_energy = float(np.sum(radial_profile[max_r // 2 : max_r]))
    
    freq_ratio = (high_freq_energy / (mid_freq_energy + 1e-6))
    
    # Anomaly indicator (synthetic generators often leave abnormal high-freq energy artifacts)
    anomaly_score = min(1.0, max(0.0, (freq_ratio - 0.15) * 3.0))

    return {
        "mid_frequency_energy": round(mid_freq_energy, 2),
        "high_frequency_energy": round(high_freq_energy, 2),
        "frequency_energy_ratio": round(freq_ratio, 4),
        "anomaly_score": round(anomaly_score, 4),
        "confidence": 0.78,
        "methodology": "2D Fast Fourier Transform (FFT) azimuthal power-spectrum decay analysis"
    }

def analyze_lighting_consistency(image_bgr: np.ndarray, face_box: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Estimates dominant illumination gradient vector of the facial region vs surrounding image.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Compute image gradients via Sobel
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)

    h, w = gray.shape
    if face_box and len(face_box) == 4:
        fx, fy, fw, fh = face_box
        fx2, fy2 = min(w, fx + fw), min(h, fy + fh)
        face_gx = np.mean(grad_x[fy:fy2, fx:fx2])
        face_gy = np.mean(grad_y[fy:fy2, fx:fx2])
        
        # Background gradients
        bg_mask = np.ones((h, w), dtype=bool)
        bg_mask[fy:fy2, fx:fx2] = False
        bg_gx = np.mean(grad_x[bg_mask])
        bg_gy = np.mean(grad_y[bg_mask])
    else:
        face_gx, face_gy = float(np.mean(grad_x)), float(np.mean(grad_y))
        bg_gx, bg_gy = face_gx, face_gy

    # Angle between face lighting gradient and background gradient
    dot = face_gx * bg_gx + face_gy * bg_gy
    norm_face = np.sqrt(face_gx**2 + face_gy**2) + 1e-6
    norm_bg = np.sqrt(bg_gx**2 + bg_gy**2) + 1e-6
    cos_sim = np.clip(dot / (norm_face * norm_bg), -1.0, 1.0)
    angle_deg = float(np.degrees(np.arccos(cos_sim)))

    # Angular disparity above 45 degrees indicates illumination mismatch
    anomaly_score = min(1.0, angle_deg / 90.0)

    return {
        "face_gradient_angle_deg": round(float(np.degrees(np.arctan2(face_gy, face_gx))), 2),
        "background_gradient_angle_deg": round(float(np.degrees(np.arctan2(bg_gy, bg_gx))), 2),
        "illumination_angle_disparity_deg": round(angle_deg, 2),
        "anomaly_score": round(anomaly_score, 4),
        "confidence": 0.72,
        "methodology": "Sobel first-order directional illumination gradient vector alignment"
    }

def analyze_landmark_geometry(landmarks: List[List[float]]) -> Dict[str, Any]:
    """
    Analyzes biometric landmark symmetry and facial geometry ratios.
    landmarks: [[x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5]]
    """
    if len(landmarks) < 5:
        return {"anomaly_score": 0.0, "confidence": 0.5, "status": "Insufficient landmarks"}

    re = np.array(landmarks[0]) # Right eye
    le = np.array(landmarks[1]) # Left eye
    nt = np.array(landmarks[2]) # Nose tip
    rm = np.array(landmarks[3]) # Right mouth corner
    lm = np.array(landmarks[4]) # Left mouth corner

    # Inter-ocular distance
    iod = np.linalg.norm(re - le)
    # Eye-to-mouth distance
    re_to_rm = np.linalg.norm(re - rm)
    le_to_lm = np.linalg.norm(le - lm)

    # Facial symmetry ratio (ideal face is close to 1.0)
    symmetry_ratio = float(min(re_to_rm, le_to_lm) / (max(re_to_rm, le_to_lm) + 1e-6))
    
    # Nose centration via 2D point-to-line distance
    mid_eyes = (re + le) / 2.0
    mid_mouth = (rm + lm) / 2.0
    face_vertical_axis = np.linalg.norm(mid_eyes - mid_mouth)
    v1 = mid_mouth - mid_eyes
    v2 = mid_eyes - nt
    cross_2d = abs(v1[0] * v2[1] - v1[1] * v2[0])
    nose_offset = cross_2d / (face_vertical_axis + 1e-6)

    # Anomaly score based on severe geometric distortion
    geom_anomaly = max(0.0, (1.0 - symmetry_ratio) * 1.5)

    return {
        "inter_ocular_distance": round(float(iod), 2),
        "facial_symmetry_ratio": round(symmetry_ratio, 4),
        "nose_axial_offset": round(float(nose_offset), 4),
        "anomaly_score": round(min(1.0, geom_anomaly), 4),
        "confidence": 0.75,
        "methodology": "Biometric 5-point facial landmark geometric symmetry and axial alignment"
    }
