from __future__ import annotations

from collections import defaultdict

from .automaton import Item, LR0Automaton
from .grammar import Grammar


def _format_item(item: Item, grammar: Grammar) -> str:
    prod = grammar.production_by_id(item.production_id)
    if not prod.body:
        return f"{prod.head} \u2192 \u03b5 \u00b7"
    parts = [str(s) for s in prod.body]
    parts.insert(item.dot, "\u00b7")
    return f"{prod.head} \u2192 {' '.join(parts)}"


def _kernel_items(
    state: frozenset[Item], state_id: int
) -> tuple[list[Item], int]:
    """Return (kernel_items, n_closure_hidden).

    Kernel definition (standard textbook):
      - I0: only the augmented-start item (production_id=0, dot=0).
      - All other states: items where dot > 0.

    Showing kernel-only keeps node labels compact.
    """
    if state_id == 0:
        kernel = [it for it in state if it.production_id == 0 and it.dot == 0]
        if not kernel:
            kernel = sorted(state, key=lambda it: (it.production_id, it.dot))[:1]
    else:
        kernel = [it for it in state if it.dot > 0]

    n_hidden = len(state) - len(kernel)
    return sorted(kernel, key=lambda it: (it.production_id, it.dot)), n_hidden


def _build_dot(automaton: LR0Automaton, grammar: Grammar) -> str:
    aug_start = grammar.productions[0]
    accept_item = Item(aug_start.id, len(aug_start.body))

    # Classify states
    accept_states: set[int] = set()
    reduce_only_states: set[int] = set()
    for sid, state in enumerate(automaton.states):
        if accept_item in state:
            accept_states.add(sid)
        elif all(
            grammar.production_by_id(it.production_id).body is not None
            and it.dot >= len(grammar.production_by_id(it.production_id).body)
            for it in state
        ):
            reduce_only_states.add(sid)

    lines = [
        "digraph LR0 {",
        "    rankdir=LR;",
        '    graph [nodesep=0.25 ranksep=0.6 fontname="Helvetica"];',
        '    node  [shape=rectangle style=filled fillcolor=white'
        '           fontname="Courier New" fontsize=9 margin="0.12,0.06"];',
        '    edge  [fontname="Courier New" fontsize=8 arrowsize=0.7];',
        "",
    ]

    # Invisible start arrow into I0
    lines.append('    __start [label="" shape=none width=0 height=0];')
    lines.append("    __start -> s0;")
    lines.append("")

    for state_id, state in enumerate(automaton.states):
        kernel, n_hidden = _kernel_items(state, state_id)

        rows = [f"I{state_id}"]
        for item in kernel:
            rows.append(_format_item(item, grammar))
        if n_hidden:
            rows.append(f"(+{n_hidden})")

        label = "\\n".join(rows).replace('"', '\\"')

        # Choose fill colour by state role
        if state_id == 0:
            fill = "#D6EAF8"   # light blue  – initial
        elif state_id in accept_states:
            fill = "#D5F5E3"   # light green – accept
        elif state_id in reduce_only_states:
            fill = "#FDEBD0"   # light orange – pure reduce
        else:
            fill = "white"

        extra = f' fillcolor="{fill}"'
        if state_id in accept_states:
            extra += " peripheries=2"

        lines.append(f'    s{state_id} [label="{label}"{extra}];')

    lines.append("")

    for (src_id, sym), dst_id in sorted(
        automaton.transitions.items(),
        key=lambda kv: (kv[0][0], kv[0][1].name),
    ):
        sym_label = str(sym).replace('"', '\\"')
        is_terminal = sym.is_terminal
        style = 'color="#1A5276"' if is_terminal else 'color="#7D6608" style=dashed'
        lines.append(
            f'    s{src_id} -> s{dst_id} [label="{sym_label}" {style}];'
        )

    lines.append("}")
    return "\n".join(lines)


def render_automaton(
    automaton: LR0Automaton,
    grammar: Grammar,
    output_path: str,
    fmt: str = "png",
) -> str:
    """Render the LR(0) automaton.

    Writes a .dot file alongside the output.  If graphviz is available the
    image is rendered; otherwise only the .dot file is returned.
    """
    dot_path = (
        output_path if output_path.endswith(".dot") else output_path + ".dot"
    )
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
