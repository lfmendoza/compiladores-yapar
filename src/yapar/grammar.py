from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str
    is_terminal: bool

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        kind = "T" if self.is_terminal else "NT"
        return f"Symbol({self.name!r}, {kind})"


EPSILON: Symbol = Symbol("ε", is_terminal=True)
EOF: Symbol = Symbol("$", is_terminal=True)


@dataclass(frozen=True)
class Production:
    id: int
    head: Symbol
    body: tuple[Symbol, ...]

    def __str__(self) -> str:
        body_str = " ".join(str(s) for s in self.body) if self.body else "ε"
        return f"{self.head} → {body_str}"

    def __repr__(self) -> str:
        return f"Production({self.id}, {self.head!r}, {self.body!r})"


@dataclass(frozen=True)
class Grammar:
    terminals: frozenset[Symbol]
    nonterminals: frozenset[Symbol]
    productions: tuple[Production, ...]
    start: Symbol

    def production_by_id(self, pid: int) -> Production:
        for p in self.productions:
            if p.id == pid:
                return p
        raise KeyError(f"No production with id={pid}")

    def augment(self) -> Grammar:
        augmented_start = Symbol(f"{self.start.name}'", is_terminal=False)
        p0 = Production(id=0, head=augmented_start, body=(self.start,))
        renumbered = tuple(
            Production(idx + 1, p.head, p.body)
            for idx, p in enumerate(self.productions)
        )
        return Grammar(
            terminals=self.terminals | frozenset({EOF}),
            nonterminals=self.nonterminals | frozenset({augmented_start}),
            productions=(p0,) + renumbered,
            start=augmented_start,
        )


def grammar_from_dict(raw: dict) -> Grammar:
    terminal_names: set[str] = set(raw.get("tokens", []))
    nonterminal_names: set[str] = set(raw.get("rules", {}).keys())
    symbols: dict[str, Symbol] = {}

    for name in terminal_names:
        symbols[name] = Symbol(name, is_terminal=True)
    for name in nonterminal_names:
        symbols[name] = Symbol(name, is_terminal=False)

    def resolve(name: str) -> Symbol:
        if name not in symbols:
            symbols[name] = Symbol(name, is_terminal=name not in nonterminal_names)
        return symbols[name]

    productions: list[Production] = []
    pid = 1
    rules: dict = raw.get("rules", {})
    start_name: str = next(iter(rules)) if rules else ""

    for head_name, alternatives in rules.items():
        head = resolve(head_name)
        for body_names in alternatives:
            body = tuple(resolve(n) for n in body_names)
            productions.append(Production(id=pid, head=head, body=body))
            pid += 1

    terminals = frozenset(s for s in symbols.values() if s.is_terminal)
    nonterminals = frozenset(s for s in symbols.values() if not s.is_terminal)
    start = symbols[start_name] if start_name else Symbol("S", is_terminal=False)

    return Grammar(
        terminals=terminals,
        nonterminals=nonterminals,
        productions=tuple(productions),
        start=start,
    )
