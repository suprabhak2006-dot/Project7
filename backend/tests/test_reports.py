import os
import pytest
from backend.app.services.report import compute_sha256

def test_compute_sha256():
    # Test hashing a known string
    test_file = "test_hash_sample.txt"
    try:
        with open(test_file, "w") as f:
            f.write("DEEPTRACE_FORENSIC_REPORT_TEST")
        h = compute_sha256(test_file)
        assert len(h) == 64
        assert isinstance(h, str)
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
