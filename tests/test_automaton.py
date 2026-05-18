from yapar.automaton import build_automaton, closure, goto
from yapar.grammar import Grammar, grammar_from_dict


def _make_grammar() -> Grammar:
    raw = {
        "tokens": ["ID", "PLUS"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["ID"]],
        },
    }
    return grammar_from_dict(raw).augment()


def _sym(g: Grammar, name: str):
    for s in g.terminals | g.nonterminals:
        if s.name == name:
            return s
    raise KeyError(name)


def test_automaton_has_states():
    g = _make_grammar()
    a = build_automaton(g)
    assert len(a.states) > 0


def test_initial_state_contains_augmented_production():
    g = _make_grammar()
    a = build_automaton(g)
    state0 = a.states[0]
    start_prod = g.productions[0]
    assert any(item.production_id == start_prod.id and item.dot == 0 for item in state0)


def test_closure_is_idempotent():
    g = _make_grammar()
    a = build_automaton(g)
    state0 = a.states[0]
    assert closure(state0, g) == state0


def test_goto_on_terminal_produces_non_empty_state():
    g = _make_grammar()
    a = build_automaton(g)
    state0 = a.states[0]
    id_sym = _sym(g, "ID")
    result = goto(state0, id_sym, g)
    assert len(result) > 0


def test_goto_on_nonterminal_produces_non_empty_state():
    g = _make_grammar()
    a = build_automaton(g)
    state0 = a.states[0]
    e_sym = _sym(g, "E")
    result = goto(state0, e_sym, g)
    assert len(result) > 0


def test_states_are_deduplicated():
    g = _make_grammar()
    a = build_automaton(g)
    for i, si in enumerate(a.states):
        for j, sj in enumerate(a.states):
            if i != j:
                assert si != sj


def test_index_maps_each_state_to_its_position():
    g = _make_grammar()
    a = build_automaton(g)
    for state_id, state in enumerate(a.states):
        assert a.state_id(state) == state_id


def test_all_transition_endpoints_are_valid_state_ids():
    g = _make_grammar()
    a = build_automaton(g)
    for (src_id, _sym), dst_id in a.transitions.items():
        assert 0 <= src_id < len(a.states)
        assert 0 <= dst_id < len(a.states)


def test_epsilon_grammar_terminates():
    raw = {
        "tokens": ["A"],
        "rules": {"S": [["A"], []]},
    }
    g = grammar_from_dict(raw).augment()
    a = build_automaton(g)
    assert len(a.states) > 0


def test_state_id_returns_none_for_unknown():
    g = _make_grammar()
    a = build_automaton(g)
    assert a.state_id(frozenset()) is None


def test_arithmetic_grammar_has_expected_state_count():
    g = _make_grammar()
    a = build_automaton(g)
    assert len(a.states) >= 6
