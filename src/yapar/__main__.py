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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m yapar",
        description="SLR(1) parser generator",
    )
    ap.add_argument("grammar", help="Path to .yalp grammar file")
    ap.add_argument("input", nargs="?", help="Tab-separated token stream file to parse")
    ap.add_argument(
        "--render",
        metavar="PATH",
        help="Render the LR(0) automaton to PATH (.dot or image)",
    )
    args = ap.parse_args(argv)

    raw = read_yalp(args.grammar)
    g = grammar_from_dict(raw).augment()
    f_sets = first(g)
    fl_sets = follow(g, f_sets)
    automaton = build_automaton(g)

    try:
        table = build_slr_table(automaton, g, fl_sets)
    except ConflictError as exc:
        print(f"conflict: {exc}", file=sys.stderr)
        return 1

    if args.render:
        out = render_automaton(automaton, g, args.render)
        print(f"automaton → {out}")

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
