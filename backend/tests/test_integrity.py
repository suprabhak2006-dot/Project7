import os
import tempfile
import hashlib
from backend.app.api.evidence import compute_sha256_bytes, compute_sha256_file

def test_sha256_integrity_and_tampering():
    test_bytes = b"DIGITAL_FORENSIC_EVIDENCE_SAMPLE_BYTES"
    expected_hash = hashlib.sha256(test_bytes).hexdigest()
    
    assert compute_sha256_bytes(test_bytes) == expected_hash

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(test_bytes)
        f_path = f.name

    try:
        assert compute_sha256_file(f_path) == expected_hash

        # Tamper with 1 byte
        with open(f_path, "wb") as f:
            f.write(b"DIGITAL_FORENSIC_EVIDENCE_SAMPLE_BYTEZ")

        tampered_hash = compute_sha256_file(f_path)
        assert tampered_hash != expected_hash
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)
