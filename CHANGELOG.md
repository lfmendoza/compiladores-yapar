# Changelog

All notable changes to YAPar are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## [0.3.0] — 2026-05-24 — Entrega final

### Added
- `src/yapar/lalr.py`: módulo LALR(1) completo — `LR1Item`, `closure_lr1`, `goto_lr1`, `build_lr1_automaton`, `core`, `merge_to_lalr`, `build_lalr_table`
- `src/yapar/validation.py`: validación semántica de gramáticas — símbolos no declarados, no terminales inalcanzables
- `examples/`: gramáticas de demo (`arithmetic.yalp`, `calculator.yalp`, `conflict_demo.yalp`)
- `docs/M3_Checkpoint_Report.md`: reporte de avance M3 con estado del pipeline y roadmap
- `docs/generate_m3_report.py`: script que genera `docs/checkpoint_m3.docx`
- `tests/test_lalr.py`: 19 tests para el módulo LALR(1)
- `tests/test_validation.py`: 11 tests para validación semántica
- `tests/test_integration.py`: 15 tests de pipeline end-to-end SLR y LALR
- `tests/test_cli.py`: 11 tests del CLI con todos los flags

### Changed
- `__main__.py`: flags `--method slr|lalr`, `--table`, `--no-validate`; imprime información del método y conteo de entradas
- `__init__.py`: exporta todos los símbolos de `lalr.py` y `validation.py`
- `README.md`: documentación final con tabla SLR vs LALR, referencia de CLI y formato del token stream

## [0.2.1] — 2026-05-17

### Added
- `docs/generate_report.py`: reproducible Word checkpoint report generator (Sprint 1)

## [0.2.0] — 2026-05-17

### Added
- Module 4 (`sets.py`): FIRST and FOLLOW fixed-point computation
- Module 5 (`automaton.py`): LR(0) canonical collection with closure/goto and frozenset deduplication
- Module 6 (`table.py`): SLR(1) ACTION/GOTO table with shift/reduce conflict detection
- Module 7 (`engine.py`): stack-based LR parser returning a concrete parse tree
- Module 8 (`viz.py`): Graphviz automaton renderer with `.dot` fallback
- Full unit test suite (7 files, >80 % line coverage)

## [0.1.1] — 2026-05-10

### Added
- Module 1 (`reader.py`): `.yalp` DSL tokenizer and parser with line/column error reporting
- Module 2 (`lexer_bridge.py`): YALex DFA adapter; defines `Token(tipo, lexema, linea, columna)` contract
- Module 3 (`grammar.py`): `Symbol`, `Production`, `Grammar` frozen dataclasses with `augment()` → S′

### Changed
- `grammar.py`: production renumbering in `augment()` now uses `enumerate` for contiguous IDs

## [0.1.0] — 2026-05-07

### Added
- Architecture document (`docs/arquitectura_yapar.drawio`, PDF export)
- Graphviz spike: minimal LR(0) automaton render proof-of-concept (`viz.py` skeleton)
- Repository scaffold: `src/yapar/`, `pyproject.toml`, `.gitignore`, `requirements.txt`
- GitHub Actions CI pipeline: ruff lint + pytest with 80 % coverage gate
- `.github/CODEOWNERS` and PR / issue templates
- Initial `README.md` and MIT license
