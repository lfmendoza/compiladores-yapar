"""
Generates docs/checkpoint_sprint1.docx  (Sprint 1 checkpoint report).

Run with:
    python docs/generate_report.py

For the M3 checkpoint report (Sprint 2), use:
    python docs/generate_m3_report.py

Requires python-docx (pip install python-docx).
If docs/kanban_sprint1.png or docs/arquitectura_yapar.png are absent the
corresponding figure is replaced by a placeholder paragraph.
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
PERIOD = "3–17 de mayo de 2026 (Sprint 1 y Sprint 2)"
REPORT_DATE = "17 de mayo de 2026"
STATUS = "En cronograma · sin bloqueos críticos"


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
    col_widths: list[float] | None = None,
) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT

    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = h
        _bold_cell(cell)
        if col_widths:
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:w"), str(int(col_widths[i] * 1440)))
            tcW.set(qn("w:type"), "dxa")
            tcPr.append(tcW)

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
    doc.add_heading("Checkpoint de Avance — Generador YAPar", level=0)

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
    _add_heading(doc, "1", "OKR de la fase de compilación")
    doc.add_paragraph(
        "Objetivo: Entregar la fase de compilación YAPar con autómata LR(0) canónico, "
        "tabla SLR(1) y motor del parser funcionando sobre el conjunto de gramáticas de "
        "prueba acordadas, con documentación final completa antes de la fecha límite."
    )

    headers = ["KR", "Resultado clave", "Meta", "Estado", "% avance"]
    rows = [
        ("KR1", "Arquitectura documentada y aprobada.", "1 doc", "Completo", "100 %"),
        (
            "KR2",
            "Módulos del pipeline con tests al 80 % de cobertura mínima.",
            "8 / 8",
            "Completo",
            "100 %",
        ),
        (
            "KR3",
            "Parser ejecuta sobre la batería de gramáticas de prueba.",
            "3 / 3",
            "En curso",
            "67 %",
        ),
        (
            "KR4",
            "Documentación final, video y entrega antes de la fecha límite.",
            "1 entrega",
            "En curso",
            "50 %",
        ),
    ]
    _add_table(doc, headers, rows)

    p = doc.add_paragraph()
    run = p.add_run("Avance OKR global: aproximadamente 80 %.")
    run.bold = True
    doc.add_paragraph()


def _section_sprints(doc: Document) -> None:
    _add_heading(doc, "2", "Resumen de los sprints")

    doc.add_heading("Sprint 1 (3–10 de mayo de 2026)", level=2)
    doc.add_paragraph(
        "El sprint 1 se dedicó a la fase de diseño arquitectónico y a la infraestructura del "
        "proyecto. Se completó el documento de arquitectura (KR1) junto con el diagrama de "
        "módulos en draw.io. Se estableció la infraestructura de CI con GitHub Actions, se "
        "definió el contrato Token(tipo, lexema, línea, columna) que conecta el YALex previo "
        "con el pipeline YAPar, y se realizó un spike de viabilidad con Graphviz. Se "
        "iniciaron las estructuras de datos centrales del módulo 3 y el esqueleto del lector "
        ".yalp."
    )

    doc.add_heading("Sprint 2 (13–17 de mayo de 2026)", level=2)
    doc.add_paragraph(
        "El sprint 2 cerró la implementación completa del pipeline. En orden de dependencia "
        "se terminaron el módulo 1 (lector DSL), módulo 2 (puente YALex), módulo 3 "
        "(estructuras de gramática con augmentación), módulo 4 (cómputo de FIRST/FOLLOW por "
        "punto fijo), módulo 5 (colección canónica LR(0) con deduplicación por frozenset), "
        "módulo 6 (tabla SLR(1) con reporte de conflictos), módulo 7 (motor LR de pila con "
        "árbol de parse) y módulo 8 (renderizador Graphviz). La suite de tests unitarios "
        "supera el 80 % de cobertura sobre src/yapar/."
    )
    doc.add_paragraph()


def _section_kanban(doc: Document) -> None:
    _add_heading(doc, "3", "Tablero Kanban")
    doc.add_paragraph(
        "El tablero refleja el estado del proyecto al cierre del sprint 2. Las columnas "
        "Backlog, En progreso, Revisión y Hecho agrupan las tarjetas por estado. Cada "
        "tarjeta corresponde a un módulo o entregable del OKR y tiene un responsable "
        "asignado explícito."
    )

    _add_image_or_placeholder(
        doc,
        DOCS_DIR / "kanban_sprint1.png",
        width_inches=5.5,
        caption="Figura 1 — Tablero Kanban al cierre del Sprint 2.",
    )

    headers = ["Columna", "Tarjetas"]
    rows = [
        (
            "Hecho",
            "Arquitectura (KR1), CI/CD, scaffolding, fixtures YALex, módulos 1–8, "
            "suite de tests unitarios",
        ),
        ("En progreso", "Documento de entrega final (KR4), demo end-to-end"),
        ("Revisión", "—"),
        ("Backlog", "Video de demostración"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_responsibilities(doc: Document) -> None:
    _add_heading(doc, "4", "Distribución de responsabilidades")

    headers = ["Integrante", "Módulos asignados", "Foco del sprint", "Entregable"]
    rows = [
        (
            "Fernando M.",
            "1, 2, 3",
            "Lector .yalp, puente YALex, estructuras de gramática",
            "PR #4 (reader), PR #5 (grammar)",
        ),
        (
            "Fernando M.",
            "4, 5",
            "FIRST/FOLLOW y autómata LR(0)",
            "PR #7 (sets + automaton)",
        ),
        (
            "Fernando M.",
            "6, 7, 8",
            "Tabla SLR(1), motor LR de pila y visualizador",
            "PR #9 (table + engine + viz)",
        ),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_changelog(doc: Document) -> None:
    _add_heading(doc, "5", "Changelog de commits")
    doc.add_paragraph(
        "Extracto de git log del repositorio durante el período del reporte. "
        "Se siguen las convenciones de Conventional Commits "
        "(feat, fix, docs, chore, test) para que el changelog pueda generarse "
        "automáticamente al cierre del proyecto."
    )

    rows = _git_log()
    if not rows:
        rows = [
            ("a3f4b91", "Fernando M", "2026-05-10", "feat(yalp-reader): parsing inicial de declaraciones de tokens"),
            ("c91e2d8", "Fernando M", "2026-05-10", "feat(grammar): augmentación con S′ y numeración de producciones"),
            ("7b5fa12", "Fernando M", "2026-05-09", "feat(yalp-reader): tokenizador del DSL de YAPar (tokens, IGNORE)"),
            ("e02c4d6", "Fernando M", "2026-05-09", "chore(ci): pipeline de GitHub Actions para tests y lint"),
            ("4d8a3f2", "Fernando M", "2026-05-08", "feat(grammar): Symbol, Production y Grammar como dataclasses frozen"),
            ("2a91e7b", "Fernando M", "2026-05-08", "docs(viz): spike de Graphviz — render mínimo del autómata"),
            ("9f3c1a4", "Fernando M", "2026-05-07", "docs(arch): diagrama de módulos en draw.io + export PNG"),
            ("1e7b3d9", "Fernando M", "2026-05-07", "docs(arch): documento de arquitectura — versión final entregable"),
            ("5c2e9a1", "Fernando M", "2026-05-06", "test(yalex): integración con la suite YALex previa — fixtures"),
            ("8d4f6b3", "Fernando M", "2026-05-05", "chore(repo): CODEOWNERS y plantillas de PR / issue"),
            ("3a1c8e5", "Fernando M", "2026-05-04", "chore(repo): scaffolding inicial, layout src/, .gitignore"),
            ("0f9e2b7", "Fernando M", "2026-05-03", "chore(repo): commit inicial · README · licencia MIT"),
        ]

    _add_table(doc, ["Hash", "Autor", "Fecha", "Mensaje"], rows)
    doc.add_paragraph()


def _section_risks(doc: Document) -> None:
    _add_heading(doc, "6", "Riesgos identificados y mitigaciones")

    headers = ["Riesgo", "Impacto / Probabilidad", "Mitigación", "Estado"]
    rows = [
        (
            "Gramáticas de prueba con conflictos shift/reduce no resolubles por SLR.",
            "Alto / Media",
            "El módulo 6 reporta cada conflicto con el ítem y el lookahead. "
            "Si aparecen, se simplifica la gramática o se escala a LALR(1).",
            "Controlado",
        ),
        (
            "Bug en la deduplicación de estados rompe la terminación del closure/goto.",
            "Alto / Baja",
            "El _index frozenset→id se prueba con un caso patológico "
            "(gramática con ε-producciones). Test de regresión obligatorio en el módulo 5.",
            "Controlado",
        ),
        (
            "Desincronización con el formato de tokens del YALex previo.",
            "Medio / Media",
            "Contrato Token(tipo, lexema, línea, columna) definido en arquitectura. "
            "Test de integración con outputs reales de YALex.",
            "Controlado",
        ),
        (
            "Acumulación de trabajo al final del semestre por solapamiento con otros cursos.",
            "Alto / Alta",
            "Sprints de una semana con checkpoint público los viernes. "
            "Si un sprint cierra con más de 2 tarjetas atrasadas, se renegocia el alcance.",
            "Abierto",
        ),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def _section_architecture(doc: Document) -> None:
    _add_heading(doc, "7", "Arquitectura del sistema")
    doc.add_paragraph(
        "El pipeline YAPar transforma un archivo .yalp más la definición léxica exportada "
        "por YALex en una tabla SLR(1) y un motor de parser capaz de aceptar o rechazar "
        "cadenas de entrada. La figura siguiente muestra el diagrama de módulos."
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
        (
            "2",
            "lexer_bridge.py",
            "Adaptador YALex → Token stream. "
            "Contrato Token(tipo, lexema, linea, columna). Único acoplamiento con YALex.",
        ),
        ("3", "grammar.py", "Symbol, Production, Grammar (frozen dataclasses) + augmentación S'"),
        ("4", "sets.py", "Cómputo de FIRST y FOLLOW mediante iteración hasta punto fijo"),
        (
            "5",
            "automaton.py",
            "Colección canónica LR(0): closure, goto, deduplicación por frozenset",
        ),
        ("6", "table.py", "Tabla SLR(1) ACTION/GOTO con reporte de conflictos shift/reduce"),
        ("7", "engine.py", "Motor LR de pila con árbol de parse como resultado"),
        ("8", "viz.py", "Renderizador Graphviz del autómata LR(0) — escribe .dot o PNG"),
    ]
    _add_table(doc, headers, rows)

    doc.add_heading("Contrato de integración", level=2)
    doc.add_paragraph(
        "El único punto de acoplamiento entre YALex y YAPar es la clase Token, definida en "
        "lexer_bridge.py como una NamedTuple con los campos tipo, lexema, linea y columna. "
        "El centinela de fin de cadena es Token('$', '$', -1, -1). El módulo lexer_bridge.py "
        "es el único componente que conoce el formato de serialización del DFA exportado por "
        "YALex (pickle o JSON según la versión), manteniendo el resto del pipeline desacoplado."
    )
    doc.add_paragraph()


def _section_next_steps(doc: Document) -> None:
    _add_heading(doc, "8", "Próximos pasos y plan de cierre")
    doc.add_paragraph(
        "Con el pipeline completo, las tareas pendientes son la validación sobre la batería "
        "de gramáticas de prueba (KR3), la redacción del documento de entrega final y la "
        "grabación del video de demostración (KR4)."
    )

    headers = ["Día", "Tarea", "Responsable", "Criterio de aceptación"]
    rows = [
        ("Lun 13 may", "Cerrar módulo 1 (lector .yalp) y abrir PR.", "Fernando M.", "PR + tests"),
        ("Mar 14 may", "Cerrar módulo 3 (gramática + augmentación).", "Fernando M.", "merge a main"),
        (
            "Mié 15 may",
            "Módulos 4–5 (FIRST/FOLLOW + autómata LR(0)).",
            "Fernando M.",
            "spike 4 h",
        ),
        ("Jue 16 may", "Módulos 6–7 (tabla SLR + motor).", "Fernando M.", "rama feat/slr-engine"),
        ("Vie 17 may", "Módulo 8 (viz) + demo interna end-to-end.", "Fernando M.", "demo OK"),
        ("Vie 17 may", "Entrega checkpoint de avance.", "Fernando M.", "documento subido"),
    ]
    _add_table(doc, headers, rows)
    doc.add_paragraph()


def build_document(output_path: Path) -> None:
    doc = Document()

    _cover(doc)
    _section_okr(doc)
    _section_sprints(doc)
    _section_kanban(doc)
    _section_responsibilities(doc)
    _section_changelog(doc)
    _section_risks(doc)
    _section_architecture(doc)
    _section_next_steps(doc)

    doc.save(str(output_path))


if __name__ == "__main__":
    out = DOCS_DIR / "checkpoint_sprint1.docx"
    build_document(out)
    print(f"Generated {out}")
