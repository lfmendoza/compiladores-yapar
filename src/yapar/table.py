from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from .automaton import LR0Automaton
from .errors import ConflictError
from .grammar import EOF, Grammar, Symbol


@dataclass(frozen=True)
class Shift:
    state: int

    def __str__(self) -> str:
        return f"s{self.state}"


@dataclass(frozen=True)
class Reduce:
    production_id: int

    def __str__(self) -> str:
        return f"r{self.production_id}"


@dataclass(frozen=True)
class Accept:
    def __str__(self) -> str:
        return "acc"


Action = Union[Shift, Reduce, Accept]


@dataclass
class SLRTable:
    action: dict[tuple[int, str], Action]
    goto_table: dict[tuple[int, str], int]
    grammar: Grammar

    def get_action(self, state: int, token_name: str) -> Action | None:
        return self.action.get((state, token_name))

    def get_goto(self, state: int, nt_name: str) -> int | None:
        return self.goto_table.get((state, nt_name))


def build_slr_table(
    automaton: LR0Automaton,
    grammar: Grammar,
    follow_sets: dict[Symbol, frozenset[Symbol]],
) -> SLRTable:
    action: dict[tuple[int, str], Action] = {}
    goto_table: dict[tuple[int, str], int] = {}
    augmented_start_prod = grammar.productions[0]

    for (state_id, symbol), target_id in automaton.transitions.items():
        if symbol.is_terminal:
            key = (state_id, symbol.name)
            entry: Action = Shift(target_id)
            if key in action and action[key] != entry:
                raise ConflictError(state_id, symbol.name, action[key], entry)
            action[key] = entry
        else:
            goto_table[(state_id, symbol.name)] = target_id

    for state_id, state in enumerate(automaton.states):
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
                for lookahead in follow_sets.get(prod.head, frozenset()):
                    key = (state_id, lookahead.name)
                    entry = Reduce(prod.id)
                    if key in action and action[key] != entry:
                        raise ConflictError(state_id, lookahead.name, action[key], entry)
                    action[key] = entry

    return SLRTable(action=action, goto_table=goto_table, grammar=grammar)
