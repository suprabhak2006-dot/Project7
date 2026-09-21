from typing import Dict, Any, List, Optional
import numpy as np

class EvidenceFusionEngine:
    """
    Transparent Multimodal Forensic Evidence Fusion Engine.
    Combines AI predictions, temporal dynamics, signal analysis, and physical forensics.
    Provides conflict detection when disparate modalities contradict each other.
    """
    # Documented module weights and intrinsic reliability priors
    MODULE_CONFIG = {
        "vision_ai": {"weight": 0.35, "reliability": 0.85, "category": "AI_MODEL"},
        "temporal_consistency": {"weight": 0.20, "reliability": 0.80, "category": "TEMPORAL_ANALYSIS"},
        "compression_ela": {"weight": 0.10, "reliability": 0.75, "category": "FORENSIC_ALGORITHM"},
        "noise_distribution": {"weight": 0.10, "reliability": 0.75, "category": "FORENSIC_ALGORITHM"},
        "frequency_spectrum": {"weight": 0.10, "reliability": 0.75, "category": "FORENSIC_ALGORITHM"},
        "landmark_geometry": {"weight": 0.05, "reliability": 0.70, "category": "FORENSIC_ALGORITHM"},
        "av_sync": {"weight": 0.10, "reliability": 0.75, "category": "SIGNAL_ANALYSIS"},
        "audio_signal": {"weight": 0.08, "reliability": 0.70, "category": "SIGNAL_ANALYSIS"},
        "metadata": {"weight": 0.05, "reliability": 0.65, "category": "METADATA_ANALYSIS"}
    }

    def fuse_evidence(self, observations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        observations: dict of module results:
        {
            'vision_ai': {'score': float, 'confidence': float, 'available': bool, ...},
            'temporal_consistency': {...},
            'compression_ela': {...},
            'noise_distribution': {...},
            'frequency_spectrum': {...},
            'landmark_geometry': {...},
            'av_sync': {...},
            'audio_signal': {...},
            'metadata': {...}
        }
        """
        valid_modules = {}
        total_weight = 0.0
        weighted_score_sum = 0.0
        weighted_conf_sum = 0.0

        scores = []
        confidences = []
        module_names = []

        for mod_key, mod_info in self.MODULE_CONFIG.items():
            obs = observations.get(mod_key)
            if obs and obs.get("available", True) and obs.get("score") is not None:
                score = float(obs["score"])
                conf = float(obs.get("confidence", mod_info["reliability"]))
                weight = mod_info["weight"]

                effective_weight = weight * conf
                weighted_score_sum += score * effective_weight
                weighted_conf_sum += conf * weight
                total_weight += weight

                valid_modules[mod_key] = {
                    "score": round(score, 4),
                    "confidence": round(conf, 4),
                    "category": mod_info["category"],
                    "description": obs.get("description", "")
                }
                scores.append(score)
                confidences.append(conf)
                module_names.append(mod_key)

        if total_weight == 0.0 or len(scores) == 0:
            return {
                "final_score": 0.0,
                "confidence": 0.0,
                "assessment": "INCONCLUSIVE",
                "evidence_conflict": False,
                "conflict_details": None,
                "indicators": {"supporting": 0, "neutral": 0, "contradictory": 0},
                "fusion_methodology": "No valid forensic module outputs available",
                "findings": []
            }

        final_score = weighted_score_sum / (sum(self.MODULE_CONFIG[k]["weight"] * valid_modules[k]["confidence"] for k in valid_modules) + 1e-6)
        final_score = max(0.0, min(1.0, float(final_score)))
        overall_confidence = float(weighted_conf_sum / total_weight)

        # Count Forensic Indicators
        supporting_count = sum(1 for s in scores if s >= 0.60)
        neutral_count = sum(1 for s in scores if 0.40 <= s < 0.60)
        contradictory_count = sum(1 for s in scores if s < 0.40)

        # Conflict Detection:
        # Check if Vision AI differs strongly from Physical Forensics (noise, compression, metadata)
        evidence_conflict = False
        conflict_details = None

        if len(scores) >= 2:
            max_score = max(scores)
            min_score = min(scores)
            divergence = max_score - min_score
            
            # Substantial divergence between reliable modules
            if divergence >= 0.55:
                evidence_conflict = True
                high_mods = [module_names[i] for i, s in enumerate(scores) if s >= 0.65]
                low_mods = [module_names[i] for i, s in enumerate(scores) if s <= 0.35]
                conflict_details = (
                    f"Evidence Conflict Detected: Divergence of {divergence:.2f} across modules. "
                    f"Modules indicating high manipulation: [{', '.join(high_mods)}]. "
                    f"Modules indicating low manipulation: [{', '.join(low_mods)}]. "
                    f"Independent forensic review recommended."
                )

        # Determine Assessment
        if evidence_conflict:
            assessment = "EVIDENCE_CONFLICT"
        elif final_score >= 0.70:
            assessment = "HIGH_MANIPULATION_LIKELIHOOD"
        elif final_score >= 0.40:
            assessment = "MODERATE_MANIPULATION_LIKELIHOOD"
        elif overall_confidence < 0.50:
            assessment = "INCONCLUSIVE"
        else:
            assessment = "LOW_MANIPULATION_LIKELIHOOD"

        # Generate structured findings
        findings = self._generate_findings(valid_modules, observations)

        return {
            "final_score": round(final_score, 4),
            "confidence": round(overall_confidence, 4),
            "assessment": assessment,
            "evidence_conflict": evidence_conflict,
            "conflict_details": conflict_details,
            "indicators": {
                "supporting": supporting_count,
                "neutral": neutral_count,
                "contradictory": contradictory_count
            },
            "modules_evaluated": valid_modules,
            "fusion_methodology": (
                "Confidence-weighted multi-signal linear aggregation with prior module reliability "
                "and automated divergence conflict detection."
            ),
            "findings": findings
        }

    def _generate_findings(self, valid_modules: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        finding_counter = 1

        for mod_key, data in valid_modules.items():
            score = data["score"]
            conf = data["confidence"]
            cat = data["category"]

            # Severity mapping
            if score >= 0.80:
                severity = "CRITICAL" if score >= 0.90 else "HIGH"
            elif score >= 0.60:
                severity = "MEDIUM"
            elif score >= 0.40:
                severity = "LOW"
            else:
                severity = "INFO"

            # Generate formal finding if notable
            obs_data = observations.get(mod_key, {})
            desc = obs_data.get("description")
            if not desc:
                if score >= 0.60:
                    desc = f"Forensic indicator detected in {mod_key.replace('_', ' ')} (measured score: {score:.2f})."
                else:
                    desc = f"Analysis of {mod_key.replace('_', ' ')} shows consistent/nominal patterns (score: {score:.2f})."

            findings.append({
                "finding_code": f"FND-{finding_counter:04d}",
                "category": cat,
                "severity": severity,
                "confidence": conf,
                "score": score,
                "description": desc,
                "model_name": obs_data.get("model_name", mod_key),
                "model_version": obs_data.get("model_version", "1.0"),
                "raw_output": obs_data.get("raw_output", {}),
                "timestamp": obs_data.get("timestamp"),
                "frame_number": obs_data.get("frame_number"),
                "bounding_box": obs_data.get("bounding_box")
            })
            finding_counter += 1

        return findings
