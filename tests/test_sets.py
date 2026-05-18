from yapar.grammar import EOF, EPSILON, Grammar, grammar_from_dict
from yapar.sets import first, first_of_sequence, follow


def _arithmetic_grammar() -> Grammar:
    raw = {
        "tokens": ["ID", "PLUS", "TIMES", "LPAREN", "RPAREN"],
        "rules": {
            "E": [["E", "PLUS", "T"], ["T"]],
            "T": [["T", "TIMES", "F"], ["F"]],
            "F": [["LPAREN", "E", "RPAREN"], ["ID"]],
        },
    }
    return grammar_from_dict(raw)


def _epsilon_grammar() -> Grammar:
    raw = {
        "tokens": ["A", "B", "C"],
        "rules": {
            "S": [["A", "B"], ["A", "opt"]],
            "opt": [["C"], []],
        },
    }
    return grammar_from_dict(raw)


def _sym(g: Grammar, name: str):
    for s in g.terminals | g.nonterminals:
        if s.name == name:
            return s
    raise KeyError(name)


def test_first_terminal_contains_itself():
    g = _arithmetic_grammar()
    f = first(g)
    id_sym = _sym(g, "ID")
    assert id_sym in f[id_sym]


def test_first_of_E_contains_id_and_lparen():
    g = _arithmetic_grammar()
    f = first(g)
    e = _sym(g, "E")
    assert _sym(g, "ID") in f[e]
    assert _sym(g, "LPAREN") in f[e]


def test_first_of_E_does_not_contain_epsilon():
    g = _arithmetic_grammar()
    f = first(g)
    e = _sym(g, "E")
    assert EPSILON not in f[e]


def test_epsilon_production_adds_epsilon_to_first():
    g = _epsilon_grammar()
    f = first(g)
    opt = _sym(g, "opt")
    assert EPSILON in f[opt]


def test_epsilon_propagates_through_nullable_symbol():
    raw = {
        "tokens": ["A"],
        "rules": {
            "S": [["B", "A"], ["A"]],
            "B": [[]],
        },
    }
    g = grammar_from_dict(raw)
    f = first(g)
    s = _sym(g, "S")
    assert _sym(g, "A") in f[s]


def test_follow_start_contains_eof():
    g = _arithmetic_grammar().augment()
    f_sets = first(g)
    fl = follow(g, f_sets)
    e = _sym(g, "E")
    assert EOF in fl[e]


def test_follow_E_contains_rparen():
    g = _arithmetic_grammar().augment()
    f_sets = first(g)
    fl = follow(g, f_sets)
    e = _sym(g, "E")
    assert _sym(g, "RPAREN") in fl[e]


def test_follow_T_contains_plus_and_eof():
    g = _arithmetic_grammar().augment()
    f_sets = first(g)
    fl = follow(g, f_sets)
    t = _sym(g, "T")
    assert _sym(g, "PLUS") in fl[t]
    assert EOF in fl[t]


def test_first_of_empty_sequence_is_epsilon():
    g = _arithmetic_grammar()
    f_sets = first(g)
    assert EPSILON in first_of_sequence((), f_sets)


def test_first_of_sequence_terminal_first():
    g = _arithmetic_grammar()
    f_sets = first(g)
    id_sym = _sym(g, "ID")
    result = first_of_sequence((id_sym,), f_sets)
    assert id_sym in result
    assert EPSILON not in result


def test_first_of_sequence_stops_at_non_nullable():
    g = _arithmetic_grammar()
    f_sets = first(g)
    id_sym = _sym(g, "ID")
    plus_sym = _sym(g, "PLUS")
    result = first_of_sequence((id_sym, plus_sym), f_sets)
    assert id_sym in result
    assert plus_sym not in result
