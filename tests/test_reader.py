from pathlib import Path

import pytest

from yapar.errors import YAParSyntaxError
from yapar.reader import parse_yalp, read_yalp


def test_parse_simple_grammar():
    source = """
TOKENS  ID PLUS

%%

expr : expr PLUS term
     | term
     ;
term : ID
     ;
"""
    result = parse_yalp(source)
    assert set(result["tokens"]) == {"ID", "PLUS"}
    assert "expr" in result["rules"]
    assert "term" in result["rules"]
    assert len(result["rules"]["expr"]) == 2
    assert ["expr", "PLUS", "term"] in result["rules"]["expr"]
    assert ["term"] in result["rules"]["expr"]


def test_comment_stripping():
    source = """
(* This is a comment *)
TOKENS  A (* inline comment *) B

%%

S : A B
  ;
"""
    result = parse_yalp(source)
    assert "A" in result["tokens"]
    assert "B" in result["tokens"]


def test_ignore_section():
    source = """
TOKENS  ID

IGNORE  WS NEWLINE

%%

S : ID
  ;
"""
    result = parse_yalp(source)
    assert "WS" in result["ignored"]
    assert "NEWLINE" in result["ignored"]


def test_missing_separator_raises():
    with pytest.raises(YAParSyntaxError, match="%%"):
        parse_yalp("TOKENS A\nS : A ;")


def test_multiple_alternatives_same_line():
    source = """TOKENS  A B C

%%

S : A | B | C ;
"""
    result = parse_yalp(source)
    assert len(result["rules"]["S"]) == 3


def test_epsilon_production():
    source = """
TOKENS  A

%%

S : A
  |
  ;
"""
    result = parse_yalp(source)
    assert [] in result["rules"]["S"]
    assert ["A"] in result["rules"]["S"]


def test_multiline_tokens_section():
    source = """
TOKENS
    ID
    PLUS
    MINUS

%%

E : ID ;
"""
    result = parse_yalp(source)
    assert "ID" in result["tokens"]
    assert "PLUS" in result["tokens"]
    assert "MINUS" in result["tokens"]


def test_read_yalp_file(simple_yalp: Path):
    result = read_yalp(str(simple_yalp))
    assert "ID" in result["tokens"]
    assert "expr" in result["rules"]
    assert "term" in result["rules"]
    assert "factor" in result["rules"]


def test_read_yalp_epsilon_fixture(epsilon_yalp: Path):
    result = read_yalp(str(epsilon_yalp))
    assert "S" in result["rules"]
    assert "opt_C" in result["rules"]
    assert [] in result["rules"]["opt_C"]
