from __future__ import annotations

from dataclasses import dataclass, field

from .errors import ParseError
from .table import Accept, Reduce, Shift, SLRTable


@dataclass
class ParseNode:
    symbol: str
    children: list[ParseNode] = field(default_factory=list)
    lexeme: str = ""

    def __repr__(self) -> str:
        if self.children:
            inner = " ".join(repr(c) for c in self.children)
            return f"({self.symbol} {inner})"
        return f"{self.symbol}:{self.lexeme!r}" if self.lexeme else self.symbol


def parse(token_stream, table: SLRTable) -> ParseNode:
    grammar = table.grammar
    tokens = list(token_stream)
    pos = 0

    state_stack: list[int] = [0]
    node_stack: list[ParseNode] = []

    while True:
        tok = tokens[pos] if pos < len(tokens) else None
        tok_name = tok.tipo if tok is not None else "$"
        tok_lexeme = tok.lexema if tok is not None else "$"
        tok_line = tok.linea if tok is not None else -1
        tok_col = tok.columna if tok is not None else -1

        state = state_stack[-1]
        action = table.get_action(state, tok_name)

        if action is None:
            raise ParseError(state, tok_name, tok_line, tok_col)

        if isinstance(action, Shift):
            node_stack.append(ParseNode(symbol=tok_name, lexeme=tok_lexeme))
            state_stack.append(action.state)
            pos += 1

        elif isinstance(action, Reduce):
            prod = grammar.production_by_id(action.production_id)
            n = len(prod.body)
            children = list(node_stack[-n:]) if n else []
            if n:
                node_stack = node_stack[:-n]
                state_stack = state_stack[:-n]
            new_node = ParseNode(symbol=prod.head.name, children=children)
            node_stack.append(new_node)

            top = state_stack[-1]
            goto_state = table.get_goto(top, prod.head.name)
            if goto_state is None:
                raise ParseError(top, prod.head.name)
            state_stack.append(goto_state)

        elif isinstance(action, Accept):
            return node_stack[-1] if node_stack else ParseNode(symbol=grammar.start.name)
