from __future__ import annotations

from .automaton import Item, LR0Automaton, build_automaton, closure, goto
from .engine import ParseNode, ParseStep, parse, parse_verbose
from .errors import ConflictError, ParseError, YAParError, YAParSyntaxError
from .grammar import EOF, EPSILON, Grammar, Production, Symbol, grammar_from_dict
from .lalr import (
    LR1Automaton,
    LR1Item,
    build_lalr_table,
    build_lr1_automaton,
    closure_lr1,
    core,
    goto_lr1,
    merge_to_lalr,
)
from .lexer_bridge import EOF_TOKEN, Token, load_dfa, tokenize, tokens_from_file
from .reader import parse_yalp, read_yalp
from .sets import first, first_of_sequence, follow
from .table import Accept, Reduce, Shift, SLRTable, build_slr_table
from .validation import check_grammar, validate_grammar
from .viz import render_automaton

__all__ = [
    "YAParError",
    "YAParSyntaxError",
    "ConflictError",
    "ParseError",
    "Grammar",
    "Symbol",
    "Production",
    "grammar_from_dict",
    "EPSILON",
    "EOF",
    "read_yalp",
    "parse_yalp",
    "Token",
    "tokenize",
    "load_dfa",
    "tokens_from_file",
    "EOF_TOKEN",
    "first",
    "follow",
    "first_of_sequence",
    "build_automaton",
    "LR0Automaton",
    "Item",
    "closure",
    "goto",
    "build_slr_table",
    "SLRTable",
    "Shift",
    "Reduce",
    "Accept",
    "parse",
    "parse_verbose",
    "ParseNode",
    "ParseStep",
    "render_automaton",
    "LR1Item",
    "LR1Automaton",
    "closure_lr1",
    "goto_lr1",
    "build_lr1_automaton",
    "core",
    "merge_to_lalr",
    "build_lalr_table",
    "validate_grammar",
    "check_grammar",
]
