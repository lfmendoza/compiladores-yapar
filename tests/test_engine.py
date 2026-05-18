import pytest

from yapar.automaton import build_automaton
from yapar.engine import ParseNode, parse
from yapar.errors import ParseError
from yapar.grammar import grammar_from_dict
from yapar.lexer_bridge import EOF_TOKEN, Token
from yapar.sets import first, follow
from yapar.table import build_slr_table


def _build_table(raw: dict):
    g = grammar_from_dict(raw).augment()
    a = build_automaton(g)
    f = first(g)
    fl = follow(g, f)
    return build_slr_table(a, g, fl)


def _tokens(*pairs: tuple[str, str]):
    toks = [Token(t, lex, i + 1, 1) for i, (t, lex) in enumerate(pairs)]
    toks.append(EOF_TOKEN)
    return iter(toks)


def test_parse_single_token():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table = _build_table(raw)
    result = parse(_tokens(("ID", "x")), table)
    assert isinstance(result, ParseNode)
    assert result.symbol == "S"


def test_parse_tree_has_correct_root():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    table = _build_table(raw)
    result = parse(_tokens(("ID", "a"), ("PLUS", "+"), ("ID", "b")), table)
    assert result.symbol == "E"


def test_parse_tree_children_count_for_binary_expression():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    table = _build_table(raw)
    result = parse(_tokens(("ID", "a"), ("PLUS", "+"), ("ID", "b")), table)
    assert len(result.children) == 3


def test_parse_rejects_unexpected_token():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    table = _build_table(raw)
    with pytest.raises(ParseError):
        parse(_tokens(("PLUS", "+")), table)


def test_parse_error_carries_token_info():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table = _build_table(raw)
    with pytest.raises(ParseError) as exc_info:
        parse(_tokens(("UNKNOWN", "?")), table)
    assert exc_info.value.token == "UNKNOWN"


def test_parse_left_associative_chain():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    table = _build_table(raw)
    result = parse(
        _tokens(("ID", "a"), ("PLUS", "+"), ("ID", "b"), ("PLUS", "+"), ("ID", "c")),
        table,
    )
    assert isinstance(result, ParseNode)
    assert result.symbol == "E"


def test_parse_node_leaf_repr():
    node = ParseNode(symbol="ID", lexeme="x")
    assert "ID" in repr(node)
    assert "x" in repr(node)


def test_parse_node_inner_repr():
    child = ParseNode(symbol="T", lexeme="")
    parent = ParseNode(symbol="E", children=[child])
    assert "E" in repr(parent)
    assert "T" in repr(parent)


def test_parse_epsilon_grammar():
    raw = {
        "tokens": ["A"],
        "rules": {
            "S": [["A"], []],
        },
    }
    table = _build_table(raw)
    result = parse(_tokens(("A", "a")), table)
    assert isinstance(result, ParseNode)
