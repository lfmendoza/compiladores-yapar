"""
Generates all images required by the M3 checkpoint document.

    python docs/generate_images.py

Produces:
  docs/kanban_m3.png          - Kanban board at Sprint 2 close
  docs/arquitectura_yapar.png - Pipeline architecture diagram
  docs/automaton_sample.png   - LR(0) automaton for the simple arithmetic grammar
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.patches import FancyBboxPatch

DOCS_DIR = Path(__file__).parent


def _kanban() -> None:
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor("#F0F4F8")

    columns = [
        ("Hecho", "#27AE60", 0.25, [
            "Arquitectura (KR1)",
            "CI/CD GitHub Actions",
            "Scaffolding del repo",
            "Fixtures YALex",
            "Módulo 1 — reader.py",
            "Módulo 2 — lexer_bridge.py",
            "Módulo 3 — grammar.py",
            "Módulo 4 — sets.py",
            "Módulo 5 — automaton.py",
            "Módulo 6 — table.py (SLR)",
            "Módulo 7 — engine.py",
            "Módulo 8 — viz.py",
            "CLI __main__.py",
            "LALR — lalr.py completo",
            "Validación semántica",
            "Suite de tests (144)",
            "Docs M3 (MD + Word)",
            "Ejemplos examples/",
        ]),
        ("En Progreso", "#2980B9", 4.75, [
            "CLI --method lalr",
            "Tests gramáticas Dragon Book",
            "Integración YALex real",
        ]),
        ("En Revisión", "#8E44AD", 9.25, [
            "Documentación final",
            "Demo end-to-end video",
        ]),
        ("Backlog", "#7F8C8D", 13.75, [
            "Exportar tabla CSV/JSON",
            "Recuperación de errores",
            "Soporte gramáticas LALR(1)\nexclusivas (no SLR)",
        ]),
    ]

    col_width = 4.0
    card_h = 0.52
    card_gap = 0.08
    header_h = 0.7
    top_y = 10.3

    for title, color, x_center, cards in columns:
        x0 = x_center - col_width / 2
        col_bg = FancyBboxPatch(
            (x0, 0.2), col_width, 10.2,
            boxstyle="round,pad=0.05",
            linewidth=1.2,
            edgecolor="#BDC3C7",
            facecolor="#FFFFFF",
        )
        ax.add_patch(col_bg)

        header = FancyBboxPatch(
            (x0, top_y - header_h + 0.05), col_width, header_h,
            boxstyle="round,pad=0.05",
            linewidth=0,
            facecolor=color,
        )
        ax.add_patch(header)

        ax.text(
            x_center, top_y - header_h / 2 + 0.05,
            f"{title}  ({len(cards)})",
            ha="center", va="center",
            fontsize=11, fontweight="bold", color="white",
        )

        y = top_y - header_h - card_gap
        for card in cards:
            if y < 0.4:
                break
            card_rect = FancyBboxPatch(
                (x0 + 0.12, y - card_h), col_width - 0.24, card_h,
                boxstyle="round,pad=0.04",
                linewidth=0.8,
                edgecolor=color,
                facecolor="#FAFAFA",
            )
            ax.add_patch(card_rect)
            ax.text(
                x_center, y - card_h / 2,
                card,
                ha="center", va="center",
                fontsize=7.5, color="#2C3E50",
                wrap=True,
            )
            y -= card_h + card_gap

    ax.text(
        9, 10.75,
        "YAPar — Tablero Kanban · Cierre Sprint 2 · 24 mayo 2026",
        ha="center", va="center",
        fontsize=13, fontweight="bold", color="#2C3E50",
    )
    ax.text(
        9, 10.45,
        "Repositorio: https://github.com/lfmendoza/compiladores-yapar",
        ha="center", va="center",
        fontsize=8, color="#7F8C8D",
    )

    out = DOCS_DIR / "kanban_m3.png"
    fig.savefig(str(out), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  kanban_m3.png  -> {out}")


def _architecture() -> None:
    dot_src = """digraph Architecture {
    rankdir=LR;
    graph [bgcolor="#F8F9FA" fontname="Helvetica" pad="0.4" nodesep="0.5" ranksep="0.9"];
    node [fontname="Helvetica" fontsize=11 style="filled,rounded" shape=box height=0.45];
    edge [fontname="Helvetica" fontsize=9 color="#555555"];

    // Inputs
    yalp [label=".yalp grammar" fillcolor="#D5E8D4" color="#82B366"];
    tsv  [label="tokens.tsv\\n(YALex output)" fillcolor="#DAE8FC" color="#6C8EBF"];

    // Pipeline modules
    reader    [label="1. reader.py\\nDSL parser" fillcolor="#FFF2CC" color="#D6B656"];
    validation[label="validation.py\\nSemantic checks" fillcolor="#FFE6CC" color="#D79B00"];
    grammar   [label="3. grammar.py\\nSymbol · Production\\nGrammar + augment()" fillcolor="#FFF2CC" color="#D6B656"];
    sets      [label="4. sets.py\\nFIRST / FOLLOW" fillcolor="#FFF2CC" color="#D6B656"];
    automaton [label="5. automaton.py\\nLR(0) canonical\\ncollection" fillcolor="#FFF2CC" color="#D6B656"];
    slr_table [label="6. table.py\\nSLR(1) ACTION/GOTO" fillcolor="#FFF2CC" color="#D6B656"];
    lalr_mod  [label="lalr.py\\nLR1Item · merge_to_lalr\\nLALR(1) ACTION/GOTO" fillcolor="#E1D5E7" color="#9673A6"];
    bridge    [label="2. lexer_bridge.py\\nToken contract\\nYALex adapter" fillcolor="#FFF2CC" color="#D6B656"];
    engine    [label="7. engine.py\\nLR stack parser\\nParseNode tree" fillcolor="#FFF2CC" color="#D6B656"];
    viz       [label="8. viz.py\\nGraphviz renderer\\n.dot / PNG" fillcolor="#FFF2CC" color="#D6B656"];

    // Outputs
    tree   [label="ParseNode\\ntree" fillcolor="#D5E8D4" color="#82B366"];
    dotout [label=".dot / PNG\\nautomaton" fillcolor="#D5E8D4" color="#82B366"];

    // Edges
    yalp -> reader;
    reader -> validation;
    validation -> grammar;
    grammar -> sets;
    grammar -> automaton;
    sets -> slr_table [label="FOLLOW sets"];
    automaton -> slr_table [label="LR(0) states"];
    automaton -> lalr_mod [label="LR(0) base" style=dashed color="#9673A6"];
    sets -> lalr_mod [label="FIRST sets" style=dashed color="#9673A6"];
    slr_table -> engine [label="SLR table"];
    lalr_mod -> engine [label="LALR table" style=dashed color="#9673A6"];
    tsv -> bridge;
    bridge -> engine [label="Token stream"];
    engine -> tree;
    automaton -> viz;
    viz -> dotout;

    // Subgraph for SLR vs LALR
    { rank=same; slr_table; lalr_mod; }
}"""

    try:
        import graphviz
        src = graphviz.Source(dot_src)
        out = DOCS_DIR / "arquitectura_yapar"
        src.render(outfile=str(out), format="png", cleanup=True)
        final = DOCS_DIR / "arquitectura_yapar.png"
        print(f"  arquitectura_yapar.png -> {final}")
    except Exception as exc:
        dot_path = DOCS_DIR / "arquitectura_yapar.dot"
        dot_path.write_text(dot_src, encoding="utf-8")
        print(f"  graphviz binary not found ({exc}); wrote {dot_path}")
        print("  Run: dot -Tpng arquitectura_yapar.dot -o arquitectura_yapar.png")


def _automaton_sample() -> None:
    repo_root = DOCS_DIR.parent
    sys.path.insert(0, str(repo_root / "src"))

    try:
        from yapar.grammar import grammar_from_dict
        from yapar.automaton import build_automaton
        from yapar.sets import first, follow
        from yapar.viz import render_automaton

        raw = {
            "tokens": ["ID", "PLUS", "TIMES", "LPAREN", "RPAREN"],
            "rules": {
                "E": [["E", "PLUS", "T"], ["T"]],
                "T": [["T", "TIMES", "F"], ["F"]],
                "F": [["LPAREN", "E", "RPAREN"], ["ID"]],
            },
        }
        g = grammar_from_dict(raw).augment()
        a = build_automaton(g)

        out = str(DOCS_DIR / "automaton_sample.png")
        result = render_automaton(a, g, out, fmt="png")
        print(f"  automaton_sample -> {result}")
    except Exception as exc:
        print(f"  automaton_sample skipped: {exc}")


if __name__ == "__main__":
    print("Generating checkpoint images...")
    _kanban()
    _architecture()
    _automaton_sample()
    print("Done.")
