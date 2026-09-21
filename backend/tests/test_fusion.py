from backend.forensic.fusion.engine import EvidenceFusionEngine

def test_evidence_fusion_normal():
    engine = EvidenceFusionEngine()
    observations = {
        "vision_ai": {"score": 0.85, "confidence": 0.90, "available": True, "description": "High manipulation in face"},
        "temporal_consistency": {"score": 0.78, "confidence": 0.85, "available": True, "description": "Facial landmark drift"},
        "compression_ela": {"score": 0.72, "confidence": 0.80, "available": True, "description": "Quantization disparity"},
    }
    result = engine.fuse_evidence(observations)
    assert result["final_score"] > 0.70
    assert result["assessment"] == "HIGH_MANIPULATION_LIKELIHOOD"
    assert result["evidence_conflict"] is False
    assert len(result["findings"]) == 3

def test_evidence_fusion_conflict_detection():
    engine = EvidenceFusionEngine()
    # Severe contradiction: AI detector flags 0.92, while physical noise and compression indicate 0.10
    observations = {
        "vision_ai": {"score": 0.92, "confidence": 0.90, "available": True, "description": "AI predicts fake"},
        "noise_distribution": {"score": 0.12, "confidence": 0.85, "available": True, "description": "Consistent sensor noise"},
        "compression_ela": {"score": 0.10, "confidence": 0.85, "available": True, "description": "Uniform compression grid"},
    }
    result = engine.fuse_evidence(observations)
    assert result["evidence_conflict"] is True
    assert result["assessment"] == "EVIDENCE_CONFLICT"
    assert "Evidence Conflict Detected" in result["conflict_details"]
