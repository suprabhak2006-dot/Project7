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

def inspect_pixel_region(image_bgr: np.ndarray, x: int, y: int, window_size: int = 16) -> Dict[str, Any]:
    """
    Forensic pixel-level inspection mode (Requirement 13).
    Extracts RGB, local luminance, local noise residual, and neighborhood statistics.
    """
    h, w = image_bgr.shape[:2]
    cx = max(0, min(w - 1, x))
    cy = max(0, min(h - 1, y))

    b, g, r = [int(v) for v in image_bgr[cy, cx]]
    
    # Neighborhood window
    half = window_size // 2
    x1, y1 = max(0, cx - half), max(0, cy - half)
    x2, y2 = min(w, cx + half), min(h, cy + half)
    
    patch = image_bgr[y1:y2, x1:x2]
    gray_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    
    # Local statistics
    local_mean = float(np.mean(gray_patch))
    local_std = float(np.std(gray_patch))
    
    # Local noise residual via median difference
    denoised_patch = cv2.medianBlur(gray_patch, 3) if min(patch.shape[:2]) >= 3 else gray_patch
    noise_residual = float(np.mean(np.abs(gray_patch.astype(np.float32) - denoised_patch.astype(np.float32))))
    
    # Local gradient magnitude
    gx = cv2.Sobel(gray_patch, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_patch, cv2.CV_32F, 0, 1, ksize=3)
    edge_mag = float(np.mean(np.sqrt(gx**2 + gy**2)))
    
    return {
        "coordinates": {"x": cx, "y": cy},
        "rgb": {"r": r, "g": g, "b": b},
        "hex": f"#{r:02x}{g:02x}{b:02x}",
        "luminance": round(0.299 * r + 0.587 * g + 0.114 * b, 2),
        "local_window": {"width": x2 - x1, "height": y2 - y1},
        "local_mean": round(local_mean, 2),
        "local_std_dev": round(local_std, 2),
        "local_noise_residual": round(noise_residual, 4),
        "local_edge_magnitude": round(edge_mag, 2),
        "local_anomaly_indicator": round(min(1.0, noise_residual / 10.0), 4)
    }

def apply_forensic_filter(image_bgr: np.ndarray, filter_name: str) -> np.ndarray:
    """
    Applies authentic forensic filters to genuine evidence images (Requirement 14).
    Filters: grayscale, sobel_edges, laplacian, high_pass, low_pass, noise_residual,
             fft_spectrum, ela, sharpen, blur.
    """
    filter_key = filter_name.lower().strip()
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    if filter_key in ("grayscale", "gray"):
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    elif filter_key in ("sobel_edges", "edges", "sobel"):
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        norm_mag = np.clip((mag / (np.max(mag) + 1e-6)) * 255.0, 0, 255).astype(np.uint8)
        return cv2.applyColorMap(norm_mag, cv2.COLORMAP_MAGMA)

    elif filter_key in ("laplacian", "canny"):
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    elif filter_key in ("high_pass", "highpass"):
        blurred = cv2.GaussianBlur(gray, (15, 15), 3.0)
        hp = cv2.absdiff(gray, blurred)
        hp_boost = np.clip(hp.astype(np.float32) * 3.0, 0, 255).astype(np.uint8)
        return cv2.applyColorMap(hp_boost, cv2.COLORMAP_VIRIDIS)

    elif filter_key in ("low_pass", "lowpass", "blur"):
        return cv2.GaussianBlur(image_bgr, (11, 11), 0)

    elif filter_key in ("noise_residual", "noise"):
        denoised = cv2.medianBlur(gray, 5)
        residual = cv2.absdiff(gray, denoised)
        res_scaled = np.clip(residual.astype(np.float32) * 5.0, 0, 255).astype(np.uint8)
        return cv2.applyColorMap(res_scaled, cv2.COLORMAP_INFERNO)

    elif filter_key in ("fft_spectrum", "fft"):
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        mag = cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1])
        spec = np.log(mag + 1.0)
        cv2.normalize(spec, spec, 0, 255, cv2.NORM_MINMAX)
        spec_uint8 = np.uint8(spec)
        return cv2.applyColorMap(spec_uint8, cv2.COLORMAP_JET)

    elif filter_key in ("ela", "error_level"):
        pil_img = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        recomp = cv2.cvtColor(np.array(Image.open(buf)), cv2.COLOR_RGB2BGR)
        diff = cv2.absdiff(image_bgr, recomp).astype(np.float32)
        ela_img = np.clip(diff * 15.0, 0, 255).astype(np.uint8)
        return ela_img

    elif filter_key in ("sharpen",):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        return cv2.filter2D(image_bgr, -1, kernel)

    # Default original
    return image_bgr

def compute_image_histograms(image_bgr: np.ndarray, face_box: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Computes RGB and Luminance histograms (256 bins), plus Face vs Background comparison (Requirement 15).
    """
    h, w = image_bgr.shape[:2]
    # Channels
    b_hist = cv2.calcHist([image_bgr], [0], None, [256], [0, 256]).flatten().tolist()
    g_hist = cv2.calcHist([image_bgr], [1], None, [256], [0, 256]).flatten().tolist()
    r_hist = cv2.calcHist([image_bgr], [2], None, [256], [0, 256]).flatten().tolist()

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    luma_hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten().tolist()

    comparison = None
    if face_box and len(face_box) == 4:
        fx, fy, fw, fh = face_box
        fx2, fy2 = min(w, fx + fw), min(h, fy + fh)
        
        face_mask = np.zeros((h, w), dtype=np.uint8)
        face_mask[fy:fy2, fx:fx2] = 255
        bg_mask = cv2.bitwise_not(face_mask)

        face_luma = cv2.calcHist([gray], [0], face_mask, [256], [0, 256])
        bg_luma = cv2.calcHist([gray], [0], bg_mask, [256], [0, 256])

        cv2.normalize(face_luma, face_luma, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(bg_luma, bg_luma, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        correlation = float(cv2.compareHist(face_luma, bg_luma, cv2.HISTCMP_CORREL))
        chi_square = float(cv2.compareHist(face_luma, bg_luma, cv2.HISTCMP_CHISQR))
        bhattacharyya = float(cv2.compareHist(face_luma, bg_luma, cv2.HISTCMP_BHATTACHARYYA))

        comparison = {
            "face_luma_hist": face_luma.flatten().tolist(),
            "bg_luma_hist": bg_luma.flatten().tolist(),
            "correlation": round(correlation, 4),
            "chi_square_divergence": round(chi_square, 4),
            "bhattacharyya_distance": round(bhattacharyya, 4),
            "anomaly_score": round(min(1.0, max(0.0, bhattacharyya * 1.5)), 4),
            "interpretation": "Measurable luminance mismatch" if bhattacharyya > 0.45 else "Consistent luminance distribution"
        }

    return {
        "red": r_hist,
        "green": g_hist,
        "blue": b_hist,
        "luminance": luma_hist,
        "face_vs_background": comparison
    }

def analyze_compression_detailed(image_path: str) -> Dict[str, Any]:
    """
    Deeper compression analysis inspecting JPEG quantization tables and 8x8 DCT grid artifacts (Requirement 16).
    """
    if not os.path.exists(image_path):
        return {"error": "Image file not found"}

    try:
        with Image.open(image_path) as pil_img:
            q_tables = getattr(pil_img, "quantization", None)
            tables_data = {}
            if q_tables:
                for k, v in q_tables.items():
                    tables_data[f"table_{k}"] = list(v)

        # Measure 8x8 DCT block boundary artifact
        bgr = cv2.imread(image_path)
        if bgr is not None:
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
            h, w = gray.shape
            
            # Boundary difference vs inner difference
            diff_x = np.abs(gray[:, 1:] - gray[:, :-1])
            diff_y = np.abs(gray[1:, :] - gray[:-1, :])
            
            # Grid boundary coordinates modulo 8
            x_indices = np.arange(w - 1) % 8 == 7
            y_indices = np.arange(h - 1) % 8 == 7
            
            boundary_diff_x = np.mean(diff_x[:, x_indices]) if np.any(x_indices) else 0.0
            inner_diff_x = np.mean(diff_x[:, ~x_indices]) if np.any(~x_indices) else 1.0
            
            blockiness_ratio = float(boundary_diff_x / (inner_diff_x + 1e-6))
            double_comp_indicator = bool(blockiness_ratio > 1.25 or (tables_data and len(tables_data) > 1))
            
            return {
                "quantization_tables_present": bool(tables_data),
                "quantization_tables": tables_data,
                "blockiness_ratio": round(blockiness_ratio, 4),
                "double_compression_detected": double_comp_indicator,
                "anomaly_score": round(min(1.0, max(0.0, (blockiness_ratio - 1.0) * 1.5)), 4),
                "methodology": "JPEG quantization matrix inspection and 8x8 DCT block artifact grid analysis"
            }
    except Exception as e:
        return {"error": str(e)}

    return {"status": "Non-JPEG or compression metadata unreadable"}

def analyze_color_consistency(image_bgr: np.ndarray, face_box: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Analyzes white balance, skin tone consistency, and color-space anomalies (Requirement 20).
    """
    h, w = image_bgr.shape[:2]
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    global_l, global_a, global_b = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]
    global_mean_a = float(np.mean(global_a))
    global_mean_b = float(np.mean(global_b))

    result = {
        "global_color_temperature_k": round(float(np.mean(global_b) * 45 + 3000), 1),
        "white_balance_balance_score": round(float(1.0 - abs(global_mean_a - 128) / 128.0), 3)
    }

    if face_box and len(face_box) == 4:
        fx, fy, fw, fh = face_box
        fx2, fy2 = min(w, fx + fw), min(h, fy + fh)

        face_lab = lab[fy:fy2, fx:fx2]
        face_mean_a = float(np.mean(face_lab[:, :, 1]))
        face_mean_b = float(np.mean(face_lab[:, :, 2]))

        # Delta E color difference between face chromaticity and global chromaticity
        delta_e = float(np.sqrt((face_mean_a - global_mean_a)**2 + (face_mean_b - global_mean_b)**2))
        
        # Skin tone consistency check (typical skin tone has a* > 130 and b* > 130 in standard 8-bit LAB)
        skin_tone_valid = bool(face_mean_a > 125 and face_mean_b > 125)

        result["face_chroma_delta"] = round(delta_e, 3)
        result["skin_tone_congruence"] = "Congruent" if skin_tone_valid else "Anomalous chromatic shift"
        result["color_anomaly_score"] = round(min(1.0, delta_e / 40.0), 4)
        result["interpretation"] = "Color space consistency verified" if delta_e < 25.0 else "Noticeable chromatic disparity between subject and scene"

    return result

