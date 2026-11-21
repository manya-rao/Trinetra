import io, json, datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, ObjectIdentifier
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import c2pa
from PIL import Image

# 2-tier: Root CA + End Entity Cert
root_key = ec.generate_private_key(ec.SECP256R1())
root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Test Root CA')])
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
    x509.NameAttribute(NameOID.COMMON_NAME, 'self-signed DEMO signer'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Trinetra DEMO Authority')
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
        ObjectIdentifier('1.3.6.1.4.1.59341.1.1.1'),
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
    alg=b'es256',
    sign_cert=cert_chain_pem,
    private_key=ee_key_pem,
    ta_url=None
)
signer = c2pa.Signer.from_info(signer_info)

img = Image.new('RGB', (200, 200), color=(100, 150, 200))
src_stream = io.BytesIO()
img.save(src_stream, format='JPEG', quality=90)
src_stream.seek(0)

builder = c2pa.Builder({
    'claim_generator': 'Trinetra Test Builder',
    'title': 'Test Signed Image',
    'assertions': [{
        'label': 'c2pa.actions',
        'data': {
            'actions': [{
                'action': 'c2pa.created',
                'digitalSourceType': 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia',
                'softwareAgent': 'Generative AI Engine (self-signed DEMO signer)'
            }]
        }
    }]
})

out = io.BytesIO()
builder.sign(signer, 'image/jpeg', src_stream, out)
signed_bytes = out.getvalue()
print('SUCCESS! Signed image size:', len(signed_bytes))

# Now test Reader on the signed bytes!
reader = c2pa.Reader('image/jpeg', io.BytesIO(signed_bytes))
print('Reader active manifest:')
active = reader.get_active_manifest()
print('  title:', active.get('title'))
print('  claim_generator:', active.get('claim_generator'))
print('  signature_info:', active.get('signature_info'))
print('  assertions:')
for a in active.get('assertions', []):
    print('   ', a.get('label'), a.get('data'))

manifest_data = json.loads(reader.json())
print('Validation status in manifest_data:', manifest_data.get('validation_status'))
