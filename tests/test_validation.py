import pytest

from yapar.errors import YAParSyntaxError
from yapar.validation import check_grammar, validate_grammar


def test_empty_rules_returns_error():
    raw = {"tokens": ["ID"], "rules": {}}
    errors = validate_grammar(raw)
    assert len(errors) >= 1
    assert any("no rules" in e.lower() for e in errors)


def test_undefined_symbol_in_body_detected():
    raw = {
        "tokens": ["ID"],
        "rules": {"S": [["ID", "GHOST"]]},
    }
    errors = validate_grammar(raw)
    assert any("GHOST" in e for e in errors)


def test_undefined_nonterminal_in_body_detected():
    raw = {
        "tokens": ["ID"],
        "rules": {"S": [["ID", "Missing"]]},
    }
    errors = validate_grammar(raw)
    assert any("Missing" in e for e in errors)


def test_unreachable_nonterminal_detected():
    raw = {
        "tokens": ["ID"],
        "rules": {
            "S": [["ID"]],
            "Orphan": [["ID"]],
        },
    }
    errors = validate_grammar(raw)
    assert any("Orphan" in e for e in errors)


def test_reachable_nonterminal_not_flagged():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    errors = validate_grammar(raw)
    assert errors == []


def test_epsilon_production_is_valid():
    raw = {
        "tokens": ["A"],
        "rules": {"S": [["A"], []]},
    }
    assert validate_grammar(raw) == []


def test_multiple_errors_all_reported():
    raw = {
        "tokens": [],
        "rules": {
            "S": [["UNDEF_A"]],
            "Dead": [["UNDEF_B"]],
        },
    }
    errors = validate_grammar(raw)
    assert len(errors) >= 2


def test_check_grammar_raises_on_invalid():
    raw = {"tokens": ["ID"], "rules": {"S": [["NOPE"]]}}
    with pytest.raises(YAParSyntaxError):
        check_grammar(raw)


def test_check_grammar_passes_on_valid():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {"E": [["E", "PLUS", "ID"], ["ID"]]},
    }
    check_grammar(raw)


def test_indirect_reachability():
    raw = {
        "tokens": ["ID"],
        "rules": {
            "S": [["A"]],
            "A": [["B"]],
            "B": [["ID"]],
        },
    }
    assert validate_grammar(raw) == []


def test_validate_from_file(simple_yalp):
    from yapar.reader import read_yalp

    raw = read_yalp(str(simple_yalp))
    assert validate_grammar(raw) == []
