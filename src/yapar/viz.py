from __future__ import annotations

from .automaton import Item, LR0Automaton
from .grammar import Grammar


def _format_item(item: Item, grammar: Grammar) -> str:
    prod = grammar.production_by_id(item.production_id)
    if not prod.body:
        return f"{prod.head} \u2192 \u03b5 \u00b7"
    body_parts = [str(s) for s in prod.body]
    body_parts.insert(item.dot, "\u00b7")
    return f"{prod.head} \u2192 {' '.join(body_parts)}"


def _build_dot(automaton: LR0Automaton, grammar: Grammar) -> str:
    lines = [
        "digraph LR0 {",
        '    rankdir=LR;',
        '    node [shape=rectangle, fontname="Courier New", fontsize=10];',
        '    edge [fontname="Courier New", fontsize=9];',
        "",
    ]

    for state_id, state in enumerate(automaton.states):
        item_lines = [f"I{state_id}"]
        for item in sorted(state, key=lambda it: (it.production_id, it.dot)):
            item_lines.append(_format_item(item, grammar))
        label = "\\n".join(item_lines).replace('"', '\\"')
        lines.append(f'    s{state_id} [label="{label}"];')

    lines.append("")

    for (src_id, sym), dst_id in sorted(
        automaton.transitions.items(),
        key=lambda kv: (kv[0][0], kv[0][1].name),
    ):
        sym_label = str(sym).replace('"', '\\"')
        lines.append(f'    s{src_id} -> s{dst_id} [label="{sym_label}"];')

    lines.append("}")
    return "\n".join(lines)


def render_automaton(
    automaton: LR0Automaton,
    grammar: Grammar,
    output_path: str,
    fmt: str = "png",
) -> str:
    dot_path = output_path if output_path.endswith(".dot") else output_path + ".dot"
    dot_src = _build_dot(automaton, grammar)

    with open(dot_path, "w", encoding="utf-8") as fh:
        fh.write(dot_src)

    if output_path.endswith(".dot"):
        return dot_path

    try:
        import graphviz

        src = graphviz.Source(dot_src)
        rendered = src.render(outfile=output_path, format=fmt, cleanup=True)
        return rendered
    except Exception:
        return dot_path
