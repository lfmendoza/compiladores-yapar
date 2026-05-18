import json
import os
import tempfile

import pytest

from yapar.errors import YAParError
from yapar.lexer_bridge import EOF_TOKEN, Token, load_dfa, tokenize, tokens_from_file

_SIMPLE_DFA = {
    "initial": "0",
    "accept": ["1", "2"],
    "token_types": {"1": "A", "2": "B"},
    "transitions": {
        "0,a": "1",
        "0,b": "2",
    },
}


def test_token_fields():
    t = Token("ID", "foo", 1, 5)
    assert t.tipo == "ID"
    assert t.lexema == "foo"
    assert t.linea == 1
    assert t.columna == 5


def test_token_is_namedtuple():
    t = Token("PLUS", "+", 2, 3)
    assert t[0] == "PLUS"
    assert t[1] == "+"


def test_eof_token_sentinel_fields():
    assert EOF_TOKEN.tipo == "$"
    assert EOF_TOKEN.lexema == "$"
    assert EOF_TOKEN.linea == -1
    assert EOF_TOKEN.columna == -1


def test_token_immutable():
    t = Token("ID", "x", 1, 1)
    with pytest.raises(AttributeError):
        t.tipo = "OTHER"


def test_tokens_from_file_basic():
    content = "ID\tfoo\t1\t1\nPLUS\t+\t1\t4\n$\t$\t-1\t-1\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tsv", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(content)
        path = fh.name

    try:
        tokens = tokens_from_file(path)
        assert tokens[0].tipo == "ID"
        assert tokens[0].lexema == "foo"
        assert tokens[1].tipo == "PLUS"
        assert tokens[-1].tipo == "$"
    finally:
        os.unlink(path)


def test_tokens_from_file_appends_eof_when_missing():
    content = "ID\tfoo\t1\t1\nPLUS\t+\t1\t4\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tsv", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(content)
        path = fh.name

    try:
        tokens = tokens_from_file(path)
        assert tokens[-1].tipo == "$"
    finally:
        os.unlink(path)


def test_tokens_from_file_skips_comments():
    content = "# header comment\nID\tfoo\t1\t1\n$\t$\t-1\t-1\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tsv", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(content)
        path = fh.name

    try:
        tokens = tokens_from_file(path)
        assert tokens[0].tipo == "ID"
        assert len(tokens) == 2
    finally:
        os.unlink(path)


def test_tokens_from_file_empty_produces_only_eof():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tsv", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("")
        path = fh.name

    try:
        tokens = tokens_from_file(path)
        assert len(tokens) == 1
        assert tokens[0].tipo == "$"
    finally:
        os.unlink(path)


def test_tokenize_single_char_tokens():
    toks = list(tokenize("ab", _SIMPLE_DFA))
    assert toks[0].tipo == "A"
    assert toks[0].lexema == "a"
    assert toks[1].tipo == "B"
    assert toks[1].lexema == "b"
    assert toks[-1].tipo == "$"


def test_tokenize_yields_eof_on_empty_source():
    toks = list(tokenize("", _SIMPLE_DFA))
    assert len(toks) == 1
    assert toks[0].tipo == "$"


def test_tokenize_tracks_line_and_column():
    toks = list(tokenize("a", _SIMPLE_DFA))
    assert toks[0].linea == 1
    assert toks[0].columna == 1


def test_tokenize_column_advances():
    toks = list(tokenize("ab", _SIMPLE_DFA))
    assert toks[1].columna == 2


def test_tokenize_unrecognized_char_raises():
    with pytest.raises(YAParError, match="Unrecognized"):
        list(tokenize("x", _SIMPLE_DFA))


def test_load_dfa_json():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as fh:
        json.dump(_SIMPLE_DFA, fh)
        path = fh.name

    try:
        dfa = load_dfa(path)
        assert dfa["initial"] == "0"
        assert "1" in dfa["accept"]
    finally:
        os.unlink(path)
