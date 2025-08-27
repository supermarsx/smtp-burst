import ssl
import socket
import threading
from datetime import datetime, timedelta

import pytest

from smtpburst import tlstest

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
except ImportError:
    pytest.skip("cryptography not available", allow_module_level=True)


def _generate_cert(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(days=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


def _start_server(certfile, keyfile):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile, keyfile)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    sock = socket.socket()
    sock.bind(("localhost", 0))
    sock.listen(5)
    port = sock.getsockname()[1]
    stop = threading.Event()

    def run():
        sock.settimeout(0.1)
        while not stop.is_set():
            try:
                conn, _ = sock.accept()
            except socket.timeout:
                continue
            with ctx.wrap_socket(
                conn,
                server_side=True,
                do_handshake_on_connect=False,
            ) as s:
                try:
                    s.do_handshake()
                    s.recv(1)
                except Exception:
                    pass
        sock.close()

    th = threading.Thread(target=run, daemon=True)
    th.start()
    return port, stop, th


def test_tls_self_signed(tmp_path):
    cert, key = _generate_cert(tmp_path)
    port, stop, th = _start_server(cert, key)
    try:
        res = tlstest.test_versions("localhost", port)
    finally:
        stop.set()
        th.join()
    assert res["TLSv1"]["supported"] is False
    assert res["TLSv1_2"]["supported"] is True
    assert res["TLSv1_2"]["valid"] is False
    assert res["TLSv1_2"]["protocol"] in {"TLSv1.2", "TLSv1.3"}
