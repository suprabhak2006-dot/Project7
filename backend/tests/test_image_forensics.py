import numpy as np
from backend.forensic.image.forensic_modules import (
    analyze_jpeg_compression,
    analyze_noise_distribution,
    analyze_frequency_spectrum,
    analyze_lighting_consistency,
    analyze_landmark_geometry
)

def test_jpeg_compression_ela():
    # Create test image
    img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
    res = analyze_jpeg_compression(img)
    assert "mean_error" in res
    assert "error_std_dev" in res
    assert "anomaly_score" in res
    assert 0.0 <= res["anomaly_score"] <= 1.0

def test_noise_distribution():
    img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    res = analyze_noise_distribution(img, face_box=[50, 50, 80, 80])
    assert "global_noise_variance" in res
    assert "face_noise_variance" in res
    assert "anomaly_score" in res
    assert 0.0 <= res["anomaly_score"] <= 1.0

def test_frequency_spectrum_2d_fft():
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    # Add synthetic grid lines (high frequency artifact)
    img[::8, :] = 255
    res = analyze_frequency_spectrum(img)
    assert "frequency_energy_ratio" in res
    assert "anomaly_score" in res
    assert 0.0 <= res["anomaly_score"] <= 1.0

def test_lighting_consistency():
    img = np.full((200, 200, 3), 128, dtype=np.uint8)
    res = analyze_lighting_consistency(img, face_box=[40, 40, 60, 60])
    assert "illumination_angle_disparity_deg" in res
    assert "anomaly_score" in res
    assert 0.0 <= res["anomaly_score"] <= 1.0

def test_landmark_geometry():
    # Simulated symmetrical facial landmarks: RE, LE, NT, RM, LM
    landmarks = [
        [100.0, 100.0],
        [200.0, 100.0],
        [150.0, 150.0],
        [110.0, 200.0],
        [190.0, 200.0]
    ]
    res = analyze_landmark_geometry(landmarks)
    assert "facial_symmetry_ratio" in res
    assert res["facial_symmetry_ratio"] > 0.8
    assert "anomaly_score" in res
    assert res["anomaly_score"] < 0.3
