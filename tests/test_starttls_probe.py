import ssl
from smtpburst.discovery import starttls_probe


def test_starttls_discover(monkeypatch):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.ctx = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

        def starttls(self, context=None):
            # Accept only TLSv1.2
            assert context is not None
            if context.maximum_version == ssl.TLSVersion.TLSv1_2:
                return (220, b"go")
            raise ssl.SSLError("unsupported")

    monkeypatch.setattr(starttls_probe.smtplib, "SMTP", DummySMTP)

    res = starttls_probe.discover("h")
    assert res["TLSv1"] is False
    assert res["TLSv1_1"] is False
    assert res["TLSv1_2"] is True
    assert res["TLSv1_3"] is False


def test_starttls_details_and_ciphers(monkeypatch):
    class DummySock:
        def version(self):
            return "TLSv1.2"

        def cipher(self):
            return ("ECDHE-RSA-AES128-GCM-SHA256", "TLSv1.2", 128)

        def getpeercert(self):
            return {
                "subject": ((("commonName", "example.com"),),),
                "issuer": ((("commonName", "CA"),),),
                "notAfter": "a",
                "subjectAltName": (("DNS", "example.com"),),
            }

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.sock = DummySock()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

        def starttls(self, context=None):
            # Accept only TLSv1.2 and a specific cipher
            if context.maximum_version == ssl.TLSVersion.TLSv1_2 and getattr(
                context, "_cipher_str", None
            ) in (None, "ECDHE-RSA-AES128-GCM-SHA256"):
                return (220, b"go")
            raise ssl.SSLError("unsupported")

    def fake_set_ciphers(self, cipher_str):
        # Store for DummySMTP to inspect during tests
        setattr(self, "_cipher_str", cipher_str)

    monkeypatch.setattr(starttls_probe.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(starttls_probe.ssl.SSLContext, "set_ciphers", fake_set_ciphers)

    det = starttls_probe.details("example.com")
    assert det["TLSv1_2"]["supported"] is True
    assert det["TLSv1_2"]["protocol"] == "TLSv1.2"
    assert det["TLSv1_2"]["cipher"] == "ECDHE-RSA-AES128-GCM-SHA256"
    assert isinstance(det["TLSv1_2"]["certificate"], dict)
    assert det["TLSv1_2"]["valid"] is True

    mat = starttls_probe.cipher_matrix(
        "h", ciphers=["ECDHE-RSA-AES128-GCM-SHA256", "TLS_AES_128_GCM_SHA256"]
    )
    assert mat["TLSv1_2"]["ECDHE-RSA-AES128-GCM-SHA256"] is True
    assert mat["TLSv1_2"]["TLS_AES_128_GCM_SHA256"] is False
