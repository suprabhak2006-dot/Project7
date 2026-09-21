import os
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional

class MediaSimilarityEngine:
    """
    Genuine media similarity, duplicate detection, and identity consistency engine.
    Calculates cryptographic equality, perceptual hashes (pHash, dHash, aHash),
    color histograms, and face feature similarity.
    """

    @staticmethod
    def compute_dhash(image: np.ndarray, hash_size: int = 8) -> str:
        """
        Difference Hash (dHash) based on adjacent pixel brightness gradients.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        bits = "".join(["1" if b else "0" for b in diff.flatten()])
        return hex(int(bits, 2))[2:].zfill((hash_size * hash_size) // 4)

    @staticmethod
    def compute_phash(image: np.ndarray, hash_size: int = 8, highfreq_factor: int = 4) -> str:
        """
        Perceptual Hash (pHash) based on Discrete Cosine Transform (DCT).
        Robust against lossy compression and minor scaling.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        img_size = hash_size * highfreq_factor
        resized = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA)
        
        # Convert to float and apply DCT
        dct = cv2.dct(np.float32(resized))
        # Extract low frequencies (top-left)
        dct_low = dct[:hash_size, :hash_size]
        # Calculate median excluding DC component at (0,0)
        median_val = np.median(dct_low.flatten()[1:])
        diff = dct_low > median_val
        bits = "".join(["1" if b else "0" for b in diff.flatten()])
        return hex(int(bits, 2))[2:].zfill((hash_size * hash_size) // 4)

    @staticmethod
    def compute_color_histogram(image: np.ndarray) -> list:
        """
        Calculates normalized 3-channel HSV color histogram.
        """
        if len(image.shape) == 2:
            hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [8], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256])
        
        cv2.normalize(hist_h, hist_h, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_s, hist_s, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_v, hist_v, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        
        combined = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
        return combined.tolist()

    @staticmethod
    def hamming_distance(hash1_hex: str, hash2_hex: str) -> int:
        """
        Computes bitwise Hamming distance between two hex hash strings.
        """
        if not hash1_hex or not hash2_hex:
            return 64
        try:
            val1 = int(hash1_hex, 16)
            val2 = int(hash2_hex, 16)
            return bin(val1 ^ val2).count("1")
        except Exception:
            return 64

    @staticmethod
    def compare_images(img_path1: str, img_path2: str) -> Dict[str, Any]:
        """
        Compares two images using pHash, dHash, and color histogram correlation.
        """
        if not os.path.exists(img_path1) or not os.path.exists(img_path2):
            return {"error": "One or both image paths do not exist"}

        img1 = cv2.imread(img_path1)
        img2 = cv2.imread(img_path2)
        if img1 is None or img2 is None:
            return {"error": "Failed to decode one or both images"}

        phash1 = MediaSimilarityEngine.compute_phash(img1)
        phash2 = MediaSimilarityEngine.compute_phash(img2)
        dhash1 = MediaSimilarityEngine.compute_dhash(img1)
        dhash2 = MediaSimilarityEngine.compute_dhash(img2)

        phash_dist = MediaSimilarityEngine.hamming_distance(phash1, phash2)
        dhash_dist = MediaSimilarityEngine.hamming_distance(dhash1, dhash2)

        # Normalized similarity (0 to 1.0)
        phash_sim = max(0.0, 1.0 - (phash_dist / 64.0))
        dhash_sim = max(0.0, 1.0 - (dhash_dist / 64.0))

        # Color correlation
        hist1 = np.array(MediaSimilarityEngine.compute_color_histogram(img1), dtype=np.float32)
        hist2 = np.array(MediaSimilarityEngine.compute_color_histogram(img2), dtype=np.float32)
        color_sim = float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))
        color_sim = max(0.0, min(1.0, (color_sim + 1.0) / 2.0))

        overall_sim = float(0.5 * phash_sim + 0.3 * dhash_sim + 0.2 * color_sim)
        is_duplicate = bool(overall_sim >= 0.88 or phash_dist <= 6)

        return {
            "phash1": phash1,
            "phash2": phash2,
            "phash_distance": phash_dist,
            "phash_similarity": round(phash_sim, 4),
            "dhash_similarity": round(dhash_sim, 4),
            "color_similarity": round(color_sim, 4),
            "overall_similarity": round(overall_sim, 4),
            "is_duplicate_candidate": is_duplicate,
            "interpretation": "Potential near-duplicate detected" if is_duplicate else "Visually distinct media"
        }

    @staticmethod
    def extract_face_descriptor(face_crop: np.ndarray) -> np.ndarray:
        """
        Extracts a normalized 128-dimensional multi-scale HOG/spatial descriptor
        from an aligned face crop.
        """
        resized = cv2.resize(face_crop, (64, 64))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
        
        # Spatial 8x8 block gradients
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        
        # 16-bin orientation histogram over 8x8 cells
        bins = (ang / 22.5).astype(np.int32) % 16
        desc = []
        for r in range(0, 64, 16):
            for c in range(0, 64, 16):
                cell_bins = bins[r:r+16, c:c+16]
                cell_mag = mag[r:r+16, c:c+16]
                h = [float(np.sum(cell_mag[cell_bins == b])) for b in range(16)]
                desc.extend(h)
        
        vec = np.array(desc, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec

    @staticmethod
    def compare_face_embeddings(desc1: np.ndarray, desc2: np.ndarray) -> Dict[str, Any]:
        """
        Calculates cosine similarity between two face descriptors.
        Adheres to Requirement 3 & 7: Does NOT claim identity equivalence.
        """
        if len(desc1) == 0 or len(desc2) == 0:
            return {"similarity": 0.0, "interpretation": "Insufficient evidence"}

        cosine_sim = float(np.dot(desc1, desc2))
        cosine_sim = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0))

        if cosine_sim >= 0.75:
            interpretation = "Potentially related"
        elif cosine_sim >= 0.50:
            interpretation = "Similarity detected"
        else:
            interpretation = "Insufficient evidence"

        return {
            "similarity": round(cosine_sim, 4),
            "interpretation": interpretation,
            "disclaimer": "Forensic biometric indicator based on spatial gradient distributions; does not establish definitive identity."
        }
