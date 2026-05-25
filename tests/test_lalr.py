import pytest

from yapar.automaton import Item, build_automaton
from yapar.errors import ConflictError
from yapar.grammar import EOF, Grammar, Symbol, grammar_from_dict
from yapar.lalr import (
    LR1Automaton,
    LR1Item,
    build_lalr_table,
    build_lr1_automaton,
    closure_lr1,
    core,
    goto_lr1,
    merge_to_lalr,
)
from yapar.sets import first
from yapar.table import Accept, Reduce, Shift


def _simple_grammar() -> Grammar:
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    return grammar_from_dict(raw).augment()


def _arithmetic_grammar() -> Grammar:
    raw = {
        "tokens": ["ID", "NUM", "PLUS", "MINUS", "TIMES", "DIV", "LPAREN", "RPAREN"],
        "rules": {
            "expr": [["expr", "PLUS", "term"], ["expr", "MINUS", "term"], ["term"]],
            "term": [["term", "TIMES", "factor"], ["term", "DIV", "factor"], ["factor"]],
            "factor": [["LPAREN", "expr", "RPAREN"], ["NUM"], ["ID"]],
        },
    }
    return grammar_from_dict(raw).augment()


def _sym(g: Grammar, name: str) -> Symbol:
    for s in g.terminals | g.nonterminals:
        if s.name == name:
            return s
    raise KeyError(name)


def test_lr1_item_fields():
    item = LR1Item(1, 2, EOF)
    assert item.production_id == 1
    assert item.dot == 2
    assert item.lookahead == EOF


def test_lr1_item_is_namedtuple():
    item = LR1Item(0, 0, EOF)
    assert item[0] == 0
    assert item[2] == EOF


def test_lr1_item_immutable():
    item = LR1Item(0, 0, EOF)
    with pytest.raises(AttributeError):
        item.lookahead = Symbol("X", True)  # type: ignore[misc]


def test_lr1_item_equality_includes_lookahead():
    la1 = Symbol("$", True)
    la2 = Symbol("+", True)
    assert LR1Item(0, 0, la1) != LR1Item(0, 0, la2)
    assert LR1Item(0, 0, la1) == LR1Item(0, 0, la1)


def test_core_strips_lookahead():
    la = Symbol("$", True)
    items = frozenset({LR1Item(0, 0, la), LR1Item(1, 1, la)})
    result = core(items)
    assert result == frozenset({Item(0, 0), Item(1, 1)})


def test_core_merges_duplicate_bases():
    la1 = Symbol("$", True)
    la2 = Symbol("+", True)
    items = frozenset({LR1Item(0, 0, la1), LR1Item(0, 0, la2)})
    result = core(items)
    assert result == frozenset({Item(0, 0)})


def test_closure_lr1_expands_nonterminals():
    g = _simple_grammar()
    f_sets = first(g)
    start_prod = g.productions[0]
    initial = frozenset({LR1Item(start_prod.id, 0, EOF)})
    result = closure_lr1(initial, g, f_sets)
    assert len(result) > 1


def test_closure_lr1_covers_all_productions():
    g = _simple_grammar()
    f_sets = first(g)
    start_prod = g.productions[0]
    initial = frozenset({LR1Item(start_prod.id, 0, EOF)})
    result = closure_lr1(initial, g, f_sets)
    prod_ids_in_state = {it.production_id for it in result}
    all_prod_ids = {p.id for p in g.productions}
    assert prod_ids_in_state == all_prod_ids


def test_closure_lr1_idempotent():
    g = _simple_grammar()
    f_sets = first(g)
    start_prod = g.productions[0]
    initial = frozenset({LR1Item(start_prod.id, 0, EOF)})
    once = closure_lr1(initial, g, f_sets)
    twice = closure_lr1(once, g, f_sets)
    assert once == twice


def test_goto_lr1_on_terminal_nonempty():
    g = _simple_grammar()
    f_sets = first(g)
    start_prod = g.productions[0]
    state0 = closure_lr1(frozenset({LR1Item(start_prod.id, 0, EOF)}), g, f_sets)
    id_sym = _sym(g, "ID")
    result = goto_lr1(state0, id_sym, g, f_sets)
    assert len(result) > 0


def test_goto_lr1_on_nonterminal_nonempty():
    g = _simple_grammar()
    f_sets = first(g)
    start_prod = g.productions[0]
    state0 = closure_lr1(frozenset({LR1Item(start_prod.id, 0, EOF)}), g, f_sets)
    e_sym = _sym(g, "E")
    result = goto_lr1(state0, e_sym, g, f_sets)
    assert len(result) > 0


def test_build_lr1_automaton_has_states():
    g = _simple_grammar()
    f_sets = first(g)
    a = build_lr1_automaton(g, f_sets)
    assert isinstance(a, LR1Automaton)
    assert len(a.states) > 0


def test_build_lr1_automaton_has_transitions():
    g = _simple_grammar()
    f_sets = first(g)
    a = build_lr1_automaton(g, f_sets)
    assert len(a.transitions) > 0


def test_lr1_has_at_least_as_many_states_as_lr0():
    g = _arithmetic_grammar()
    f_sets = first(g)
    lr0 = build_automaton(g)
    lr1 = build_lr1_automaton(g, f_sets)
    assert len(lr1.states) >= len(lr0.states)


def test_merge_to_lalr_matches_lr0_state_count():
    g = _arithmetic_grammar()
    f_sets = first(g)
    lr0 = build_automaton(g)
    lr1 = build_lr1_automaton(g, f_sets)
    merged_states, _ = merge_to_lalr(lr1)
    assert len(merged_states) == len(lr0.states)


def test_merge_to_lalr_preserves_transitions():
    g = _simple_grammar()
    f_sets = first(g)
    lr1 = build_lr1_automaton(g, f_sets)
    _, merged_transitions = merge_to_lalr(lr1)
    assert len(merged_transitions) > 0


def test_build_lalr_table_arithmetic_no_conflict():
    g = _arithmetic_grammar()
    f_sets = first(g)
    table = build_lalr_table(g, f_sets)
    assert table is not None
    assert any(isinstance(v, Accept) for v in table.action.values())


def test_build_lalr_table_has_shifts_and_reduces():
    g = _simple_grammar()
    f_sets = first(g)
    table = build_lalr_table(g, f_sets)
    assert any(isinstance(v, Shift) for v in table.action.values())
    assert any(isinstance(v, Reduce) for v in table.action.values())


def test_build_lalr_table_conflict_on_dangling_else():
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
    g = grammar_from_dict(raw).augment()
    f_sets = first(g)
    with pytest.raises(ConflictError):
        build_lalr_table(g, f_sets)
