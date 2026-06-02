#!/usr/bin/env python3
"""
Demostración end-to-end con visualización completa de todos los pasos internos.

Cubre los tres ejemplos del proyecto mostrando CADA etapa del pipeline:
  [1] Tokenización (YALex)
  [2] Conjuntos FIRST y FOLLOW
  [3] Autómata LR(0) — estados e ítems
  [4] Tabla ACTION / GOTO
  [5] Traza de parseo paso a paso (Shift / Reduce / Goto / Accept)
  [6] Árbol de parseo resultante

Ejecutar desde la raíz de compiladores-yapar/:
  python e2e_demo.py
"""

from __future__ import annotations

import io
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Ruta hacia el proyecto hermano YALex ──────────────────────────────────────
_HERE = Path(__file__).parent
_YALEX = _HERE.parent / "lexer-generator"

if not _YALEX.exists():
    sys.exit(
        f"ERROR: No se encontró lexer-generator en {_YALEX}\n"
        "Asegúrate de que ambos proyectos estén en el mismo directorio padre."
    )
sys.path.insert(0, str(_YALEX))

# ── Imports de YAPar ──────────────────────────────────────────────────────────
from yapar.automaton import build_automaton
from yapar.engine import ParseStep, parse_verbose
from yapar.errors import ConflictError
from yapar.grammar import grammar_from_dict
from yapar.lalr import build_lalr_table
from yapar.lexer_bridge import EOF_TOKEN, Token
from yapar.reader import read_yalp
from yapar.sets import first, follow
from yapar.table import build_slr_table
from yapar.viz import render_automaton

# ── Bridge: YALex tuple → YAPar Token ────────────────────────────────────────
_SKIP = {"EOL", "ASSIGN"}


def bridge(raw: list) -> list[Token]:
    result: list[Token] = []
    for t in raw:
        if t is None or t[0] in _SKIP:
            continue
        result.append(Token(t[0], str(t[1]), t[2], t[3]))
    result.append(EOF_TOKEN)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def _bar(char: str = "═", width: int = 70) -> str:
    return char * width


def header(title: str) -> None:
    b = _bar()
    print(f"\n{b}\n  {title}\n{b}")


def subsection(label: str) -> None:
    print(f"\n  {'─'*60}")
    print(f"  {label}")
    print(f"  {'─'*60}")


# ── [1] Tokenización ─────────────────────────────────────────────────────────

def show_tokens(tokens: list[Token], entrada: str) -> None:
    subsection("[1] Tokenización  (YALex)")
    print(f"  Entrada : {entrada!r}\n")
    print(f"  {'Tipo':<14} {'Lexema':<12} {'Línea':>5}  {'Col':>4}")
    print(f"  {'─'*14} {'─'*12} {'─'*5}  {'─'*4}")
    for tok in tokens:
        if tok.tipo == "$":
            continue
        print(f"  {tok.tipo:<14} {tok.lexema!r:<12} {tok.linea:>5}  {tok.columna:>4}")
    print(f"  {'─'*38}")
    print(f"  {len(tokens)-1} tokens  +  1 centinela EOF ($)")


# ── [2] FIRST / FOLLOW ────────────────────────────────────────────────────────

def show_first_follow(grammar, first_sets, follow_sets) -> None:
    subsection("[2] Conjuntos FIRST y FOLLOW  (yapar/sets.py)")

    nts = sorted(
        (s for s in grammar.nonterminals if "'" not in s.name),
        key=lambda s: s.name,
    )
    aug = [s for s in grammar.nonterminals if "'" in s.name]
    ordered = aug + nts

    col = 14

    print(f"\n  {'No-terminal':<{col}}  FIRST")
    print(f"  {'─'*col}  {'─'*40}")
    for nt in ordered:
        fs = first_sets.get(nt, frozenset())
        symbols = sorted(str(s) for s in fs if str(s) != "ε")
        eps = "  ε" if any(str(s) == "ε" for s in fs) else ""
        print(f"  {nt.name:<{col}}  {{ {', '.join(symbols)}{eps} }}")

    print(f"\n  {'No-terminal':<{col}}  FOLLOW")
    print(f"  {'─'*col}  {'─'*40}")
    for nt in ordered:
        fls = follow_sets.get(nt, frozenset())
        symbols = sorted(str(s) for s in fls)
        print(f"  {nt.name:<{col}}  {{ {', '.join(symbols)} }}")

    print()
    print("  Nota: FOLLOW se usa en SLR para decidir cuándo Reduce.")
    print("  LALR usa lookaheads por ítem (más precisos que FOLLOW global).")


# ── [3] Autómata LR(0) ────────────────────────────────────────────────────────

def _fmt_item(item, grammar) -> str:
    """Format an LR(0) item as  A → α · β"""
    prod = grammar.production_by_id(item.production_id)
    if not prod.body:
        return f"{prod.head} → ε ·"
    parts = [str(s) for s in prod.body]
    parts.insert(item.dot, "·")
    return f"{prod.head} → {' '.join(parts)}"


def show_lr0_states(automaton, grammar, max_states=None, highlight=None) -> None:
    subsection("[3] Autómata LR(0) — estados e ítems  (yapar/automaton.py)")

    n_total = len(automaton.states)
    shown = n_total if max_states is None else min(max_states, n_total)

    # Build per-state transition list
    outgoing: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for (src, sym), dst in automaton.transitions.items():
        outgoing[src].append((sym.name, dst))

    print(f"\n  Total: {n_total} estados,  {len(automaton.transitions)} transiciones")
    if shown < n_total:
        print(f"  (mostrando {shown} de {n_total} — ver imagen PNG para el grafo completo)\n")
    else:
        print()

    for state_id in range(shown):
        state = automaton.states[state_id]
        marker = "  ◄ CONFLICTO" if state_id == highlight else ""
        print(f"  I{state_id}:{marker}")
        for item in sorted(state, key=lambda it: (it.production_id, it.dot)):
            print(f"    {_fmt_item(item, grammar)}")
        trans = sorted(outgoing.get(state_id, []))
        if trans:
            parts = "  ".join(f"{sym}→I{dst}" for sym, dst in trans)
            print(f"    Transiciones: {parts}")
        print()


def try_render(automaton, grammar, name: str) -> str | None:
    """Render the automaton to PNG (or .dot if graphviz unavailable)."""
    out = str(_HERE / name)
    try:
        result = render_automaton(automaton, grammar, out)
        print(f"  Imagen guardada: {result}")
        print("  (abre el archivo para ver el grafo completo)")
        return result
    except Exception as exc:
        print(f"  No se pudo renderizar: {exc}")
        return None


# ── [4] Tabla ACTION / GOTO ───────────────────────────────────────────────────

def show_action_goto_table(table) -> None:
    subsection("[4] Tabla ACTION / GOTO  (yapar/table.py)")

    terminals = sorted({tok for _, tok in table.action})
    nts = sorted({nt for _, nt in table.goto_table})
    all_states = sorted(
        set(s for s, _ in table.action) | set(s for s, _ in table.goto_table)
    )

    s_w = max(3, len(str(max(all_states))))
    t_ws = {t: max(len(t), 3) for t in terminals}
    nt_ws = {nt: max(len(nt), 3) for nt in nts}

    def _row_action(state: int) -> str:
        cells = []
        for t in terminals:
            act = table.action.get((state, t))
            cells.append(f"{str(act) if act else '':>{t_ws[t]}}")
        return " ".join(cells)

    def _row_goto(state: int) -> str:
        cells = []
        for nt in nts:
            g = table.goto_table.get((state, nt))
            cells.append(f"{str(g) if g is not None else '':>{nt_ws[nt]}}")
        return " ".join(cells)

    # ACTION table
    print(f"\n  ACTION  ({len(table.action)} entradas)\n")
    hdr = f"  {'':>{s_w}}  " + " ".join(f"{t:>{t_ws[t]}}" for t in terminals)
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))
    for state in all_states:
        row = _row_action(state)
        if any(c.strip() for c in row.split()):
            print(f"  {state:>{s_w}}  {row}")

    # GOTO table
    if nts:
        print(f"\n  GOTO  ({len(table.goto_table)} entradas)\n")
        hdr2 = f"  {'':>{s_w}}  " + " ".join(f"{nt:>{nt_ws[nt]}}" for nt in nts)
        print(hdr2)
        print("  " + "─" * (len(hdr2) - 2))
        for state in all_states:
            row = _row_goto(state)
            if any(c.strip() for c in row.split()):
                print(f"  {state:>{s_w}}  {row}")

    print(f"\n  Leyenda:  sN = Shift al estado N  |  rN = Reduce prod N  |  acc = Accept")


# ── [5] Traza de parseo ───────────────────────────────────────────────────────

def show_parse_trace(trace: list[ParseStep], max_steps: int | None = None) -> None:
    subsection("[5] Traza de parseo paso a paso  (yapar/engine.py)")

    shown = trace if max_steps is None else trace[:max_steps]
    truncated = len(trace) - len(shown)

    S_W, Y_W, I_W = 22, 20, 26

    def _trim(s: str, w: int) -> str:
        return s if len(s) <= w else "…" + s[-(w - 1):]

    fmt = f"  {{:>4}}  {{:<{S_W}}}  {{:<{Y_W}}}  {{:<{I_W}}}  {{}}"
    print()
    print(fmt.format("#", "Pila estados", "Pila simbolos", "Entrada", "Accion"))
    print("  " + "─" * (4 + S_W + Y_W + I_W + 42))

    for s in shown:
        states_str = _trim(" ".join(str(x) for x in s.state_stack), S_W)
        syms_str = _trim(" ".join(s.symbol_stack) or "─", Y_W)
        rem_str = " ".join(s.remaining[:4])
        if len(s.remaining) > 4:
            rem_str += " …"
        rem_str = _trim(rem_str, I_W)
        print(fmt.format(s.step, states_str, syms_str, rem_str, s.action_str))

    if truncated:
        print(f"\n  ... {truncated} pasos adicionales (parseo exitoso)")


# ── Helpers de construcción ───────────────────────────────────────────────────

def _build(grammar_path: str, method: str = "slr"):
    raw = read_yalp(str(_HERE / grammar_path))
    g = grammar_from_dict(raw).augment()
    f = first(g)
    fl = follow(g, f)
    auto = build_automaton(g)
    if method == "lalr":
        table = build_lalr_table(g, f)
    else:
        table = build_slr_table(auto, g, fl)
    return g, f, fl, auto, table


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO 1 — ARITMÉTICA  (demo educativo completo)
#   Spec YALex : lexer-generator/specs/yal/arithmetic_expression.yal
#   Gramática  : examples/arithmetic.yalp
# ═══════════════════════════════════════════════════════════════════════════════

header("DEMO 1 — Gramática Aritmética  [arithmetic_expression.yal + arithmetic.yalp]")

from arithmetic_expression_lexer import Lexer as _ALex  # noqa: E402

D1_INPUT = "1 + 2 * 3"
_raw1 = _ALex(D1_INPUT).gettoken()
d1_tokens = bridge(_raw1)

# [1] Tokens
show_tokens(d1_tokens, D1_INPUT)

# [2] FIRST / FOLLOW
_g1, _f1, _fl1, _auto1, _t1 = _build("examples/arithmetic.yalp")
show_first_follow(_g1, _f1, _fl1)

# [3] Autómata LR(0) — mostrar todos los estados (17 es manejable)
subsection("[3] Autómata LR(0)  (yapar/automaton.py)")
print(f"\n  Renderizando imagen del autómata...")
try_render(_auto1, _g1, "automaton_arith.png")
show_lr0_states(_auto1, _g1)

# [4] Tabla ACTION / GOTO
show_action_goto_table(_t1)

# [5] Traza SLR
subsection("[5] Traza de parseo SLR(1) — método  SLR(1)")
print(f"  Entrada: {D1_INPUT!r}")
_tree1_slr, _trace1 = parse_verbose(iter(d1_tokens), _t1)
show_parse_trace(_trace1)

# Comparativa rápida LALR
subsection("[5b] Comparativa LALR(1)")
_, _f1b, _, _, _t1_lalr = _build("examples/arithmetic.yalp", "lalr")
_tree1_lalr, _trace1_lalr = parse_verbose(iter(bridge(_raw1)), _t1_lalr)
print(f"\n  LALR entradas ACTION : {len(_t1_lalr.action)}"
      f"   SLR entradas ACTION : {len(_t1.action)}")
print(f"  Árbol LALR idéntico al SLR: {repr(_tree1_slr) == repr(_tree1_lalr)}")

# [6] Árbol
subsection("[6] Árbol de parseo resultante")
print(f"\n  {_tree1_slr!r}")
print()
print("  Lectura del árbol:")
print("    expr → expr(1) PLUS term(2*3)")
print("    term → term(2) TIMES factor(3)   ← la multiplicación agrupa primero")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO 2 — CALCULADORA CON LLAMADAS A FUNCIÓN
#   Spec YALex : lexer-generator/specs/yal/calculator.yal
#   Gramática  : examples/calculator.yalp
# ═══════════════════════════════════════════════════════════════════════════════

header("DEMO 2 — Calculadora con Llamadas  [calculator.yal + calculator.yalp]")

from calculator_lexer import Lexer as _CLex  # noqa: E402

D2_INPUT = "g(x, y - 1) + f(2)"
_raw2 = _CLex(D2_INPUT).gettoken()
d2_tokens = bridge(_raw2)

# [1] Tokens
show_tokens(d2_tokens, D2_INPUT)

# [2] FIRST / FOLLOW
_g2, _f2, _fl2, _auto2, _t2 = _build("examples/calculator.yalp")
show_first_follow(_g2, _f2, _fl2)

# [3] Autómata LR(0) — mostrar solo los primeros 6 estados (27 es mucho para terminal)
subsection("[3] Autómata LR(0)  (yapar/automaton.py)")
print(f"\n  Renderizando imagen del autómata...")
try_render(_auto2, _g2, "automaton_calc.png")
show_lr0_states(_auto2, _g2, max_states=6)

# [4] Tabla ACTION / GOTO
show_action_goto_table(_t2)

# [5] Traza (limitar a 25 pasos para no saturar)
subsection("[5] Traza de parseo SLR(1)")
print(f"  Entrada: {D2_INPUT!r}")
_tree2, _trace2 = parse_verbose(iter(d2_tokens), _t2)
show_parse_trace(_trace2, max_steps=25)

# [6] Árbol
subsection("[6] Árbol de parseo resultante")
print(f"\n  {_tree2!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO 3 — CONFLICTO SHIFT/REDUCE (dangling else)
#   Spec YALex : lexer-generator/specs/yal/control_flow.yal
#   Gramática  : examples/conflict_demo.yalp  → ConflictError en construcción
# ═══════════════════════════════════════════════════════════════════════════════

header("DEMO 3 — Conflicto Dangling-Else  [control_flow.yal + conflict_demo.yalp]")

from control_flow_lexer import Lexer as _CFLex  # noqa: E402

D3_INPUT = "if cond then if cond2 then x else y"
_raw3 = _CFLex(D3_INPUT).gettoken()
d3_tokens = bridge(_raw3)

# [1] Tokens
show_tokens(d3_tokens, D3_INPUT)

# [2] FIRST / FOLLOW
_g3 = grammar_from_dict(read_yalp(str(_HERE / "examples/conflict_demo.yalp"))).augment()
_f3 = first(_g3)
_fl3 = follow(_g3, _f3)
show_first_follow(_g3, _f3, _fl3)

# [3] Autómata LR(0) — mostrar todos (son pocos) y resaltar estado conflictivo
_auto3 = build_automaton(_g3)
subsection("[3] Autómata LR(0) — todos los estados")
print(f"\n  Renderizando imagen del autómata...")
try_render(_auto3, _g3, "automaton_conflict.png")
print()
print("  El estado con CONFLICTO es aquel que contiene AMBAS estas situaciones:")
print("    stmt → IF STMT THEN stmt ·   (quiere Reduce cuando ELSE sigue)")
print("    stmt → IF STMT THEN stmt · ELSE stmt  (quiere Shift ELSE)")
print()
show_lr0_states(_auto3, _g3, highlight=6)  # state 6 is the conflict state

# [4] Intento de construcción — capturar y explicar el conflicto
subsection("[4] Tabla ACTION — Intento de construcción SLR(1)")
print()
try:
    _t3_slr = build_slr_table(_auto3, _g3, _fl3)
    print("  Sin conflicto (resultado inesperado)")
except ConflictError as e:
    print(f"  CONFLICTO DETECTADO en estado {e.state}, simbolo '{e.symbol}'")
    print(f"  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │  Accion existente  :  {str(e.existing):<38}│")
    print(f"  │  Accion entrante   :  {str(e.incoming):<38}│")
    print(f"  └──────────────────────────────────────────────────────────┘")
    print()
    print("  Por qué ocurre (FOLLOW(stmt) = { $, ELSE }):")
    print("    Produccion 2: stmt → IF STMT THEN stmt")
    print("    FOLLOW(stmt) contiene ELSE → se coloca Reduce r2 en ACTION[I6, ELSE]")
    print("    Pero tambien: stmt → IF STMT THEN stmt · ELSE stmt")
    print("    requiere Shift al estado siguiente → ACTION[I6, ELSE] ya tiene r2")
    print()
    print("  Resultado: SLR no puede construir la tabla — ambigüedad real.")

subsection("[4b] El mismo conflicto con LALR(1)")
try:
    build_lalr_table(_g3, _f3)
    print("  Sin conflicto (resultado inesperado)")
except ConflictError as e:
    print(f"\n  LALR también falla — estado {e.state}, simbolo '{e.symbol}'")
    print(f"  {e.existing}  vs  {e.incoming}")
    print()
    print("  Conclusion: es una ambiguedad genuina de la gramatica,")
    print("  no un falso positivo de SLR. Ni LALR ni SLR pueden resolverla")
    print("  sin modificar la gramatica o añadir reglas de precedencia.")


# ── Cierre ────────────────────────────────────────────────────────────────────
print("\n" + _bar() + "\n  Demo completado.\n" + _bar() + "\n")
print("  Archivos generados:")
print(f"    automaton_arith.png    — autómata LR(0) gramática aritmética")
print(f"    automaton_calc.png     — autómata LR(0) gramática calculadora")
print(f"    automaton_conflict.png — autómata LR(0) gramática dangling-else")
print()
