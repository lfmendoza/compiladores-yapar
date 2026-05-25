# Checkpoint de Avance M3 — Generador de Analizadores Sintácticos

**Universidad del Valle de Guatemala · Diseño y Construcción de Compiladores**
**Equipo:** Fernando Mendoza
**Período:** 3–24 de mayo de 2026 (Sprint 1 y Sprint 2)
**Repositorio:** https://github.com/lfmendoza/compiladores-yapar
**Estado general:** En cronograma — pipeline SLR(1) completo, LALR(1) iniciado

---

## 1. Descripción del proyecto

YAPar es un generador de analizadores sintácticos escrito en Python 3.12 que lee una gramática en formato `.yalp`, construye el autómata LR(0) canónico, calcula los conjuntos FIRST y FOLLOW, genera la tabla SLR(1) ACTION/GOTO y ejecuta un motor de parseo de pila sobre una cadena de tokens de entrada. El proyecto es la fase de compilación sintáctica que se integra con el YALex (analizador léxico) del proyecto anterior a través de un contrato de token bien definido.

---

## 2. Objetivo general (OKR)

Entregar la fase de compilación YAPar con autómata LR(0)/LALR(1) canónico, tabla SLR(1)/LALR(1) y motor del parser funcionando sobre el conjunto de gramáticas de prueba acordadas, con documentación final completa antes de la fecha límite.

| KR | Resultado clave | Meta | Estado | % |
|----|-----------------|------|--------|---|
| KR1 | Arquitectura documentada y aprobada | 1 doc | Completo | 100% |
| KR2 | Módulos del pipeline con tests ≥ 80% cobertura | 8/8 + LALR | En progreso | 89% |
| KR3 | Parser ejecuta sobre batería de gramáticas de prueba | 3/3 SLR | En progreso | 67% |
| KR4 | Documentación final, video y entrega antes de fecha límite | 1 entrega | En curso | 40% |

**Avance OKR global: ~74%. Pipeline SLR(1) completamente funcional. LALR(1) iniciado.**

---

## 3. Estado actual del pipeline

### 3.1 Módulos implementados

| Módulo | Archivo | Responsabilidad | Estado |
|--------|---------|-----------------|--------|
| 1 | `src/yapar/reader.py` | Parser del DSL `.yalp`, comments, TOKENS/IGNORE, `%%` | Completado |
| 2 | `src/yapar/lexer_bridge.py` | Adaptador YALex → `Token(tipo, lexema, linea, columna)` | Completado |
| 3 | `src/yapar/grammar.py` | `Symbol`, `Production`, `Grammar` frozen dataclasses + `augment()` | Completado |
| 4 | `src/yapar/sets.py` | FIRST y FOLLOW por iteración de punto fijo | Completado |
| 5 | `src/yapar/automaton.py` | Colección canónica LR(0): `closure`, `goto`, deduplicación frozenset | Completado |
| 6 | `src/yapar/table.py` | Tabla SLR(1) ACTION/GOTO, `ConflictError` en shift/reduce | Completado |
| 7 | `src/yapar/engine.py` | Motor LR de pila, árbol de parse `ParseNode` | Completado |
| 8 | `src/yapar/viz.py` | Renderizador Graphviz del autómata LR(0), fallback a `.dot` | Completado |
| CLI | `src/yapar/__main__.py` | `python -m yapar grammar.yalp [input.tsv] [--render PATH]` | Completado |
| LALR | `src/yapar/lalr.py` | `LR1Item`, `closure_lr1`, `goto_lr1`, `build_lr1_automaton`, `merge_to_lalr`, `build_lalr_table` | En progreso |

### 3.2 Infraestructura

| Componente | Estado |
|------------|--------|
| 90+ tests unitarios, 90% cobertura línea | Completado |
| CI GitHub Actions: ruff lint + pytest 80% gate | Completado |
| Fixtures de gramáticas de prueba (`tests/fixtures/`) | Completado (3) |
| Gramáticas de demo (`examples/`) | Completado (3) |
| Validación semántica de gramática | Pendiente |

---

## 4. Qué ya funciona — demo reproducible

```bash
# Instalar
pip install -e . -r requirements.txt

# Parsear gramática aritmética — genera tabla SLR(1) sin conflictos
python -m yapar examples/arithmetic.yalp

# Detectar conflicto shift/reduce en gramática if-else
python -m yapar examples/conflict_demo.yalp

# Renderizar autómata LR(0) como Graphviz
python -m yapar examples/arithmetic.yalp --render automaton.dot

# Ejecutar suite de tests con cobertura
pytest --cov=src/yapar --cov-report=term-missing
```

El pipeline completo `.yalp → Grammar → FIRST/FOLLOW → LR(0) → SLR(1) table → ParseNode` funciona sobre las tres gramáticas de ejemplo. Los conflictos shift/reduce se detectan y reportan con estado, símbolo y las dos acciones en conflicto.

---

## 5. Qué está en progreso

- **`src/yapar/lalr.py`**: `LR1Item`, `closure_lr1`, `goto_lr1`, `build_lr1_automaton` y `merge_to_lalr` implementados. `build_lalr_table` completo. Tests cubriendo LR1Item, closure y merge.
- **Integración CLI**: flag `--method lalr` para seleccionar entre SLR y LALR está planificado para Sprint 3.
- **Tests adicionales**: suite LALR con gramáticas de libros de texto (aritmética completa con precedencia).

---

## 6. Qué falta para la entrega final

1. Integrar `build_lalr_table` en el CLI con `--method lalr`.
2. Validación semántica: detectar símbolos inalcanzables y no definidos en producciones.
3. Tests de `lalr.py` comparando tablas LALR contra valores esperados de libros.
4. Documentación final con output de tabla impresa y ejemplo de derivación.
5. Demo end-to-end: gramática aritmética → tabla LALR(1) → parsing de `1 + 2 * 3`.

---

## 7. Arquitectura interna

```
.yalp grammar
    │
    ▼
reader.py ──► grammar.py (augment) ──► sets.py (FIRST/FOLLOW)
                                               │
                              ┌────────────────┴──────────────────┐
                              ▼                                    ▼
                       automaton.py (LR0)               lalr.py (LR1 → LALR)
                              │                                    │
                              └──────────────┬────────────────────┘
                                             ▼
                                        table.py (SLR/LALR ACTION/GOTO)
                                             │
                         .yalex DFA ──► lexer_bridge.py ──► engine.py ──► ParseNode
```

**Contrato de integración con YALex:** `Token(tipo, lexema, linea, columna)`. El EOF sentinel es `Token("$", "$", -1, -1)`. El módulo `lexer_bridge.py` es el único componente que conoce el formato del DFA exportado por YALex.

---

## 8. Plan técnico LALR(1)

### Por qué ruta incremental y no saltar directamente a LALR

El proyecto ya tiene LR(0) completo en `automaton.py`. La extensión a LALR(1) reutiliza toda esa infraestructura sin modificarla:

- `Item(production_id, dot)` se extiende con un campo `lookahead: Symbol` → `LR1Item`.
- `closure_lr1` es análogo a `closure` pero al expandir un no-terminal calcula `FIRST(β · a)` para determinar los lookaheads de los nuevos ítems.
- `merge_to_lalr` agrupa estados LR(1) por su core LR(0) y une los frozensets de lookaheads.
- `build_lalr_table` es idéntico a `build_slr_table` pero usa `item.lookahead` en lugar de `FOLLOW(head)`.

### Diferencia clave SLR vs LALR en la tabla

- **SLR:** `Reduce(p)` se coloca en ACTION para todo `a ∈ FOLLOW(head(p))` — criterio global, puede generar falsos conflictos.
- **LALR:** `Reduce(p)` solo para `a ∈ lookahead(item)` — criterio por item, lookaheads más precisos, acepta más gramáticas sin conflictos.

### Los 5 pasos de implementación

| Paso | Componente | Dependencia |
|------|-----------|------------|
| A | `LR1Item` + `closure_lr1` | `first_of_sequence` de `sets.py` |
| B | `goto_lr1` + `build_lr1_automaton` | Paso A |
| C | `core()` + `merge_to_lalr` | Paso B |
| D | `build_lalr_table` | Paso C + `table.py` |
| E | CLI `--method lalr` | Paso D + `__main__.py` |

---

## 9. Roadmap hacia la implementación final

| Sprint | Semana | Objetivo | Criterio de aceptación |
|--------|--------|----------|----------------------|
| Sprint 2 (actual) | 17–24 may | Pipeline SLR(1) completo + inicio LALR | 90 tests pasando, `lalr.py` Pasos A–D |
| Sprint 3 | 25–31 may | LALR integrado en CLI + tests de libro | `--method lalr` funcional, aritmética sin conflicto |
| Sprint 4 | 1–7 jun | Validación semántica + ejemplos adicionales | Errores claros para gramáticas inválidas |
| Sprint 5 | 8–14 jun | Documentación final + demo + video | KR4 completo |

---

## 10. Riesgos y mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación | Estado |
|--------|---------|-------------|------------|--------|
| LALR no termina antes de la entrega final | Medio | Baja | SLR(1) ya funciona como entrega demostrable; LALR es extensión | Controlado |
| Conflictos LALR post-fusión difíciles de depurar | Alto | Baja | Probar primero con gramáticas LALR conocidas de libros | Controlado |
| Validación semántica no implementada | Bajo | Alta | Para M3 no es bloqueante; gramáticas de test bien formadas | Abierto |
| Evidencia de trabajo grupal insuficiente | Alto | Media | Commits por módulo en GitHub con Conventional Commits | Controlado |

---

## 11. Distribución de trabajo

| Módulo / Tarea | Responsable | Sprint | Entregable |
|---------------|-------------|--------|-----------|
| Módulos 1–3 (reader, bridge, grammar) | Fernando M. | Sprint 1–2 | Implementados |
| Módulos 4–5 (sets, automaton) | Fernando M. | Sprint 2 | Implementados |
| Módulos 6–8 (table, engine, viz) + CLI | Fernando M. | Sprint 2 | Implementados |
| CI/CD, tests, cobertura 90% | Fernando M. | Sprint 2 | Implementados |
| Documentación M3, ejemplos | Fernando M. | Sprint 2 | Este reporte |
| `lalr.py` Pasos A–D | Fernando M. | Sprint 2–3 | En progreso |
| CLI `--method lalr`, docs finales | Fernando M. | Sprint 3–5 | Pendiente |

---

## 12. Preguntas para la clase

1. ¿Se espera que la entrega final soporte LALR(1) además de SLR(1), o SLR(1) es suficiente?
2. ¿Las gramáticas de prueba del catedrático incluyen casos que SLR no puede manejar pero LALR sí?
3. ¿Se espera visualización de los estados LALR(1) además del autómata LR(0)?
4. ¿El input de tokens debe venir obligatoriamente de YALex, o puede ser un archivo TSV manual para los tests?

---

*Generado el 24 de mayo de 2026 — Repositorio: https://github.com/lfmendoza/compiladores-yapar*
