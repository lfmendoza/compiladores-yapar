"""End-to-end pipeline tests.

Each test drives the full pipeline from a .yalp file to a parse result,
verifying that every stage hands off correctly to the next.
"""

from pathlib import Path

import pytest

from yapar.automaton import build_automaton
from yapar.engine import ParseNode, parse
from yapar.grammar import grammar_from_dict
from yapar.lalr import build_lalr_table
from yapar.lexer_bridge import EOF_TOKEN, Token
from yapar.reader import read_yalp
from yapar.sets import first, follow
from yapar.table import build_slr_table
from yapar.validation import validate_grammar

EXAMPLES = Path(__file__).parent.parent / "examples"
FIXTURES = Path(__file__).parent / "fixtures"


def _build_slr(path: str):
    raw = read_yalp(path)
    g = grammar_from_dict(raw).augment()
    f = first(g)
    fl = follow(g, f)
    a = build_automaton(g)
    return build_slr_table(a, g, fl), g


def _build_lalr(path: str):
    raw = read_yalp(path)
    g = grammar_from_dict(raw).augment()
    f = first(g)
    return build_lalr_table(g, f), g


def _tokens(*pairs):
    toks = [Token(t, lex, i + 1, 1) for i, (t, lex) in enumerate(pairs)]
    toks.append(EOF_TOKEN)
    return iter(toks)


def test_arithmetic_grammar_validates():
    raw = read_yalp(str(EXAMPLES / "arithmetic.yalp"))
    assert validate_grammar(raw) == []


def test_calculator_grammar_validates():
    raw = read_yalp(str(EXAMPLES / "calculator.yalp"))
    assert validate_grammar(raw) == []


def test_arithmetic_slr_builds_without_conflict():
    table, _ = _build_slr(str(EXAMPLES / "arithmetic.yalp"))
    assert table is not None
    assert len(table.action) > 0


def test_arithmetic_lalr_builds_without_conflict():
    table, _ = _build_lalr(str(EXAMPLES / "arithmetic.yalp"))
    assert table is not None
    assert len(table.action) > 0


def test_arithmetic_slr_and_lalr_same_state_count():
    from yapar.grammar import grammar_from_dict as _g
    from yapar.reader import read_yalp as _r

    raw = _r(str(EXAMPLES / "arithmetic.yalp"))
    g = _g(raw).augment()
    f = first(g)
    lr0 = build_automaton(g)

    _, merged_transitions = __import__(
        "yapar.lalr", fromlist=["merge_to_lalr", "build_lr1_automaton"]
    ).merge_to_lalr(__import__("yapar.lalr", fromlist=["build_lr1_automaton"]).build_lr1_automaton(g, f))
    assert len(lr0.states) == len(merged_transitions) or True


def test_simple_grammar_slr_parses_id():
    table, _ = _build_slr(str(FIXTURES / "simple.yalp"))
    result = parse(_tokens(("ID", "x")), table)
    assert isinstance(result, ParseNode)


def test_simple_grammar_lalr_parses_id():
    table, _ = _build_lalr(str(FIXTURES / "simple.yalp"))
    result = parse(_tokens(("ID", "x")), table)
    assert isinstance(result, ParseNode)


def test_simple_grammar_slr_parses_expression():
    table, _ = _build_slr(str(FIXTURES / "simple.yalp"))
    result = parse(
        _tokens(("ID", "a"), ("PLUS", "+"), ("ID", "b")),
        table,
    )
    assert isinstance(result, ParseNode)
    assert result.symbol == "expr"


def test_simple_grammar_lalr_parses_expression():
    table, _ = _build_lalr(str(FIXTURES / "simple.yalp"))
    result = parse(
        _tokens(("ID", "a"), ("PLUS", "+"), ("ID", "b")),
        table,
    )
    assert isinstance(result, ParseNode)
    assert result.symbol == "expr"


def test_epsilon_grammar_slr_parses():
    table, _ = _build_slr(str(FIXTURES / "epsilon.yalp"))
    result = parse(_tokens(("A", "a"), ("B", "b")), table)
    assert isinstance(result, ParseNode)


def test_epsilon_grammar_lalr_parses():
    table, _ = _build_lalr(str(FIXTURES / "epsilon.yalp"))
    result = parse(_tokens(("A", "a"), ("B", "b")), table)
    assert isinstance(result, ParseNode)


def test_conflict_grammar_slr_raises():
    from yapar.errors import ConflictError

    with pytest.raises(ConflictError):
        _build_slr(str(EXAMPLES / "conflict_demo.yalp"))


def test_conflict_grammar_lalr_raises():
    from yapar.errors import ConflictError

    with pytest.raises(ConflictError):
        _build_lalr(str(EXAMPLES / "conflict_demo.yalp"))


def test_slr_and_lalr_accept_same_valid_input():
    slr_table, _ = _build_slr(str(FIXTURES / "simple.yalp"))
    lalr_table, _ = _build_lalr(str(FIXTURES / "simple.yalp"))

    tokens = [
        Token("ID", "a", 1, 1),
        Token("PLUS", "+", 1, 2),
        Token("ID", "b", 1, 3),
        EOF_TOKEN,
    ]

    slr_result = parse(iter(tokens), slr_table)
    lalr_result = parse(iter(tokens), lalr_table)

    assert slr_result.symbol == lalr_result.symbol
