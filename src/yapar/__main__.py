"""YAPar — SLR(1) / LALR(1) parser generator CLI.

This is the primary entry point for the tool.  It accepts any .yalp grammar
and can parse input either from a pre-built TSV token file *or* from a raw
source file tokenised on-the-fly by any YALex-generated lexer.

  # Build table only
  python -m yapar examples/arithmetic.yalp

  # Parse a raw source file using a YALex lexer
  python -m yapar examples/arithmetic.yalp \\
      --lexer ../lexer-generator/arithmetic_expression_lexer.py \\
      --source myfile.txt

  # Parse a pre-built TSV token stream
  python -m yapar examples/arithmetic.yalp tokens.tsv

  # Show full pipeline: FIRST/FOLLOW + trace + automaton image
  python -m yapar examples/pico.yalp \\
      --lexer ../lexer-generator/pico_lexer.py \\
      --source examples/pico/conditional.pico \\
      --first-follow --trace --render automaton.png
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from . import (
    ConflictError,
    ParseError,
    build_automaton,
    build_slr_table,
    first,
    follow,
    grammar_from_dict,
    read_yalp,
    render_automaton,
    tokens_from_file,
)
from .engine import ParseStep, parse, parse_verbose
from .lalr import build_lalr_table
from .lexer_bridge import EOF_TOKEN, Token
from .validation import validate_grammar


# ── Dynamic lexer loading ────────────────────────────────────────────────────


def _load_yalex_lexer(lexer_path: str):
    """Dynamically import a YALex-generated Python lexer and return its Lexer class."""
    path = Path(lexer_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Lexer file not found: {lexer_path}")
    spec = importlib.util.spec_from_file_location("_yalex_lexer", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "Lexer"):
        raise AttributeError(
            f"{lexer_path} does not define a 'Lexer' class — "
            "is it a YALex-generated file?"
        )
    return module.Lexer


def _tokenize(source_text: str, LexerClass, skip: set[str]) -> list[Token]:
    """Run a YALex Lexer on source_text; return a list of Token objects."""
    lexer = LexerClass(source_text)
    try:
        raw = lexer.gettoken()
    except EOFError:
        raw = getattr(lexer, "tokens", [])

    result: list[Token] = []
    for t in raw:
        if t is None or t[0] in skip:
            continue
        result.append(Token(t[0], str(t[1]), t[2], t[3]))
    result.append(EOF_TOKEN)
    return result


# ── Display helpers ───────────────────────────────────────────────────────────


def _print_action_table(table) -> None:
    terminals = sorted({tok for _, tok in table.action})
    col_w = max((len(t) for t in terminals), default=3)
    col_w = max(col_w, 4)
    header = f"{'':>5}  " + "  ".join(f"{t:>{col_w}}" for t in terminals)
    print(header)
    print("-" * len(header))
    for state in sorted({s for s, _ in table.action}):
        row = f"{state:>5}  "
        for tok in terminals:
            act = table.action.get((state, tok))
            row += f"{str(act) if act else '':>{col_w}}  "
        if any(table.action.get((state, tok)) for tok in terminals):
            print(row)


def _print_goto_table(table) -> None:
    nts = sorted({nt for _, nt in table.goto_table})
    col_w = max((len(nt) for nt in nts), default=3)
    col_w = max(col_w, 3)
    header = f"{'':>5}  " + "  ".join(f"{nt:>{col_w}}" for nt in nts)
    print(header)
    print("-" * len(header))
    for state in sorted({s for s, _ in table.goto_table}):
        row = f"{state:>5}  "
        row += "  ".join(
            f"{str(table.goto_table.get((state, nt), '')):>{col_w}}"
            for nt in nts
        )
        if any(table.goto_table.get((state, nt)) is not None for nt in nts):
            print(row)


def _print_first_follow(grammar, f_sets, fl_sets) -> None:
    nts = sorted(
        (s for s in grammar.nonterminals if "'" not in s.name),
        key=lambda s: s.name,
    )
    aug = sorted(
        (s for s in grammar.nonterminals if "'" in s.name),
        key=lambda s: s.name,
    )
    ordered = aug + nts
    col = max(len(s.name) for s in ordered) + 2

    print("FIRST:")
    for nt in ordered:
        fs = sorted(str(s) for s in f_sets.get(nt, frozenset()) if str(s) != "e")
        eps = "  e" if any(str(s) == "e" for s in f_sets.get(nt, frozenset())) else ""
        print(f"  {nt.name:<{col}} {{ {', '.join(fs)}{eps} }}")

    print("\nFOLLOW:")
    for nt in ordered:
        fl = sorted(str(s) for s in fl_sets.get(nt, frozenset()))
        print(f"  {nt.name:<{col}} {{ {', '.join(fl)} }}")


def _print_tokens(tokens: list[Token]) -> None:
    print(f"  {'Type':<16} {'Lexeme':<14} Line  Col")
    print(f"  {'-'*16} {'-'*14} {'-'*4}  {'-'*3}")
    for t in tokens:
        if t.tipo == "$":
            continue
        print(f"  {t.tipo:<16} {t.lexema!r:<14} {t.linea:>4}  {t.columna:>3}")
    print(f"  {len(tokens)-1} tokens + EOF ($)")


def _print_trace(trace: list[ParseStep], max_steps: int = 40) -> None:
    shown = trace[:max_steps]
    extra = len(trace) - len(shown)

    S_W, Y_W, I_W = 22, 20, 26

    def _trim(s: str, w: int) -> str:
        return s if len(s) <= w else "..." + s[-(w - 3):]

    fmt = f"  {{:>4}}  {{:<{S_W}}}  {{:<{Y_W}}}  {{:<{I_W}}}  {{}}"
    print(fmt.format("#", "State stack", "Symbol stack", "Input", "Action"))
    print("  " + "-" * (4 + S_W + Y_W + I_W + 40))
    for s in shown:
        st = _trim(" ".join(str(x) for x in s.state_stack), S_W)
        sy = _trim(" ".join(s.symbol_stack) or "-", Y_W)
        inp = " ".join(s.remaining[:4]) + (" ..." if len(s.remaining) > 4 else "")
        inp = _trim(inp, I_W)
        print(fmt.format(s.step, st, sy, inp, s.action_str))
    if extra:
        print(f"  ... {extra} more steps (parse succeeded)")


# ── Main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m yapar",
        description="SLR(1) / LALR(1) parser generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Build table (show state count and entry count)
  python -m yapar examples/arithmetic.yalp

  # Parse source text with a YALex lexer
  python -m yapar examples/pico.yalp \\
      --lexer ../lexer-generator/pico_lexer.py \\
      --source examples/pico/conditional.pico

  # Full pipeline: FIRST/FOLLOW + trace + automaton image
  python -m yapar examples/arithmetic.yalp \\
      --lexer ../lexer-generator/arithmetic_expression_lexer.py \\
      --source myexpr.txt \\
      --first-follow --trace --render automaton.png

  # Parse a pre-built TSV token stream (classic mode)
  python -m yapar examples/arithmetic.yalp tokens.tsv

  # Show ACTION/GOTO tables
  python -m yapar examples/arithmetic.yalp --table""",
    )

    # Positional
    ap.add_argument("grammar", help="Path to .yalp grammar file")
    ap.add_argument(
        "input",
        nargs="?",
        help="Tab-separated token stream file (.tsv) — alternative to --source",
    )

    # Lexer / source
    ap.add_argument(
        "--lexer",
        metavar="PATH",
        help="YALex-generated lexer .py file; used with --source to tokenise text",
    )
    ap.add_argument(
        "--source",
        metavar="PATH",
        help="Source text file to tokenise with --lexer and then parse",
    )
    ap.add_argument(
        "--skip",
        metavar="TOKENS",
        default="EOL,WS",
        help="Comma-separated token types to discard from lexer output (default: EOL,WS)",
    )

    # Parser method
    ap.add_argument(
        "--method",
        choices=["slr", "lalr"],
        default="slr",
        help="Parsing method: slr (default) or lalr",
    )

    # Output options
    ap.add_argument("--render", metavar="PATH", help="Render LR(0) automaton to PATH")
    ap.add_argument("--table", action="store_true", help="Print ACTION/GOTO tables")
    ap.add_argument(
        "--first-follow",
        action="store_true",
        dest="first_follow",
        help="Print FIRST and FOLLOW sets",
    )
    ap.add_argument(
        "--trace",
        action="store_true",
        help="Print step-by-step Shift/Reduce/Goto trace",
    )
    ap.add_argument("--no-validate", action="store_true", help="Skip grammar validation")

    args = ap.parse_args(argv)

    # ── Validate mutual usage ───────────────────────────────────────────────
    if args.source and not args.lexer:
        ap.error("--source requires --lexer")
    if args.lexer and not args.source:
        ap.error("--lexer requires --source")
    if args.source and args.input:
        ap.error("--source and a positional TSV input cannot be used together")

    # ── Load and validate grammar ───────────────────────────────────────────
    raw = read_yalp(args.grammar)

    if not args.no_validate:
        errs = validate_grammar(raw)
        if errs:
            for err in errs:
                print(f"validation: {err}", file=sys.stderr)
            return 1

    g = grammar_from_dict(raw).augment()
    f_sets = first(g)
    fl_sets = follow(g, f_sets)
    automaton = build_automaton(g)

    # Render automaton early so it's produced even when the table has conflicts
    if args.render:
        out = render_automaton(automaton, g, args.render)
        print(f"automaton -> {out}")

    if args.first_follow:
        print()
        _print_first_follow(g, f_sets, fl_sets)

    # ── Build parsing table ─────────────────────────────────────────────────
    try:
        if args.method == "lalr":
            table = build_lalr_table(g, f_sets)
            print(f"method: LALR(1)  states: {len(automaton.states)}", end="")
        else:
            table = build_slr_table(automaton, g, fl_sets)
            print(f"method: SLR(1)   states: {len(automaton.states)}", end="")
    except ConflictError as exc:
        print(f"conflict: {exc}", file=sys.stderr)
        return 1

    print(
        f"  action: {len(table.action)}  goto: {len(table.goto_table)}"
        f"  prods: {len(g.productions) - 1}"
    )

    if args.table:
        print("\nACTION:")
        _print_action_table(table)
        print("\nGOTO:")
        _print_goto_table(table)

    # ── Parse input ─────────────────────────────────────────────────────────
    toks: list[Token] | None = None

    if args.source and args.lexer:
        # Generic pipeline: tokenise raw source with a YALex lexer
        try:
            LexerClass = _load_yalex_lexer(args.lexer)
        except (FileNotFoundError, AttributeError) as exc:
            print(f"lexer error: {exc}", file=sys.stderr)
            return 1

        skip = {t.strip() for t in args.skip.split(",") if t.strip()}
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"source not found: {args.source}", file=sys.stderr)
            return 1

        source_text = source_path.read_text(encoding="utf-8")

        print(f"\ntokenising {source_path.name} with {Path(args.lexer).name} ...")
        toks = _tokenize(source_text, LexerClass, skip)
        _print_tokens(toks)

    elif args.input:
        # Classic mode: TSV token stream
        toks = tokens_from_file(args.input)

    if toks is not None:
        print()
        try:
            if args.trace:
                tree, trace = parse_verbose(iter(toks), table)
                print("parse trace:")
                _print_trace(trace)
                print(f"\nresult: OK -- root = '{tree.symbol}'")
                repr_str = repr(tree)
                if len(repr_str) <= 300:
                    print(repr_str)
                else:
                    print(repr_str[:300] + " ...")
            else:
                tree = parse(iter(toks), table)
                print(f"OK: {repr(tree)[:300]}")
        except ParseError as exc:
            loc = f" at line {exc.line}, col {exc.column}" if exc.line >= 0 else ""
            print(f"parse error: unexpected '{exc.token}'{loc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
