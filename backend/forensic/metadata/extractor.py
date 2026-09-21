import os
import json
import subprocess
from typing import Dict, Any, Optional
from PIL import Image, ExifTags
import imageio_ffmpeg

def extract_image_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extracts comprehensive EXIF and structural metadata from an image file.
    """
    metadata: Dict[str, Any] = {
        "format": None,
        "mode": None,
        "width": None,
        "height": None,
        "exif_present": False,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "datetime_original": None,
        "gps_info": None,
        "color_space": None,
        "suspicious_software_tag": False,
        "metadata_status": "NORMAL"
    }

    try:
        with Image.open(filepath) as img:
            metadata["format"] = img.format
            metadata["mode"] = img.mode
            metadata["width"] = img.width
            metadata["height"] = img.height

            exif_raw = img.getexif()
            if exif_raw:
                metadata["exif_present"] = True
                for tag_id, value in exif_raw.items():
                    tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                    if tag == "Make":
                        metadata["camera_make"] = str(value).strip()
                    elif tag == "Model":
                        metadata["camera_model"] = str(value).strip()
                    elif tag == "Software":
                        metadata["software"] = str(value).strip()
                    elif tag == "DateTime":
                        metadata["datetime_original"] = str(value).strip()
                    elif tag == "ColorSpace":
                        metadata["color_space"] = str(value)

                # Check for editing software tags
                known_editors = ["photoshop", "gimp", "deepfacelab", "facefusion", "faceswap", "stable diffusion", "midjourney"]
                if metadata["software"]:
                    soft_lower = metadata["software"].lower()
                    for editor in known_editors:
                        if editor in soft_lower:
                            metadata["suspicious_software_tag"] = True
                            metadata["metadata_status"] = "INCONSISTENT_SOFTWARE_TAG"
                            break

            if not metadata["exif_present"]:
                metadata["metadata_status"] = "METADATA_STRIPPED_OR_MISSING"

    except Exception as e:
        metadata["error"] = str(e)
        metadata["metadata_status"] = "EXTRACTION_ERROR"

    return metadata

def extract_video_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extracts video and audio stream information using FFprobe/FFmpeg.
    """
    metadata: Dict[str, Any] = {
        "container": os.path.splitext(filepath)[1].lower().lstrip("."),
        "width": None,
        "height": None,
        "fps": None,
        "duration": None,
        "video_codec": None,
        "audio_codec": None,
        "bitrate": None,
        "has_audio": False,
        "encoder": None,
        "metadata_status": "NORMAL"
    }

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    try:
        # Run ffmpeg -i <file>
        cmd = [ffmpeg_exe, "-hide_banner", "-i", filepath]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        output = res.stderr

        for line in output.splitlines():
            line_str = line.strip()
            # Duration: 00:00:10.50, start: 0.000000, bitrate: 2500 kb/s
            if "Duration:" in line_str:
                parts = line_str.split(",")
                for p in parts:
                    if "Duration:" in p:
                        dur_str = p.split("Duration:")[1].strip()
                        try:
                            h, m, s = dur_str.split(":")
                            metadata["duration"] = round(float(h)*3600 + float(m)*60 + float(s), 2)
                        except Exception:
                            pass
                    elif "bitrate:" in p:
                        metadata["bitrate"] = p.split("bitrate:")[1].strip()

            # Stream #0:0: Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 30 fps, 30 tbr...
            if "Stream #" in line_str and "Video:" in line_str:
                v_part = line_str.split("Video:")[1].strip()
                parts = [x.strip() for x in v_part.split(",")]
                if len(parts) > 0:
                    metadata["video_codec"] = parts[0].split()[0]
                for p in parts:
                    if "x" in p and any(c.isdigit() for c in p):
                        dim_candidate = p.split()[0]
                        if "x" in dim_candidate and len(dim_candidate.split("x")) == 2:
                            try:
                                w_str, h_str = dim_candidate.split("x")
                                metadata["width"] = int(w_str)
                                metadata["height"] = int(h_str)
                            except Exception:
                                pass
                    if "fps" in p:
                        try:
                            metadata["fps"] = float(p.split("fps")[0].strip())
                        except Exception:
                            pass

            # Stream #0:1: Audio: aac (LC), 44100 Hz, stereo, fltp, 128 kb/s
            if "Stream #" in line_str and "Audio:" in line_str:
                metadata["has_audio"] = True
                a_part = line_str.split("Audio:")[1].strip()
                metadata["audio_codec"] = a_part.split(",")[0].strip()

            if "encoder" in line_str.lower():
                metadata["encoder"] = line_str

    except Exception as e:
        metadata["error"] = str(e)
        metadata["metadata_status"] = "EXTRACTION_ERROR"

    return metadata
