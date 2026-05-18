from __future__ import annotations

import re

from .errors import YAParSyntaxError

_COMMENT_RE = re.compile(r"\(\*.*?\*\)", re.DOTALL)
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")


def read_yalp(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    return parse_yalp(source)


def parse_yalp(source: str) -> dict:
    text = _COMMENT_RE.sub("", source)

    sep = text.find("%%")
    if sep < 0:
        line = text.count("\n") + 1
        raise YAParSyntaxError("Missing '%%' section separator", line=line)

    tokens, ignored = _parse_declarations(text[:sep])
    rules = _parse_rules(text[sep + 2 :])

    return {"tokens": tokens, "ignored": ignored, "rules": rules}


def _parse_declarations(text: str) -> tuple[list[str], list[str]]:
    tokens: list[str] = []
    ignored: list[str] = []
    current: list[str] | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        kw = parts[0].upper()
        if kw == "TOKENS":
            current = tokens
            current.extend(parts[1:])
        elif kw == "IGNORE":
            current = ignored
            current.extend(parts[1:])
        elif current is not None:
            current.extend(parts)

    return tokens, ignored


def _parse_rules(text: str) -> dict[str, list[list[str]]]:
    rules: dict[str, list[list[str]]] = {}

    for block in text.split(";"):
        block = block.strip()
        if not block:
            continue

        colon = block.find(":")
        if colon < 0:
            continue

        head = block[:colon].strip()
        if not _IDENT_RE.match(head):
            continue

        alts: list[list[str]] = []
        for alt_text in block[colon + 1 :].split("|"):
            alts.append(alt_text.split())

        if head in rules:
            rules[head].extend(alts)
        else:
            rules[head] = alts

    return rules
