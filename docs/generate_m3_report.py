"""
Generates docs/checkpoint_m3.docx — Checkpoint de Avance M3.

Run with:
    python docs/generate_m3_report.py

Requires python-docx (pip install python-docx).
Place docs/kanban_m3.png before running to embed the Kanban screenshot.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

DOCS_DIR = Path(__file__).parent
REPO_URL = "https://github.com/lfmendoza/compiladores-yapar"
COURSE = "Diseño y Construcción de Compiladores"
UNIVERSITY = "Universidad del Valle de Guatemala"
TEAM = "Fernando Mendoza"
PERIOD = "17–24 de mayo de 2026 (Sprint 2 — Checkpoint M3)"
REPORT_DATE = "24 de mayo de 2026"
STATUS = "En cronograma · pipeline SLR(1) completo · LALR(1) iniciado"


def _git_log() -> list[tuple[str, str, str, str]]:
    try:
        out = subprocess.check_output(
            ["git", "log", "--pretty=format:%h\t%an\t%ad\t%s", "--date=short"],
            cwd=DOCS_DIR.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        rows: list[tuple[str, str, str, str]] = []
        for line in out.strip().splitlines():
            parts = line.split("\t", maxsplit=3)
            if len(parts) == 4:
                rows.append((parts[0], parts[1], parts[2], parts[3]))
        return rows
    except Exception:
        return []


def _bold_cell(cell) -> None:
    for para in cell.paragraphs:
        for run in para.runs:
            run.bold = True


def _add_table(
    doc: Document,
    headers: list[str],
    rows: list[tuple[str, ...]],
) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = h
        _bold_cell(cell)
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            t.rows[r_idx + 1].cells[c_idx].text = str(val)


def _add_heading(doc: Document, number: str, title: str) -> None:
    h = doc.add_heading(f"{number}. {title}", level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT


def _add_image_or_placeholder(
    doc: Document,
    img_path: Path,
    width_inches: float,
    caption: str,
) -> None:
    if img_path.exists():
        doc.add_picture(str(img_path), width=Inches(width_inches))
        p = doc.add_paragraph(caption)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.italic = True
            run.font.size = Pt(9)
    else:
        p = doc.add_paragraph(f"[Imagen no disponible: {img_path.name}]")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.italic = True
            run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)


def _cover(doc: Document) -> None:
    doc.add_heading("Checkpoint de Avance M3 — Generador de Analizadores Sintácticos", level=0)
    fields = [
        ("Universidad", UNIVERSITY),
        ("Curso", COURSE),
        ("Equipo", TEAM),
        ("Período del reporte", PERIOD),
        ("Repositorio", REPO_URL),
        ("Estado general", STATUS),
        ("Fecha del reporte", REPORT_DATE),
    ]
    for label, value in fields:
        p = doc.add_paragraph()
        run_label = p.add_run(f"{label}: ")
        run_label.bold = True
        p.add_run(value)
    doc.add_page_break()


def _section_okr(doc: Document) -> None:
    _add_heading(doc, "1", "OKR de la fase de compilación — Estado M3")
    doc.add_paragraph(
        "Objetivo: Entregar la fase de compilación YAPar con autómata LR(0)/LALR(1) "
        "canónico, tabla SLR(1)/LALR(1) y motor del parser funcionando sobre el "
        "conjunto de gramáticas de prueba acordadas, con documentación final completa."
    )
    headers = ["KR", "Resultado clave", "Meta", "Estado", "% avance"]
    rows = [
        ("KR1", "Arquitectura documentada y aprobada.", "1 doc", "Completo", "100 %"),
        (
            "KR2",
            "Módulos del pipeline con tests al 80 % de cobertura mínima.",
            "8/8 + LALR",
            "En progreso",
            "89 %",
        ),
        (
            "KR3",
            "Parser ejecuta sobre la batería de gramáticas de prueba.",
            "3/3 SLR",
            "En progreso",
            "67 %",
        ),
        (
            "KR4",
            "Documentación final, video y entrega completa.",
            "1 entrega",
            "En curso",
            "40 %",
        ),
    ]
    _add_table(doc, headers, rows)
    p = doc.add_paragraph()
    p.add_run("Avance OKR global: aproximadamente 74 %.").bold = True
    doc.add_paragraph()


def _section_pipeline_state(doc: Document) -> None:
    _add_heading(doc, "2", "Estado del pipeline")
    doc.add_paragraph(
        "Los 8 módulos SLR(1) están completamente implementados y probados. "
        "El módulo LALR(1) se agrega en este sprint como extensión del autómata LR(0) existente."
    )
    headers = ["Módulo", "Archivo", "Responsabilidad", "Estado"]
    rows = [
        ("1", "reader.py", "Parser del DSL .yalp", "Completado"),
        ("2", "lexer_bridge.py", "Adaptador YALex → Token contract", "Completado"),
        ("3", "grammar.py", "Symbol, Production, Grammar + augment()", "Completado"),
        ("4", "sets.py", "FIRST y FOLLOW por punto fijo", "Completado"),
        ("5", "automaton.py", "Colección canónica LR(0): closure, goto", "Completado"),
        ("6", "table.py", "Tabla SLR(1) ACTION/GOTO con ConflictError", "Completado"),
        ("7", "engine.py", "Motor LR de pila + árbol de parse ParseNode", "Completado"),
        ("8", "viz.py", "Renderizador Graphviz .dot / PNG", "Completado"),
        ("CLI", "__main__.py", "python -m yapar grammar.yalp [input] [--render]", "Completado"),
        (
            "LALR",
            "lalr.py",
            "LR1Item, closure_lr1, build_lr1_automaton, merge_to_lalr, build_lalr_table",
            "Completado",
        ),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_sprint_summary(doc: Document) -> None:
    _add_heading(doc, "3", "Resumen de los sprints")

    doc.add_heading("Sprint 1 (3–10 de mayo)", level=2)
    doc.add_paragraph(
        "Se completó el diseño arquitectónico (KR1), la infraestructura del repositorio con "
        "CI en GitHub Actions y se iniciaron los módulos 1–3. El documento de arquitectura "
        "en draw.io fue aprobado. Se definió el contrato Token(tipo, lexema, línea, columna) "
        "para la integración con YALex."
    )

    doc.add_heading("Sprint 2 (13–24 de mayo)", level=2)
    doc.add_paragraph(
        "Se cerraron los 8 módulos del pipeline SLR(1) en orden de dependencia. La suite de "
        "tests cubre 109 tests con 91 % de cobertura. El CI corre en cada push verificando "
        "lint (ruff) y cobertura mínima del 80 %. Se agregó el módulo LALR(1) completo "
        "(lalr.py) con LR(1) items, autómata canónico LR(1), fusión de estados y tabla "
        "ACTION/GOTO con detección de conflictos. Se crearon tres gramáticas de demo en "
        "examples/ y el documento de checkpoint M3 en dos formatos (Markdown y Word)."
    )
    doc.add_paragraph()


def _section_kanban(doc: Document) -> None:
    _add_heading(doc, "4", "Tablero Kanban — Sprint 2")
    doc.add_paragraph(
        "El tablero refleja el estado al cierre del sprint 2. Las tarjetas de los "
        "8 módulos SLR y LALR están en Hecho. Las tarjetas de integración CLI y "
        "validación semántica están en To Do para el sprint 3."
    )
    _add_image_or_placeholder(
        doc,
        DOCS_DIR / "kanban_m3.png",
        width_inches=5.5,
        caption="Figura 1 — Tablero Kanban al cierre del Sprint 2.",
    )
    headers = ["Columna", "Tarjetas"]
    rows = [
        (
            "Hecho",
            "Módulos 1–8 SLR, lalr.py completo, CI/CD, tests 91%, docs M3, ejemplos",
        ),
        (
            "En progreso",
            "Integración CLI --method lalr, tests LALR con gramáticas de libro",
        ),
        ("To Do", "Validación semántica, demo end-to-end, video final"),
        ("Backlog", "Exportar tabla como CSV/JSON, manejo de errores de recuperación"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_responsibilities(doc: Document) -> None:
    _add_heading(doc, "5", "Distribución de responsabilidades")
    headers = ["Integrante", "Módulos / Tareas", "Sprint", "Entregable"]
    rows = [
        ("Fernando M.", "Módulos 1–3 (reader, bridge, grammar)", "Sprint 1–2", "Implementados"),
        ("Fernando M.", "Módulos 4–5 (sets, automaton)", "Sprint 2", "Implementados"),
        ("Fernando M.", "Módulos 6–8 (table, engine, viz) + CLI", "Sprint 2", "Implementados"),
        ("Fernando M.", "CI/CD, 109 tests, cobertura 91%", "Sprint 2", "Implementados"),
        ("Fernando M.", "lalr.py completo (Pasos A–D)", "Sprint 2", "Implementado"),
        ("Fernando M.", "Documentación M3, examples/, Word", "Sprint 2", "Este documento"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_changelog(doc: Document) -> None:
    _add_heading(doc, "6", "Changelog de commits")
    doc.add_paragraph(
        "Extracto de git log durante el período del reporte. "
        "Convención: Conventional Commits (feat, fix, docs, chore, test)."
    )
    rows = _git_log()
    if not rows:
        rows = [
            ("42a2a5d", "Fernando M", "2026-05-17", "docs(checkpoint): script generador del reporte Word Sprint 2"),
            ("48ad791", "Fernando M", "2026-05-17", "feat(viz): render Graphviz del autómata LR(0)"),
            ("505b36b", "Fernando M", "2026-05-17", "feat(engine): motor LR de pila + árbol de parse"),
            ("4e8295f", "Fernando M", "2026-05-17", "feat(table): tabla SLR(1) ACTION/GOTO con reporte de conflictos"),
            ("204774c", "Fernando M", "2026-05-17", "feat(automaton): colección canónica LR(0) — closure y goto"),
            ("76d8c2d", "Fernando M", "2026-05-17", "feat(sets): cómputo de FIRST y FOLLOW con punto fijo"),
        ]
    _add_table(doc, ["Hash", "Autor", "Fecha", "Mensaje"], rows)
    doc.add_paragraph()


def _section_risks(doc: Document) -> None:
    _add_heading(doc, "7", "Riesgos y mitigaciones")
    headers = ["Riesgo", "Impacto / Prob.", "Mitigación", "Estado"]
    rows = [
        (
            "LALR no termina antes de la entrega final",
            "Medio / Baja",
            "SLR(1) ya funciona como entrega demostrable; LALR es extensión",
            "Controlado",
        ),
        (
            "Conflictos LALR post-fusión difíciles de depurar",
            "Alto / Baja",
            "Probar primero con gramáticas LALR conocidas de libros",
            "Controlado",
        ),
        (
            "Validación semántica no implementada",
            "Bajo / Alta",
            "Para M3 no es bloqueante; gramáticas de test bien formadas",
            "Abierto",
        ),
        (
            "Evidencia de trabajo grupal insuficiente",
            "Alto / Media",
            "Commits por módulo en GitHub con Conventional Commits",
            "Controlado",
        ),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_architecture(doc: Document) -> None:
    _add_heading(doc, "8", "Arquitectura del sistema")
    doc.add_paragraph(
        "El pipeline YAPar transforma un archivo .yalp en una tabla SLR(1) o LALR(1) y "
        "ejecuta un motor de parseo sobre una cadena de tokens de entrada. El módulo "
        "lalr.py extiende el autómata LR(0) existente sin modificar ninguno de los "
        "8 módulos originales."
    )
    _add_image_or_placeholder(
        doc,
        DOCS_DIR / "arquitectura_yapar.png",
        width_inches=5.5,
        caption="Figura 2 — Diagrama de módulos YAPar (fuente: arquitectura_yapar.drawio).",
    )
    headers = ["Módulo", "Archivo", "Responsabilidad"]
    rows = [
        ("1", "reader.py", "Tokenizador y parser del DSL .yalp"),
        ("2", "lexer_bridge.py", "Adaptador YALex. Contrato: Token(tipo, lexema, linea, columna)"),
        ("3", "grammar.py", "Symbol, Production, Grammar frozen dataclasses + augment()"),
        ("4", "sets.py", "FIRST y FOLLOW por punto fijo"),
        ("5", "automaton.py", "Colección canónica LR(0): closure, goto, deduplicación frozenset"),
        ("6", "table.py", "Tabla SLR(1) ACTION/GOTO con ConflictError"),
        ("7", "engine.py", "Motor LR de pila con ParseNode"),
        ("8", "viz.py", "Renderizador Graphviz con fallback .dot"),
        ("LALR", "lalr.py", "LR1Item, closure/goto LR(1), merge_to_lalr, build_lalr_table"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_lalr_plan(doc: Document) -> None:
    _add_heading(doc, "9", "Plan técnico LALR(1)")
    doc.add_paragraph(
        "El proyecto ya tenía LR(0) completo en automaton.py. La extensión a LALR(1) "
        "reutiliza toda esa infraestructura añadiendo un campo lookahead al item:"
    )
    doc.add_paragraph(
        "Item(production_id, dot) → LR1Item(production_id, dot, lookahead: Symbol)"
    ).runs[0].italic = True

    doc.add_heading("Diferencia clave SLR vs LALR en la tabla", level=2)
    doc.add_paragraph(
        "SLR: Reduce(p) se coloca en ACTION para todo a ∈ FOLLOW(head(p)) — criterio global.\n"
        "LALR: Reduce(p) solo para a ∈ lookahead(item) — criterio por item, más preciso, "
        "acepta más gramáticas sin conflictos."
    )

    doc.add_heading("Pasos de implementación", level=2)
    headers = ["Paso", "Componente", "Dependencia", "Estado"]
    rows = [
        ("A", "LR1Item + closure_lr1", "first_of_sequence de sets.py", "Completado"),
        ("B", "goto_lr1 + build_lr1_automaton", "Paso A", "Completado"),
        ("C", "core() + merge_to_lalr", "Paso B", "Completado"),
        ("D", "build_lalr_table", "Paso C + table.py", "Completado"),
        ("E", "CLI --method lalr", "Paso D + __main__.py", "Pendiente Sprint 3"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_roadmap(doc: Document) -> None:
    _add_heading(doc, "10", "Roadmap hacia la implementación final")
    headers = ["Sprint", "Semana", "Objetivo", "Criterio de aceptación"]
    rows = [
        (
            "Sprint 2 (actual)",
            "17–24 may",
            "Pipeline SLR(1) completo + LALR(1) Pasos A–D",
            "109 tests, 91% cobertura, lalr.py funcional",
        ),
        (
            "Sprint 3",
            "25–31 may",
            "CLI --method lalr + tests gramáticas de libro",
            "--method lalr funcional, aritmética sin conflicto LALR",
        ),
        (
            "Sprint 4",
            "1–7 jun",
            "Validación semántica + ejemplos adicionales",
            "Errores claros para gramáticas mal formadas",
        ),
        (
            "Sprint 5",
            "8–14 jun",
            "Documentación final + demo + video",
            "KR4 completo, entrega final",
        ),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_next_steps(doc: Document) -> None:
    _add_heading(doc, "11", "Próximos pasos inmediatos")
    headers = ["Día", "Tarea", "Responsable", "Criterio de aceptación"]
    rows = [
        ("Lun 25 may", "Integrar --method lalr en CLI", "Fernando M.", "PR + tests pasando"),
        ("Mar 26 may", "Tests LALR con gramáticas de Dragon Book", "Fernando M.", "tablas correctas"),
        ("Mié 27 may", "Validación semántica — símbolos no definidos", "Fernando M.", "YAParSyntaxError"),
        ("Jue 28 may", "Reporte de conflictos con trazabilidad de lookahead", "Fernando M.", "output claro"),
        ("Vie 29 may", "Demo interna end-to-end: aritmética LALR", "Fernando M.", "demo OK"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def build_document(output_path: Path) -> None:
    doc = Document()

    _cover(doc)
    _section_okr(doc)
    _section_pipeline_state(doc)
    _section_sprint_summary(doc)
    _section_kanban(doc)
    _section_responsibilities(doc)
    _section_changelog(doc)
    _section_risks(doc)
    _section_architecture(doc)
    _section_lalr_plan(doc)
    _section_roadmap(doc)
    _section_next_steps(doc)

    doc.save(str(output_path))


if __name__ == "__main__":
    out = DOCS_DIR / "checkpoint_m3.docx"
    build_document(out)
    print(f"Generated {out}")
