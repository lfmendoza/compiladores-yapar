from __future__ import annotations

import json
import pickle
from collections import namedtuple
from collections.abc import Iterator
from typing import Any

from .errors import YAParError

Token = namedtuple("Token", ["tipo", "lexema", "linea", "columna"])

EOF_TOKEN: Token = Token("$", "$", -1, -1)


def load_dfa(path: str) -> Any:
    with open(path, "rb") as fh:
        first_byte = fh.read(1)

    if first_byte == b"{":
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    with open(path, "rb") as fh:
        return pickle.load(fh)


def tokenize(source: str, dfa: Any) -> Iterator[Token]:
    transitions: dict[str, str] = dfa["transitions"]
    accept_map: dict[str, str] = dfa.get("token_types", {})
    accept_states: set[str] = set(str(s) for s in dfa["accept"])
    initial: str = str(dfa["initial"])

    line, col = 1, 1
    i = 0

    while i < len(source):
        state = initial
        last_accept_state: str | None = None
        last_accept_end = i
        j = i

        while j < len(source):
            key = f"{state},{source[j]}"
            if key not in transitions:
                break
            state = transitions[key]
            j += 1
            if state in accept_states:
                last_accept_state = state
                last_accept_end = j

        if last_accept_state is None:
            raise YAParError(
                f"Unrecognized character '{source[i]}' at line {line}, col {col}"
            )

        lexeme = source[i:last_accept_end]
        token_type = accept_map.get(last_accept_state, last_accept_state)
        yield Token(token_type, lexeme, line, col)

        newlines = lexeme.count("\n")
        if newlines:
            line += newlines
            col = len(lexeme) - lexeme.rfind("\n")
        else:
            col += len(lexeme)
        i = last_accept_end

    yield EOF_TOKEN


def tokens_from_file(path: str) -> list[Token]:
    tokens: list[Token] = []
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                tokens.append(Token(parts[0], parts[1], int(parts[2]), int(parts[3])))

    if not tokens or tokens[-1].tipo != "$":
        tokens.append(EOF_TOKEN)

    return tokens
