# MySQL Workbench Python script (Plugin/Module)
# Script to Generate an HTML Schema Report from Mysql Model
# Author: Tito Sanchez
# Update by: Fernando Gil
# Update2 by: Mgil10
# Written in MySQL Workbench 8.0.25

# To install this Plugin on MySQL Workbench version 8.0:
# 1. Download this file wuth a Python extension (.py)
# 2. Go to "Scripting" Menu on MySQL Workbench, and select "Install Plugin/Module" option
# 3. Find and select the file downloaded on step 1. Then restart MySQL Workbench
# 5. You can trigger the report from "Tools/Catalog" Menu, option "HTML Database Schema Report"

from wb import *
import grt
from mforms import Utilities, FileChooser
import mforms

ModuleInfo = DefineModule(
    name="DBReportHTML",
    author="Tito Sanchez & Mgil10",
    version="1.1",
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

    schema = catalog.schemata[0]
    html = []

    # HTML HEADER
    html.append(
        f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{schema.name} - Schema Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body {{ background-color: #f8f9fa; }}
        .table th {{ background-color: #e9ecef; }}
        .relation-badge {{ font-size: 0.85rem; }}
    </style>
</head>
<body>
<nav class="navbar navbar-dark bg-primary mb-4">
  <div class="container-fluid">
    <span class="navbar-brand mb-0 h1">Schema Report: {schema.name}</span>
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
    html.append('<h2 id="tables" class="mt-5 mb-3">Tablas</h2>')
    for table in schema.tables:
        html.append(
            f"""
        <div class="card mb-4 shadow-sm">
          <div class="card-header bg-secondary text-white">
            <h5 id="{table.name}" class="mb-0">{table.name}</h5>
          </div>
          <div class="card-body">
            <p><strong>Comentarios:</strong> {table.comment or "Sin comentarios"}</p>
            <div class="table-responsive">
              <table class="table table-bordered table-striped table-sm align-middle">
                <thead><tr>
                  <th>Nombre</th><th>Tipo de dato</th><th>Not Null</th><th>PK</th><th>FK</th><th>Default</th><th>Comentario</th>
                </tr></thead><tbody>
        """
        )
        for column in table.columns:
            pk = "✅" if table.isPrimaryKeyColumn(column) else ""
            fk = "🔗" if table.isForeignKeyColumn(column) else ""
            nn = "✔️" if column.isNotNull else ""
            html.append(
                f"<tr><td>{column.name}</td><td>{column.formattedType}</td><td>{nn}</td><td>{pk}</td><td>{fk}</td><td>{column.defaultValue or ''}</td><td>{column.comment or ''}</td></tr>"
            )
        html.append("</tbody></table></div>")

        # Foreign keys
        if table.foreignKeys:
            html.append("<p><strong>Claves foráneas:</strong></p><ul>")
            for fk in table.foreignKeys:
                ref_table = fk.referencedTable.name if fk.referencedTable else "?"
                html.append(
                    f"<li>{fk.name or '(sin nombre)'} → <span class='badge bg-info text-dark relation-badge'>{ref_table}</span></li>"
                )
            html.append("</ul>")
        else:
            html.append("<p><em>Sin claves foráneas.</em></p>")

        html.append(
            f'<a href="#tables" class="btn btn-outline-primary mt-3">Volver al listado</a></div></div>'
        )

    # VIEWS SECTION
    html.append('<h2 id="views" class="mt-5 mb-3">Vistas</h2>')
    if schema.views:
        for view in schema.views:
            html.append(
                f"""
            <div class="card mb-3">
              <div class="card-header bg-dark text-white">
                <h5 id="view_{view.name}" class="mb-0">{view.name}</h5>
              </div>
              <div class="card-body">
                <p><strong>Comentarios:</strong> {view.comment or "Sin comentarios"}</p>
                <p><strong>Definición SQL:</strong></p>
                <pre class="bg-light p-2 border">{view.sqlDefinition or "(No disponible)"}</pre>
                <a href="#views" class="btn btn-outline-secondary">Volver al listado</a>
              </div>
            </div>
            """
            )
    else:
        html.append("<p>No hay vistas definidas.</p>")

    # RELATIONS SECTION
    html.append('<h2 id="relations" class="mt-5 mb-3">Relaciones entre tablas</h2>')
    relations = []
    for table in schema.tables:
        for fk in table.foreignKeys:
            if fk.referencedTable:
                relations.append((table.name, fk.referencedTable.name, fk.name))
    if relations:
        html.append(
            '<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>Tabla origen</th><th>Tabla destino</th><th>Clave foránea</th></tr></thead><tbody>'
        )
        for src, dest, fkname in relations:
            html.append(
                f"<tr><td>{src}</td><td>{dest}</td><td>{fkname or '(sin nombre)'}</td></tr>"
            )
        html.append("</tbody></table></div>")
    else:
        html.append("<p>No existen relaciones entre tablas.</p>")

    # FOOTER
    html.append(
        """
  <footer class="mt-5 text-center text-muted">
    <hr>
    <p>Generado automáticamente por DBReportHTML</p>
  </footer>
</div>
</body></html>
"""
    )

    with open(htmlOut, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    Utilities.show_message(
        "Informe generado",
        f"El informe HTML se ha creado correctamente en:\n{htmlOut}",
        "OK",
        "",
        "",
    )

    return 0
