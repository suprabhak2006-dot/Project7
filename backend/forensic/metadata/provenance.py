import os
import subprocess
import json
from typing import Dict, Any, List
from PIL import Image, ExifTags

class MediaProvenanceAnalyzer:
    """
    Analyzes media container structure, codec metadata, EXIF provenance,
    re-encoding signatures, and scans for PII/sensitive metadata.
    """

    @staticmethod
    def inspect_file_structure_and_provenance(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        original_indicators = []
        editing_indicators = []
        reencoding_indicators = []
        pii_warnings = []
        metadata_dict = {}

        # 1. Image inspection via PIL
        if ext in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"):
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    format_name = img.format
                    info = img.info

                    # Software and editing tags
                    software = info.get("Software") or info.get("software")
                    if software:
                        metadata_dict["software"] = str(software)
                        soft_lower = str(software).lower()
                        if any(kw in soft_lower for kw in ["photoshop", "gimp", "canva", "lightroom", "after effects", "premiere"]):
                            editing_indicators.append(f"Editing software tag detected: {software}")
                        else:
                            original_indicators.append(f"Camera firmware / capture software: {software}")

                    # EXIF extraction
                    exif_data = img.getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            # Convert bytes or un-serializable objects
                            val_str = str(value)
                            metadata_dict[tag_name] = val_str

                            # PII inspection (Requirement 72)
                            if "GPS" in tag_name or tag_name == "GPSInfo":
                                pii_warnings.append("GPS location data embedded in image metadata")
                            elif any(k in tag_name.lower() for k in ["serial", "device", "author", "artist", "owner"]):
                                pii_warnings.append(f"Potential hardware/personal identifier: {tag_name} = {val_str[:30]}")

                        if "Make" in metadata_dict and "Model" in metadata_dict:
                            original_indicators.append(f"Capture hardware signature: {metadata_dict['Make']} {metadata_dict['Model']}")
                        if "DateTimeOriginal" in metadata_dict:
                            original_indicators.append(f"Original capture timestamp present: {metadata_dict['DateTimeOriginal']}")
                    else:
                        editing_indicators.append("EXIF metadata stripped (common in web re-uploads or editing suites)")

            except Exception as e:
                editing_indicators.append(f"Metadata parser warning: {str(e)}")

        # 2. Video / Audio container inspection via FFprobe
        elif ext in (".mp4", ".mov", ".avi", ".mkv", ".wav", ".mp3"):
            try:
                cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0 and res.stdout:
                    probe_data = json.loads(res.stdout)
                    fmt = probe_data.get("format", {})
                    streams = probe_data.get("streams", [])

                    metadata_dict["container_format"] = fmt.get("format_name")
                    metadata_dict["duration"] = fmt.get("duration")
                    metadata_dict["bitrate"] = fmt.get("bit_rate")
                    metadata_dict["streams_count"] = len(streams)

                    tags = fmt.get("tags", {})
                    encoder = tags.get("encoder") or tags.get("major_brand")
                    if encoder:
                        metadata_dict["encoder"] = encoder
                        enc_lower = encoder.lower()
                        if any(kw in enc_lower for kw in ["lavf", "ffmpeg", "handbrake", "adobe", "capcut"]):
                            reencoding_indicators.append(f"Transcoding / editing encoder signature: {encoder}")
                        else:
                            original_indicators.append(f"Capture container brand: {encoder}")

                    for s in streams:
                        codec_type = s.get("codec_type")
                        codec_name = s.get("codec_name")
                        if codec_type == "video":
                            profile = s.get("profile")
                            pix_fmt = s.get("pix_fmt")
                            metadata_dict["video_codec"] = f"{codec_name} ({profile})"
                            metadata_dict["pixel_format"] = pix_fmt
                            if s.get("has_b_frames", 0) > 0:
                                original_indicators.append("Bidirectional (B-frame) GOP compression structure present")
                        elif codec_type == "audio":
                            metadata_dict["audio_codec"] = codec_name
                            metadata_dict["audio_sample_rate"] = s.get("sample_rate")

            except Exception as e:
                reencoding_indicators.append(f"Container inspector exception: {str(e)}")

        # Calculate Provenance Assessment
        prov_score = 0.5
        if original_indicators and not editing_indicators:
            prov_score = 0.85
            summary = "Consistent with camera/device original capture"
        elif editing_indicators and not original_indicators:
            prov_score = 0.25
            summary = "Signs of post-capture editing or metadata stripping"
        elif editing_indicators and original_indicators:
            prov_score = 0.55
            summary = "Mixed provenance indicators (camera metadata with re-encoding or editor tags)"
        else:
            summary = "Insufficient container metadata to establish provenance definitively"

        return {
            "original_capture_indicators": original_indicators or ["None detected"],
            "editing_indicators": editing_indicators or ["None detected"],
            "reencoding_indicators": reencoding_indicators or ["None detected"],
            "pii_warnings": pii_warnings,
            "provenance_confidence": "HIGH" if (original_indicators or editing_indicators) else "MODERATE",
            "provenance_score": prov_score,
            "assessment_summary": summary,
            "container_metadata": metadata_dict,
            "disclaimer": "Metadata and container indicators are investigative aids and do not alone prove malicious intent."
        }
