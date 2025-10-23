# MySQL Workbench Python script (Plugin/Module)
# Script to Generate an HTML Schema Report from Mysql Model
# Author: Tito Sanchez
# Update by: Fernando Gil
# Update2 by: Mgil10
# Written in MySQL Workbench 8.0.25

from wb import *
import grt
from mforms import Utilities, FileChooser
import mforms
import html


def sanitize(text):
    """
    Convierte secuencias literales '\\n' en saltos de línea reales,
    escapa HTML y convierte saltos de línea en <br>.
    También normaliza tabs y dobles espacios para mantener formato.
    """
    if text is None:
        return ""
    # Asegurar que trabajamos con str
    s = str(text)

    # Primero: convertir secuencias literales como "\\r\\n" o "\\n" en saltos reales
    # (esto cubre casos donde el texto contiene la secuencia de caracteres \n en lugar de un newline)
    s = s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")

    # Escapar caracteres HTML reservados
    s = html.escape(s)

    # Convertir saltos reales en <br>
    s = s.replace("\n", "<br>")

    # Convertir tabs en espacios visuales y preservar dobles espacios
    s = s.replace("\t", "&emsp;")
    # Repetir reemplazo de dos espacios para convertirlos en &nbsp; pares (iterativo para múltiples espacios)
    while "  " in s:
        s = s.replace("  ", "&nbsp;&nbsp;")

    return s

ModuleInfo = DefineModule(
    name="DBReportHTML",
    author="Tito Sanchez & Mgil10",
    version="1.2",
    description="Database Schema Report in HTML format (with Bootstrap)",
)

@ModuleInfo.plugin(
    "tmsanchezplugin.dbReportHtml",
    caption="DB Report in HTML",
    description="Database Schema Report in HTML format (with Bootstrap)",
    input=[wbinputs.currentCatalog()],
    pluginMenu="Catalog",
)
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)
def htmlDataDictionary(catalog):
    filechooser = FileChooser(mforms.SaveFile)
    filechooser.set_extensions("HTML File (*.html)|*.html", "html")
    if not filechooser.run_modal():
        return 1
    htmlOut = filechooser.get_path()
    if not htmlOut:
        return 1

    # Si no hay esquemas, abortar
    if not catalog.schemata:
        Utilities.show_message(
            "Error",
            "No se encontró ningún esquema en el catálogo seleccionado.",
            "OK",
            "",
            "",
        )
        return 1

    schema = catalog.schemata[0]
    html_parts = []

    # HTML HEADER
    html_parts.append(
        f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(schema.name)} - Schema Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body {{ background-color: #f8f9fa; }}
        .table th {{ background-color: #e9ecef; }}
        .relation-badge {{ font-size: 0.85rem; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
<nav class="navbar navbar-dark bg-primary mb-4">
  <div class="container-fluid">
    <span class="navbar-brand mb-0 h1">Schema Report: {html.escape(schema.name)}</span>
  </div>
</nav>

<div class="container mb-5">
  <h2>Índice</h2>
  <ul class="list-group">
    <li class="list-group-item"><a href="#tables">Tablas</a></li>
    <li class="list-group-item"><a href="#views">Vistas</a></li>
    <li class="list-group-item"><a href="#relations">Relaciones</a></li>
  </ul>
  <hr>
"""
    )

    # TABLES SECTION
    html_parts.append('<h2 id="tables" class="mt-5 mb-3">Tablas</h2>')
    for table in schema.tables:
        table_name_escaped = html.escape(table.name) if table.name else "(sin nombre)"
        html_parts.append(
            f"""
        <div class="card mb-4 shadow-sm">
          <div class="card-header bg-secondary text-white">
            <h5 id="{table_name_escaped}" class="mb-0">{table_name_escaped}</h5>
          </div>
          <div class="card-body">
            <p><strong>Comentarios:</strong> {sanitize(table.comment) or "Sin comentarios"}</p>
            <div class="table-responsive">
              <table class="table table-bordered table-striped table-sm align-middle">
                <thead><tr>
                  <th>Nombre</th><th>Tipo de dato</th><th>Not Null</th><th>PK</th><th>FK</th><th>Default</th><th>Comentario</th>
                </tr></thead><tbody>
        """
        )
        for column in table.columns:
            col_name = html.escape(column.name) if column.name else ""
            formatted_type = (
                html.escape(column.formattedType)
                if getattr(column, "formattedType", None)
                else html.escape(getattr(column, "simpleType", "") or "")
            )
            pk = "✅" if table.isPrimaryKeyColumn(column) else ""
            fk = "🔗" if table.isForeignKeyColumn(column) else ""
            nn = "✔️" if getattr(column, "isNotNull", False) else ""
            default_val = (
                sanitize(column.defaultValue)
                if getattr(column, "defaultValue", None)
                else ""
            )
            comment_val = (
                sanitize(column.comment) if getattr(column, "comment", None) else ""
            )
            html_parts.append(
                f"<tr><td>{col_name}</td><td>{formatted_type}</td><td>{nn}</td><td>{pk}</td><td>{fk}</td><td>{default_val}</td><td>{comment_val}</td></tr>"
            )
        html_parts.append("</tbody></table></div>")

        # Foreign keys
        if getattr(table, "foreignKeys", None):
            html_parts.append("<p><strong>Claves foráneas:</strong></p><ul>")
            for fk in table.foreignKeys:
                ref_table = (
                    fk.referencedTable.name
                    if getattr(fk, "referencedTable", None)
                    and fk.referencedTable
                    and getattr(fk.referencedTable, "name", None)
                    else "?"
                )
                fk_name = fk.name if getattr(fk, "name", None) else "(sin nombre)"
                html_parts.append(
                    f"<li>{sanitize(fk_name) or '(sin nombre)'} → <span class='badge bg-info text-dark relation-badge'>{sanitize(ref_table)}</span></li>"
                )
            html_parts.append("</ul>")
        else:
            html_parts.append("<p><em>Sin claves foráneas.</em></p>")

        html_parts.append(
            f'<a href="#tables" class="btn btn-outline-primary mt-3">Volver al listado</a></div></div>'
        )

    # VIEWS SECTION
    html_parts.append('<h2 id="views" class="mt-5 mb-3">Vistas</h2>')
    if getattr(schema, "views", None):
        if schema.views:
            for view in schema.views:
                view_name = (
                    html.escape(view.name)
                    if getattr(view, "name", None)
                    else "(sin nombre)"
                )
                # Algunos modelos usan sqlDefinition, otros usan definition; intentamos ambas
                sql_def = (
                    getattr(view, "sqlDefinition", None)
                    or getattr(view, "definition", None)
                    or getattr(view, "body", None)
                    or ""
                )
                html_parts.append(
                    f"""
            <div class="card mb-3">
              <div class="card-header bg-dark text-white">
                <h5 id="view_{view_name}" class="mb-0">{view_name}</h5>
              </div>
              <div class="card-body">
                <p><strong>Comentarios:</strong> {sanitize(getattr(view, 'comment', None)) or "Sin comentarios"}</p>
                <p><strong>Definición SQL:</strong></p>
                <pre class="bg-light p-2 border">{sanitize(sql_def) or "(No disponible)"}</pre>
                <a href="#views" class="btn btn-outline-secondary">Volver al listado</a>
              </div>
            </div>
            """
                )
        else:
            html_parts.append("<p>No hay vistas definidas.</p>")
    else:
        html_parts.append("<p>No hay vistas definidas.</p>")

    # RELATIONS SECTION
    html_parts.append(
        '<h2 id="relations" class="mt-5 mb-3">Relaciones entre tablas</h2>'
    )
    relations = []
    for table in schema.tables:
        for fk in getattr(table, "foreignKeys", []) or []:
            if getattr(fk, "referencedTable", None) and getattr(
                fk.referencedTable, "name", None
            ):
                relations.append(
                    (table.name or "(sin nombre)", fk.referencedTable.name, fk.name)
                )
    if relations:
        html_parts.append(
            '<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>Tabla origen</th><th>Tabla destino</th><th>Clave foránea</th></tr></thead><tbody>'
        )
        for src, dest, fkname in relations:
            html_parts.append(
                f"<tr><td>{sanitize(src)}</td><td>{sanitize(dest)}</td><td>{sanitize(fkname) or '(sin nombre)'}</td></tr>"
            )
        html_parts.append("</tbody></table></div>")
    else:
        html_parts.append("<p>No existen relaciones entre tablas.</p>")

    # FOOTER
    html_parts.append(
        """
  <footer class="mt-5 text-center text-muted">
    <hr>
    <p>Generado automáticamente por DBReportHTML</p>
  </footer>
</div>
</body></html>
"""
    )

    try:
        with open(htmlOut, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
    except Exception as e:
        Utilities.show_message("Error al escribir archivo", str(e), "OK", "", "")
        return 1

    Utilities.show_message(
        "Informe generado",
        f"El informe HTML se ha creado correctamente en:\n{htmlOut}",
        "OK",
        "",
        "",
    )

    return 0
