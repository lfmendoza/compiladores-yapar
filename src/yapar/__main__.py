from __future__ import annotations

import argparse
import sys

from . import (
    ConflictError,
    ParseError,
    build_automaton,
    build_slr_table,
    first,
    follow,
    grammar_from_dict,
    parse,
    read_yalp,
    render_automaton,
    tokens_from_file,
)
from .lalr import build_lalr_table
from .validation import validate_grammar


def _print_action_table(table) -> None:
    terminals = sorted({tok for _, tok in table.action})
    header = f"{'':>6}  " + "  ".join(f"{t:>8}" for t in terminals)
    print(header)
    print("-" * len(header))
    for state in sorted({s for s, _ in table.action}):
        row = f"{state:>6}  "
        for tok in terminals:
            act = table.action.get((state, tok))
            row += f"{str(act) if act else '':>8}  "
        print(row)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m yapar",
        description="SLR(1) / LALR(1) parser generator",
    )
    ap.add_argument("grammar", help="Path to .yalp grammar file")
    ap.add_argument("input", nargs="?", help="Tab-separated token stream file to parse")
    ap.add_argument(
        "--method",
        choices=["slr", "lalr"],
        default="slr",
        help="Parsing method: slr (default) or lalr",
    )
    ap.add_argument(
        "--render",
        metavar="PATH",
        help="Render the LR(0) automaton to PATH (.dot or image)",
    )
    ap.add_argument(
        "--table",
        action="store_true",
        help="Print the ACTION table to stdout after building",
    )
    ap.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip semantic grammar validation",
    )
    args = ap.parse_args(argv)

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

    try:
        if args.method == "lalr":
            table = build_lalr_table(g, f_sets)
            print(f"method: LALR(1)  states: {len(automaton.states)}")
        else:
            table = build_slr_table(automaton, g, fl_sets)
            print(f"method: SLR(1)   states: {len(automaton.states)}")
    except ConflictError as exc:
        print(f"conflict: {exc}", file=sys.stderr)
        return 1

    print(f"action entries: {len(table.action)}  goto entries: {len(table.goto_table)}")

    if args.render:
        out = render_automaton(automaton, g, args.render)
        print(f"automaton → {out}")

    if args.table:
        print()
        _print_action_table(table)

    if args.input:
        toks = tokens_from_file(args.input)
        try:
            tree = parse(iter(toks), table)
            print("OK —", repr(tree))
        except ParseError as exc:
            print(f"parse error: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
