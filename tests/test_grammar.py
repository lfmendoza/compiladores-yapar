import pytest

from yapar.grammar import EOF, Grammar, Production, Symbol, grammar_from_dict


def _make_simple_grammar() -> Grammar:
    raw = {
        "tokens": ["ID", "PLUS"],
        "ignored": [],
        "rules": {
            "expr": [["expr", "PLUS", "term"], ["term"]],
            "term": [["ID"]],
        },
    }
    return grammar_from_dict(raw)


def test_symbol_value_equality():
    assert Symbol("A", True) == Symbol("A", True)
    assert Symbol("A", True) != Symbol("A", False)


def test_symbol_hashable_and_usable_in_set():
    s = Symbol("A", True)
    assert s in {s}
    assert s in frozenset({s})


def test_symbol_immutable():
    s = Symbol("A", True)
    with pytest.raises(Exception):
        s.name = "B"  # type: ignore[misc]


def test_production_str_non_empty_body():
    head = Symbol("E", False)
    body = (Symbol("E", False), Symbol("+", True), Symbol("T", False))
    p = Production(1, head, body)
    assert "E" in str(p)
    assert "→" in str(p)
    assert "+" in str(p)


def test_production_str_empty_body():
    head = Symbol("A", False)
    p = Production(1, head, ())
    assert "ε" in str(p)


def test_grammar_from_dict_terminals():
    g = _make_simple_grammar()
    names = {s.name for s in g.terminals}
    assert "ID" in names
    assert "PLUS" in names


def test_grammar_from_dict_nonterminals():
    g = _make_simple_grammar()
    names = {s.name for s in g.nonterminals}
    assert "expr" in names
    assert "term" in names


def test_grammar_from_dict_start_is_first_rule():
    g = _make_simple_grammar()
    assert g.start.name == "expr"


def test_grammar_from_dict_production_count():
    g = _make_simple_grammar()
    assert len(g.productions) == 3


def test_augment_inserts_new_start():
    g = _make_simple_grammar()
    aug = g.augment()
    assert aug.start.name == "expr'"
    assert aug.start not in g.nonterminals


def test_augment_production_zero_structure():
    g = _make_simple_grammar()
    aug = g.augment()
    p0 = aug.production_by_id(0)
    assert p0.head == aug.start
    assert p0.body == (g.start,)


def test_augment_production_ids_are_sequential():
    g = _make_simple_grammar()
    aug = g.augment()
    ids = [p.id for p in aug.productions]
    assert ids == sorted(ids)
    assert ids[0] == 0
    assert ids[-1] == len(ids) - 1


def test_augment_adds_eof_to_terminals():
    g = _make_simple_grammar()
    aug = g.augment()
    assert EOF in aug.terminals


def test_augment_original_grammar_unchanged():
    g = _make_simple_grammar()
    original_prod_count = len(g.productions)
    _ = g.augment()
    assert len(g.productions) == original_prod_count


def test_production_by_id_existing():
    g = _make_simple_grammar()
    p = g.production_by_id(1)
    assert p.id == 1


def test_production_by_id_missing_raises():
    g = _make_simple_grammar()
    with pytest.raises(KeyError):
        g.production_by_id(9999)


def test_epsilon_production_in_body():
    raw = {
        "tokens": ["A"],
        "rules": {"S": [["A"], []]},
    }
    g = grammar_from_dict(raw)
    empty_prods = [p for p in g.productions if not p.body]
    assert len(empty_prods) == 1
