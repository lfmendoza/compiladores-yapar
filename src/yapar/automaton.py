from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

from .grammar import EPSILON, Grammar, Symbol


class Item(NamedTuple):
    production_id: int
    dot: int

    def __str__(self) -> str:
        return f"({self.production_id}, {self.dot})"


@dataclass
class LR0Automaton:
    states: list[frozenset[Item]]
    transitions: dict[tuple[int, Symbol], int]
    _index: dict[frozenset[Item], int] = field(default_factory=dict, repr=False)

    def state_id(self, items: frozenset[Item]) -> int | None:
        return self._index.get(items)


def closure(items: frozenset[Item], grammar: Grammar) -> frozenset[Item]:
    result: set[Item] = set(items)
    queue = list(items)

    while queue:
        item = queue.pop()
        prod = grammar.production_by_id(item.production_id)

        if item.dot >= len(prod.body):
            continue

        sym = prod.body[item.dot]
        if sym.is_terminal:
            continue

        for p in grammar.productions:
            if p.head == sym:
                new_item = Item(p.id, 0)
                if new_item not in result:
                    result.add(new_item)
                    queue.append(new_item)

    return frozenset(result)


def goto(items: frozenset[Item], symbol: Symbol, grammar: Grammar) -> frozenset[Item]:
    kernel: set[Item] = set()
    for item in items:
        prod = grammar.production_by_id(item.production_id)
        if item.dot < len(prod.body) and prod.body[item.dot] == symbol:
            kernel.add(Item(item.production_id, item.dot + 1))
    return closure(frozenset(kernel), grammar)


def build_automaton(grammar: Grammar) -> LR0Automaton:
    start_prod = grammar.productions[0]
    initial = closure(frozenset({Item(start_prod.id, 0)}), grammar)

    states: list[frozenset[Item]] = [initial]
    index: dict[frozenset[Item], int] = {initial: 0}
    transitions: dict[tuple[int, Symbol], int] = {}
    queue: list[frozenset[Item]] = [initial]

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
            next_state = goto(current, sym, grammar)
            if not next_state:
                continue

            if next_state not in index:
                index[next_state] = len(states)
                states.append(next_state)
                queue.append(next_state)

            transitions[(current_id, sym)] = index[next_state]

    return LR0Automaton(states=states, transitions=transitions, _index=index)
