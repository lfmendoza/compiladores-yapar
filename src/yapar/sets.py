from __future__ import annotations

from .grammar import EOF, EPSILON, Grammar, Symbol


def first(grammar: Grammar) -> dict[Symbol, frozenset[Symbol]]:
    sets: dict[Symbol, set[Symbol]] = {}

    for t in grammar.terminals:
        sets[t] = {t}
    for nt in grammar.nonterminals:
        sets[nt] = set()

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            head = prod.head
            snapshot = frozenset(sets[head])

            if not prod.body:
                sets[head].add(EPSILON)
            else:
                all_nullable = True
                for sym in prod.body:
                    sym_first = sets.get(sym, frozenset({sym}))
                    sets[head].update(sym_first - {EPSILON})
                    if EPSILON not in sym_first:
                        all_nullable = False
                        break
                if all_nullable:
                    sets[head].add(EPSILON)

            if frozenset(sets[head]) != snapshot:
                changed = True

    return {s: frozenset(v) for s, v in sets.items()}


def first_of_sequence(
    seq: tuple[Symbol, ...],
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> frozenset[Symbol]:
    result: set[Symbol] = set()
    for sym in seq:
        sym_first = first_sets.get(sym, frozenset({sym}))
        result.update(sym_first - {EPSILON})
        if EPSILON not in sym_first:
            return frozenset(result)
    result.add(EPSILON)
    return frozenset(result)


def follow(
    grammar: Grammar,
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> dict[Symbol, frozenset[Symbol]]:
    sets: dict[Symbol, set[Symbol]] = {nt: set() for nt in grammar.nonterminals}
    sets[grammar.start].add(EOF)

    changed = True
    while changed:
        changed = False
        for prod in grammar.productions:
            for i, sym in enumerate(prod.body):
                if sym.is_terminal or sym not in sets:
                    continue

                beta = prod.body[i + 1 :]
                first_beta = first_of_sequence(beta, first_sets)
                snapshot = frozenset(sets[sym])

                sets[sym].update(first_beta - {EPSILON})
                if EPSILON in first_beta:
                    sets[sym].update(sets.get(prod.head, set()))

                if frozenset(sets[sym]) != snapshot:
                    changed = True

    return {s: frozenset(v) for s, v in sets.items()}
