import random
import secrets
import string
from enum import Enum
from typing import List, Optional, TextIO, Union


class DataMode(Enum):
    """Available data generation modes."""

    ASCII = "ascii"
    BINARY = "binary"
    UTF8 = "utf8"
    DICT = "dict"
    REPEAT = "repeat"


def gen_ascii(size: int, secure: bool = False) -> str:
    """Return ``size`` random ASCII characters."""
    rng = secrets.SystemRandom() if secure else random
    chars = string.ascii_letters + string.digits
    return "".join(rng.choice(chars) for _ in range(size))


def gen_utf8(size: int, secure: bool = False) -> str:
    """Return ``size`` random UTF-8 characters."""
    rng = secrets.SystemRandom() if secure else random
    charset = string.ascii_letters + string.digits + "äöüßéñΩ≈ç√∫µ≤≥÷"
    return "".join(rng.choice(charset) for _ in range(size))


def gen_binary(
    size: int, secure: bool = False, stream: Optional[TextIO] = None
) -> bytes:
    """Return ``size`` random bytes, optionally reading from ``stream``."""
    if stream is not None:
        data = stream.read(size)
        if isinstance(data, str):
            data = data.encode()
        if len(data) < size:
            data += gen_binary(size - len(data), secure)
        return data
    if secure:
        return secrets.token_bytes(size)
    return bytes(random.getrandbits(8) for _ in range(size))


def gen_dictionary(size: int, words: List[str]) -> str:
    """Return text of approximately ``size`` bytes from ``words`` list."""
    if not words:
        return ""
    result: List[str] = []
    total = 0
    while total < size:
        word = random.choice(words)
        result.append(word)
        total += len(word) + 1
    return " ".join(result)[:size]


def gen_repeat(text: str, size: int) -> str:
    """Repeat ``text`` until ``size`` bytes are produced."""
    if not text:
        return ""
    reps = (size // len(text)) + 1
    return (text * reps)[:size]


def load_wordlist(path: str) -> List[str]:
    """Return non-empty, stripped lines from ``path``."""
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def compile_wordlist(path: str) -> List[str]:
    """Return list of words from ``path``."""
    return load_wordlist(path)


def generate(
    size: int,
    mode: Union[DataMode, str] = DataMode.ASCII,
    *,
    secure: bool = False,
    words: Optional[List[str]] = None,
    repeat: Optional[str] = None,
    stream: Optional[TextIO] = None,
) -> bytes:
    """Generate ``size`` bytes of data using ``mode``."""
    if size < 0:
        raise ValueError("size must be non-negative")
    if isinstance(mode, str):
        try:
            mode = DataMode(mode.lower())
        except ValueError:
            mode = DataMode.ASCII

    if mode is DataMode.BINARY:
        return gen_binary(size, secure=secure, stream=stream)
    if mode is DataMode.UTF8:
        return gen_utf8(size, secure=secure).encode("utf-8")
    if mode is DataMode.DICT:
        return gen_dictionary(size, words or []).encode("utf-8")
    if mode is DataMode.REPEAT:
        return gen_repeat(repeat or "", size).encode("utf-8")

    # default ascii
    return gen_ascii(size, secure=secure).encode("ascii")
