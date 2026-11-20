"""Read legacy .strings files."""

from __future__ import annotations

import re
from typing import Dict

ENTRY_RE = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;')
COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'"}


def decode(data: bytes) -> str:
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-16", errors="replace")


def unescape(value: str) -> str:
    result = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            following = value[index + 1]
            if following in ESCAPES:
                result.append(ESCAPES[following])
                index += 2
                continue
            if following == "u" and index + 5 < len(value):
                try:
                    result.append(chr(int(value[index + 2 : index + 6], 16)))
                    index += 6
                    continue
                except ValueError:
                    pass
            result.append(following)
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def parse_strings(text: str) -> Dict[str, str]:
    cleaned = COMMENT_RE.sub("", text)
    entries: Dict[str, str] = {}
    for match in ENTRY_RE.finditer(cleaned):
        key = unescape(match.group(1))
        value = unescape(match.group(2))
        if key:
            entries[key] = value
    return entries


def load_strings(path: str) -> Dict[str, str]:
    from pathlib import Path

    return parse_strings(decode(Path(path).read_bytes()))
