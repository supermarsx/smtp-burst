import secrets
from smtpburst import datagen


def test_generate_secure_binary_uses_token_bytes(monkeypatch):
    monkeypatch.setattr(secrets, "token_bytes", lambda n: b"x" * n)
    assert datagen.generate(4, mode="binary", secure=True) == b"x" * 4


def test_generate_secure_ascii_uses_system_random(monkeypatch):
    class DummyRandom:
        def choice(self, seq):
            return seq[0]

    monkeypatch.setattr(secrets, "SystemRandom", lambda: DummyRandom())
    assert datagen.generate(5, mode="ascii", secure=True) == b"a" * 5
