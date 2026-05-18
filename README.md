# YAPar — Generador de Parser SLR(1)

Parser generator that reads a `.yalp` grammar description and produces an SLR(1) parse table, executing the canonical LR(0) automaton construction algorithm together with FIRST/FOLLOW set computation. Designed to integrate with the YALex lexer from the previous project phase.

## Architecture

```
.yalp grammar ──► reader ──► Grammar (augmented) ──► FIRST/FOLLOW ──► LR(0) automaton ──► SLR(1) table ──► LR engine
                    ▲                                                                                            ▲
               .yalex DFA ─────────────────── lexer bridge ────────────────────────────────────────────────────┘
                                                    ▲
                                              source string
```

See [`docs/arquitectura_yapar.drawio`](docs/arquitectura_yapar.drawio) for the full module diagram.

## Requirements

- Python 3.12+
- `pip install -e . -r requirements.txt`

The Graphviz binary is optional; if absent the automaton renderer writes `.dot` files only and prints a warning.

## Usage

```bash
python -m yapar grammar.yalp tokens.tsv
python -m yapar grammar.yalp --render automaton.png
```

The token stream file is a tab-separated file with columns `tipo`, `lexema`, `linea`, `columna` (one token per line), matching the contract exported by YALex.

## Modules

| # | File | Responsibility |
|---|------|----------------|
| 1 | `reader.py` | `.yalp` DSL tokenizer and parser |
| 2 | `lexer_bridge.py` | YALex DFA adapter; defines `Token` contract |
| 3 | `grammar.py` | `Symbol`, `Production`, `Grammar` frozen dataclasses |
| 4 | `sets.py` | FIRST / FOLLOW fixed-point computation |
| 5 | `automaton.py` | LR(0) canonical collection |
| 6 | `table.py` | SLR(1) ACTION / GOTO table builder |
| 7 | `engine.py` | Stack-based LR parser engine |
| 8 | `viz.py` | Graphviz automaton renderer |

## Running tests

```bash
pytest --cov=src/yapar --cov-report=term-missing
```

The CI target requires at least 80 % line coverage (`--cov-fail-under=80`).

## Generating the checkpoint report

```bash
python docs/generate_report.py
```

Produces `docs/checkpoint_sprint1.docx`. Requires `python-docx` and an optional `docs/kanban_sprint1.png` for the embedded Kanban screenshot.

## License

MIT — see [`LICENSE`](LICENSE).
