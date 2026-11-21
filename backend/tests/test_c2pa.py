import io
import json
import datetime
import pytest
from PIL import Image
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, ObjectIdentifier
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend.c2pa_check import check_c2pa, is_c2pa_available
from backend.aggregator import aggregate


def create_c2pa_signed_test_image(tamper: bool = False) -> bytes:
    """Helper to build and cryptographically sign a test image using c2pa-python."""
    import c2pa

    # 1. Generate ES256 key and certificate chain
    root_key = ec.generate_private_key(ec.SECP256R1())
    root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Root CA")])
    root_cert = x509.CertificateBuilder().subject_name(
        root_name
    ).issuer_name(
        root_name
    ).public_key(
        root_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=1), critical=True
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=True,
            crl_sign=True, encipher_only=False, decipher_only=False
        ), critical=True
    ).add_extension(
        x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()), critical=False
    ).sign(root_key, hashes.SHA256())

    ee_key = ec.generate_private_key(ec.SECP256R1())
    ee_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "self-signed DEMO signer"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Trinetra DEMO Authority")
    ])
    ee_cert = x509.CertificateBuilder().subject_name(
        ee_name
    ).issuer_name(
        root_name
    ).public_key(
        ee_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True, content_commitment=True, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=False,
            crl_sign=False, encipher_only=False, decipher_only=False
        ), critical=True
    ).add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.EMAIL_PROTECTION,
            ExtendedKeyUsageOID.CODE_SIGNING,
            ObjectIdentifier("1.3.6.1.4.1.59341.1.1.1"),
        ]), critical=False
    ).add_extension(
        x509.SubjectKeyIdentifier.from_public_key(ee_key.public_key()), critical=False
    ).add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(root_key.public_key()), critical=False
    ).sign(root_key, hashes.SHA256())

    cert_chain_pem = ee_cert.public_bytes(serialization.Encoding.PEM) + root_cert.public_bytes(serialization.Encoding.PEM)
    ee_key_pem = ee_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    signer_info = c2pa.C2paSignerInfo(
        alg=b"es256",
        sign_cert=cert_chain_pem,
        private_key=ee_key_pem,
        ta_url=None
    )
    signer = c2pa.Signer.from_info(signer_info)

    # 2. Source image
    img = Image.new("RGB", (160, 160), color=(80, 130, 190))
    src_stream = io.BytesIO()
    img.save(src_stream, format="JPEG", quality=90)
    src_stream.seek(0)

    manifest_json = {
        "claim_generator": "Trinetra Test Builder",
        "title": "C2PA Test Image",
        "assertions": [{
            "label": "c2pa.actions",
            "data": {
                "actions": [{
                    "action": "c2pa.created",
                    "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia",
                    "softwareAgent": "Generative AI Engine (self-signed DEMO signer)"
                }]
            }
        }]
    }

    builder = c2pa.Builder(manifest_json)
    out_stream = io.BytesIO()
    builder.sign(signer, "image/jpeg", src_stream, out_stream)
    signed_bytes = out_stream.getvalue()

    if tamper:
        # Tamper bytes in the image data to break dataHash
        mutated = bytearray(signed_bytes)
        mutated[1200:1250] = b"\x00" * 50
        return bytes(mutated)

    return signed_bytes


@pytest.mark.skipif(not is_c2pa_available(), reason="c2pa-python not installed")
def test_real_signed_c2pa_gives_ai_confirmed():
    """A real signed file must validate, return valid status, and yield ai_confirmed."""
    signed_jpeg = create_c2pa_signed_test_image(tamper=False)
    res = check_c2pa(signed_jpeg)
    assert res["status"] == "valid", f"Expected valid, got: {res}"
    assert res["ai_generated"] is True, "Expected ai_generated to be True from manifest"
    assert "self-signed DEMO signer" in res["issuer"], f"Expected self-signed DEMO signer, got: {res['issuer']}"

    # Test that aggregator produces ai_confirmed with synthesis=confirmed
    passport = aggregate(phash_match=None, diff_result=None, c2pa=res, ml_output=None)
    assert passport["verdict"] == "ai_confirmed"
    assert passport["eyes"]["synthesis"] == "confirmed"


@pytest.mark.skipif(not is_c2pa_available(), reason="c2pa-python not installed")
def test_forged_c2pa_bytes_must_not_give_ai_confirmed():
    """Forged 'c2pa' bytes on a normal JPEG must NOT return valid or give ai_confirmed."""
    img = Image.new("RGB", (100, 100), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    # Append forged strings
    forged_bytes = buf.getvalue() + b"c2pa JUMBF fake manifest generator"

    res = check_c2pa(forged_bytes)
    assert res["status"] in ("none", "invalid"), f"Status must NOT be valid: {res}"
    assert res["ai_generated"] is False

    passport = aggregate(phash_match=None, diff_result=None, c2pa=res, ml_output=None)
    assert passport["verdict"] != "ai_confirmed"


@pytest.mark.skipif(not is_c2pa_available(), reason="c2pa-python not installed")
def test_tampered_signed_c2pa_gives_invalid():
    """A signed image with tampered payload bytes must be caught as invalid."""
    tampered_bytes = create_c2pa_signed_test_image(tamper=True)
    res = check_c2pa(tampered_bytes)
    assert res["status"] in ("invalid", "none"), f"Expected invalid or none, got: {res}"
    assert res["ai_generated"] is False

    passport = aggregate(phash_match=None, diff_result=None, c2pa=res, ml_output=None)
    assert passport["verdict"] != "ai_confirmed"


def test_plain_jpeg_gives_none():
    """A standard JPEG with no manifest must return status 'none'."""
    img = Image.new("RGB", (80, 80), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    res = check_c2pa(buf.getvalue())
    assert res["status"] == "none"
    assert res["issuer"] is None
    assert res["ai_generated"] is False
