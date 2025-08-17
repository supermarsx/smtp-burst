import secrets
import pytest
from smtpburst import datagen


def test_generate_secure_binary_uses_token_bytes(monkeypatch):
    monkeypatch.setattr(secrets, "token_bytes", lambda n: b"x" * n)
    assert (
        datagen.generate(4, mode=datagen.DataMode.BINARY, secure=True) == b"x" * 4
    )


def test_generate_secure_ascii_uses_system_random(monkeypatch):
    class DummyRandom:
        def choice(self, seq):
            return seq[0]

    monkeypatch.setattr(secrets, "SystemRandom", lambda: DummyRandom())
    assert (
        datagen.generate(5, mode=datagen.DataMode.ASCII, secure=True) == b"a" * 5
    )


def test_generate_negative_size():
    with pytest.raises(ValueError):
        datagen.generate(-1)


def test_gen_binary_stream_partial(monkeypatch):
    class PartialStream:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def read(self, n):
            return self.chunks.pop(0) if self.chunks else b""

    stream = PartialStream([b"ab", b"c"])
    monkeypatch.setattr(datagen.random, "getrandbits", lambda n: ord("x"))
    assert datagen.gen_binary(5, stream=stream) == b"abcxx"
    # ensure the stream was fully consumed before random data was added
    assert stream.chunks == []


def test_gen_binary_stream_partial_secure(monkeypatch):
    class PartialStream:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def read(self, n):
            return self.chunks.pop(0) if self.chunks else b""

    stream = PartialStream([b"ab"])
    monkeypatch.setattr(secrets, "token_bytes", lambda n: b"x" * n)
    assert datagen.gen_binary(4, secure=True, stream=stream) == b"abxx"
    # ensure the stream was fully consumed before random data was added
    assert stream.chunks == []


def test_generate_binary_stream_partial(monkeypatch):
    class PartialStream:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def read(self, n):
            return self.chunks.pop(0) if self.chunks else b""

    stream = PartialStream([b"ab", b"c"])
    monkeypatch.setattr(datagen.random, "getrandbits", lambda n: ord("x"))
    assert (
        datagen.generate(5, mode=datagen.DataMode.BINARY, stream=stream) == b"abcxx"
    )
    assert stream.chunks == []


def test_generate_binary_stream_partial_secure(monkeypatch):
    class PartialStream:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def read(self, n):
            return self.chunks.pop(0) if self.chunks else b""

    stream = PartialStream([b"ab"])
    monkeypatch.setattr(secrets, "token_bytes", lambda n: b"x" * n)
    assert (
        datagen.generate(4, mode=datagen.DataMode.BINARY, secure=True, stream=stream)
        == b"abxx"
    )
    assert stream.chunks == []
