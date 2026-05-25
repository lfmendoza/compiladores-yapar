# YAPar — Generador de Parsers SLR(1) y LALR(1)

Parser generator that reads a `.yalp` grammar file, validates it semantically, constructs the canonical LR(0)/LR(1) automaton, computes FIRST/FOLLOW sets and produces a full SLR(1) or LALR(1) ACTION/GOTO table. A stack-based LR engine then uses the table to parse a token stream and return a concrete parse tree.

Designed to integrate with the [YALex](https://github.com/lfmendoza/compiladores-yapar) lexer from the previous project phase through a shared `Token` contract.

## Quick start

```bash
pip install -e . -r requirements.txt

# Build SLR(1) table for an arithmetic grammar
python -m yapar examples/arithmetic.yalp

# Build LALR(1) table
python -m yapar examples/arithmetic.yalp --method lalr

# Print the ACTION table
python -m yapar examples/arithmetic.yalp --table

# Parse a token stream (tab-separated: tipo lexema linea columna)
python -m yapar examples/arithmetic.yalp tokens.tsv

# Render the LR(0) automaton to Graphviz
python -m yapar examples/arithmetic.yalp --render automaton.dot

# Detect a grammar conflict
python -m yapar examples/conflict_demo.yalp
```

## CLI reference

```
python -m yapar <grammar.yalp> [input.tsv]
                [--method slr|lalr]
                [--table]
                [--render PATH]
                [--no-validate]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--method` | `slr` | Build SLR(1) or LALR(1) table |
| `--table` | off | Print ACTION table to stdout |
| `--render PATH` | — | Write LR(0) automaton to `.dot` / PNG |
| `--no-validate` | off | Skip semantic grammar validation |

## Architecture

```
.yalp grammar
    │
    ▼
reader.py ──► validation.py ──► grammar.py (augment)
                                       │
                          ┌────────────┴──────────────────────┐
                          ▼                                    ▼
                   automaton.py (LR0)               lalr.py (LR1 → LALR)
                          │                                    │
                          │           sets.py (FIRST/FOLLOW)  │
                          └──────────────┬────────────────────┘
                                         ▼
                                    table.py (SLR or LALR ACTION/GOTO)
                                         │
                    .yalex DFA ──► lexer_bridge.py ──► engine.py ──► ParseNode
                                                                          │
                                                                     viz.py (.dot/PNG)
```

See [`docs/arquitectura_yapar.drawio`](docs/arquitectura_yapar.drawio) for the full diagram.

## Modules

| # | File | Responsibility |
|---|------|----------------|
| 1 | `reader.py` | `.yalp` DSL tokenizer and parser |
| 2 | `lexer_bridge.py` | YALex DFA adapter; `Token(tipo, lexema, linea, columna)` contract |
| 3 | `grammar.py` | `Symbol`, `Production`, `Grammar` frozen dataclasses + `augment()` |
| 4 | `sets.py` | FIRST / FOLLOW fixed-point computation |
| 5 | `automaton.py` | LR(0) canonical collection: `closure`, `goto`, frozenset deduplication |
| 6 | `table.py` | SLR(1) ACTION / GOTO table builder with `ConflictError` |
| 7 | `engine.py` | Stack-based LR parser engine returning `ParseNode` tree |
| 8 | `viz.py` | Graphviz automaton renderer with `.dot` fallback |
| LALR | `lalr.py` | `LR1Item`, `closure_lr1`, `merge_to_lalr`, `build_lalr_table` |
| Val | `validation.py` | Semantic grammar checks (undefined symbols, unreachable nonterminals) |

## SLR vs LALR

| Property | SLR(1) | LALR(1) |
|----------|--------|---------|
| Reduce lookahead | `FOLLOW(head)` — global | `lookahead(item)` — per-item |
| State count | Equal (same LR(0) automaton) | Equal (merged from LR(1)) |
| Conflict rate | More conservative | Fewer false conflicts |
| Accepted grammars | Strict subset of LALR | Strict subset of LR(1) |

Both use the same `SLRTable` structure and the same `engine.py` parser.

## Example grammars

| File | Description | Conflicts |
|------|-------------|-----------|
| `examples/arithmetic.yalp` | Left-recursive arithmetic with precedence | None |
| `examples/calculator.yalp` | Arithmetic + function calls + unary minus | None |
| `examples/conflict_demo.yalp` | Classic dangling-else (if/then/else) | shift/reduce on ELSE |

## Running tests

```bash
pytest --cov=src/yapar --cov-report=term-missing
```

144 tests, 96 % line coverage. The CI gate requires ≥ 80 %.

## Generating the checkpoint report

```bash
# Sprint 1 report → docs/checkpoint_sprint1.docx
python docs/generate_report.py

# M3 checkpoint report → docs/checkpoint_m3.docx
python docs/generate_m3_report.py
```

Both require `python-docx`. The generated `.docx` files are listed in `.gitignore`.

## Token stream format

The `input.tsv` file expected by the CLI is a tab-separated file with four columns per line:

```
tipo    lexema  linea  columna
ID      x       1      1
PLUS    +       1      3
ID      y       1      5
$       $       -1     -1
```

This matches the export contract of the YALex project (`Token(tipo, lexema, linea, columna)`). If the last token is not `$`, the bridge appends the EOF sentinel automatically.

## License

MIT — see [`LICENSE`](LICENSE).
