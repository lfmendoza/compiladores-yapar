import os
import tempfile

from yapar.automaton import Item, build_automaton
from yapar.grammar import grammar_from_dict
from yapar.viz import _build_dot, _format_item, render_automaton


def _simple_grammar():
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    return grammar_from_dict(raw).augment()


def test_format_item_dot_at_start():
    g = _simple_grammar()
    p = g.productions[0]
    item = Item(p.id, 0)
    result = _format_item(item, g)
    assert "·" in result
    assert str(p.head) in result


def test_format_item_dot_in_middle():
    g = _simple_grammar()
    p = next(p for p in g.productions if len(p.body) >= 2)
    item = Item(p.id, 1)
    result = _format_item(item, g)
    assert "·" in result


def test_format_item_epsilon_production():
    raw = {"tokens": ["A"], "rules": {"S": [["A"], []]}}
    g = grammar_from_dict(raw).augment()
    eps_prod = next(p for p in g.productions if not p.body)
    item = Item(eps_prod.id, 0)
    result = _format_item(item, g)
    assert "ε" in result
    assert "·" in result


def test_build_dot_contains_all_states():
    g = _simple_grammar()
    a = build_automaton(g)
    dot = _build_dot(a, g)
    for i in range(len(a.states)):
        assert f"s{i}" in dot


def test_build_dot_contains_digraph_header():
    g = _simple_grammar()
    a = build_automaton(g)
    dot = _build_dot(a, g)
    assert "digraph LR0" in dot
    assert "rankdir=LR" in dot


def test_build_dot_contains_transitions():
    g = _simple_grammar()
    a = build_automaton(g)
    dot = _build_dot(a, g)
    assert "->" in dot


def test_render_automaton_writes_dot_file():
    g = _simple_grammar()
    a = build_automaton(g)
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "automaton.dot")
        result = render_automaton(a, g, out_path)
        assert os.path.exists(result)
        content = open(result, encoding="utf-8").read()
        assert "digraph LR0" in content


def test_render_automaton_dot_extension_stays_as_dot():
    g = _simple_grammar()
    a = build_automaton(g)
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "out.dot")
        result = render_automaton(a, g, out_path)
        assert result.endswith(".dot")


def test_render_automaton_non_dot_path_returns_path():
    g = _simple_grammar()
    a = build_automaton(g)
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "automaton")
        result = render_automaton(a, g, out_path)
        assert isinstance(result, str)
        assert len(result) > 0
