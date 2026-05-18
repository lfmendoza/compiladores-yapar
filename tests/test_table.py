import pytest

from yapar.automaton import build_automaton
from yapar.errors import ConflictError
from yapar.grammar import Grammar, grammar_from_dict
from yapar.sets import first, follow
from yapar.table import Accept, Reduce, Shift, SLRTable, build_slr_table


def _build(raw: dict) -> tuple[SLRTable, Grammar]:
    g = grammar_from_dict(raw).augment()
    a = build_automaton(g)
    f = first(g)
    fl = follow(g, f)
    return build_slr_table(a, g, fl), g


def test_table_has_accept_action():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table, _ = _build(raw)
    has_accept = any(isinstance(v, Accept) for v in table.action.values())
    assert has_accept


def test_table_has_shift_actions():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table, _ = _build(raw)
    shifts = [v for v in table.action.values() if isinstance(v, Shift)]
    assert len(shifts) > 0


def test_table_has_reduce_actions():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table, _ = _build(raw)
    reduces = [v for v in table.action.values() if isinstance(v, Reduce)]
    assert len(reduces) > 0


def test_table_has_goto_entries():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    table, _ = _build(raw)
    assert len(table.goto_table) > 0


def test_get_action_returns_none_for_unknown_pair():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table, _ = _build(raw)
    assert table.get_action(999, "ID") is None


def test_get_goto_returns_none_for_unknown_pair():
    raw = {"tokens": ["ID"], "rules": {"S": [["ID"]]}}
    table, _ = _build(raw)
    assert table.get_goto(999, "S") is None


def test_shift_reduce_conflict_raises():
    raw = {
        "tokens": ["IF", "THEN", "ELSE", "STMT"],
        "rules": {
            "stmt": [
                ["IF", "STMT", "THEN", "stmt", "ELSE", "stmt"],
                ["IF", "STMT", "THEN", "stmt"],
                ["STMT"],
            ]
        },
    }
    with pytest.raises(ConflictError) as exc_info:
        _build(raw)
    assert "ELSE" in str(exc_info.value)


def test_conflict_error_carries_state_info():
    raw = {
        "tokens": ["IF", "THEN", "ELSE", "STMT"],
        "rules": {
            "stmt": [
                ["IF", "STMT", "THEN", "stmt", "ELSE", "stmt"],
                ["IF", "STMT", "THEN", "stmt"],
                ["STMT"],
            ]
        },
    }
    with pytest.raises(ConflictError) as exc_info:
        _build(raw)
    err = exc_info.value
    assert isinstance(err.state, int)
    assert err.symbol == "ELSE"


def test_arithmetic_grammar_builds_without_conflict():
    raw = {
        "tokens": ["ID", "PLUS", "TIMES", "LPAREN", "RPAREN"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["T", "TIMES", "F"], ["F"]],
            "F": [["LPAREN", "E", "RPAREN"], ["ID"]],
        },
    }
    table, _ = _build(raw)
    assert table is not None


def test_action_str_representations():
    assert str(Shift(3)) == "s3"
    assert str(Reduce(2)) == "r2"
    assert str(Accept()) == "acc"
