from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

from .automaton import Item
from .errors import ConflictError
from .grammar import EOF, EPSILON, Grammar, Symbol
from .sets import first_of_sequence
from .table import Accept, Reduce, Shift, SLRTable


class LR1Item(NamedTuple):
    production_id: int
    dot: int
    lookahead: Symbol

    def __str__(self) -> str:
        return f"({self.production_id}, {self.dot}, {self.lookahead})"


@dataclass
class LR1Automaton:
    states: list[frozenset[LR1Item]]
    transitions: dict[tuple[int, Symbol], int]
    _index: dict[frozenset[LR1Item], int] = field(default_factory=dict, repr=False)

    def state_id(self, items: frozenset[LR1Item]) -> int | None:
        return self._index.get(items)


def core(state: frozenset[LR1Item]) -> frozenset[Item]:
    return frozenset(Item(it.production_id, it.dot) for it in state)


def closure_lr1(
    items: frozenset[LR1Item],
    grammar: Grammar,
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> frozenset[LR1Item]:
    result: set[LR1Item] = set(items)
    queue = list(items)

    while queue:
        lr1_item = queue.pop()
        prod = grammar.production_by_id(lr1_item.production_id)

        if lr1_item.dot >= len(prod.body):
            continue

        sym = prod.body[lr1_item.dot]
        if sym.is_terminal:
            continue

        beta = prod.body[lr1_item.dot + 1 :]
        first_beta = first_of_sequence(beta + (lr1_item.lookahead,), first_sets)

        for p in grammar.productions:
            if p.head != sym:
                continue
            for la in first_beta:
                if la == EPSILON:
                    continue
                new_item = LR1Item(p.id, 0, la)
                if new_item not in result:
                    result.add(new_item)
                    queue.append(new_item)

    return frozenset(result)


def goto_lr1(
    items: frozenset[LR1Item],
    symbol: Symbol,
    grammar: Grammar,
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> frozenset[LR1Item]:
    kernel: set[LR1Item] = set()
    for item in items:
        prod = grammar.production_by_id(item.production_id)
        if item.dot < len(prod.body) and prod.body[item.dot] == symbol:
            kernel.add(LR1Item(item.production_id, item.dot + 1, item.lookahead))
    return closure_lr1(frozenset(kernel), grammar, first_sets)


def build_lr1_automaton(
    grammar: Grammar,
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> LR1Automaton:
    start_prod = grammar.productions[0]
    initial_kernel = frozenset({LR1Item(start_prod.id, 0, EOF)})
    initial = closure_lr1(initial_kernel, grammar, first_sets)

    states: list[frozenset[LR1Item]] = [initial]
    index: dict[frozenset[LR1Item], int] = {initial: 0}
    transitions: dict[tuple[int, Symbol], int] = {}
    queue: list[frozenset[LR1Item]] = [initial]

    while queue:
        current = queue.pop(0)
        current_id = index[current]

        symbols_at_dot: set[Symbol] = set()
        for item in current:
            prod = grammar.production_by_id(item.production_id)
            if item.dot < len(prod.body):
                sym = prod.body[item.dot]
                if sym != EPSILON:
                    symbols_at_dot.add(sym)

        for sym in sorted(symbols_at_dot, key=lambda s: s.name):
            next_state = goto_lr1(current, sym, grammar, first_sets)
            if not next_state:
                continue

            if next_state not in index:
                index[next_state] = len(states)
                states.append(next_state)
                queue.append(next_state)

            transitions[(current_id, sym)] = index[next_state]

    return LR1Automaton(states=states, transitions=transitions, _index=index)


def merge_to_lalr(
    lr1: LR1Automaton,
) -> tuple[list[frozenset[LR1Item]], dict[tuple[int, Symbol], int]]:
    core_to_merged: dict[frozenset[Item], int] = {}
    merged_states: list[frozenset[LR1Item]] = []
    old_to_new: dict[int, int] = {}

    for old_id, state in enumerate(lr1.states):
        c = core(state)
        if c not in core_to_merged:
            new_id = len(merged_states)
            core_to_merged[c] = new_id
            merged_states.append(state)
        else:
            new_id = core_to_merged[c]
            merged_states[new_id] = frozenset(merged_states[new_id] | state)
        old_to_new[old_id] = new_id

    merged_transitions: dict[tuple[int, Symbol], int] = {}
    for (src_id, sym), dst_id in lr1.transitions.items():
        merged_transitions[(old_to_new[src_id], sym)] = old_to_new[dst_id]

    return merged_states, merged_transitions


def build_lalr_table(
    grammar: Grammar,
    first_sets: dict[Symbol, frozenset[Symbol]],
) -> SLRTable:
    lr1 = build_lr1_automaton(grammar, first_sets)
    lalr_states, lalr_transitions = merge_to_lalr(lr1)

    action: dict[tuple[int, str], Accept | Shift | Reduce] = {}
    goto_table: dict[tuple[int, str], int] = {}
    augmented_start_prod = grammar.productions[0]

    for (state_id, symbol), target_id in lalr_transitions.items():
        if symbol.is_terminal:
            key = (state_id, symbol.name)
            entry: Accept | Shift | Reduce = Shift(target_id)
            if key in action and action[key] != entry:
                raise ConflictError(state_id, symbol.name, action[key], entry)
            action[key] = entry
        else:
            goto_table[(state_id, symbol.name)] = target_id

    for state_id, state in enumerate(lalr_states):
        for item in state:
            prod = grammar.production_by_id(item.production_id)
            if item.dot < len(prod.body):
                continue

            if prod.id == augmented_start_prod.id:
                key = (state_id, EOF.name)
                entry = Accept()
                if key in action and action[key] != entry:
                    raise ConflictError(state_id, EOF.name, action[key], entry)
                action[key] = entry
            else:
                key = (state_id, item.lookahead.name)
                entry = Reduce(prod.id)
                if key in action and action[key] != entry:
                    raise ConflictError(state_id, item.lookahead.name, action[key], entry)
                action[key] = entry

    return SLRTable(action=action, goto_table=goto_table, grammar=grammar)
