from flask import Flask, render_template, request, redirect, url_for, session, Response, send_file, jsonify
import sqlite3
from datetime import datetime, date
import csv
import io
import os
import base64
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = "logixware_secret_key_2026"
DB_NAME = os.path.join(os.path.dirname(__file__), "logixware.db")

# ─────────────────────────────────────────────
#  ROLES Y MENÚ
# ─────────────────────────────────────────────

ROLES = {
    "Administrador": [
        "dashboard", "gerencia", "contratos", "clientes", "facturacion", "pagos",
      "equipo", "nomina", "tareas", "reportes",
    init_db()
    app.run(debug=True, port=5000)ortes", "documentos", "usuarios", "accesos",
        "logs", "mantenimiento", "documentacion", "monitoreo", "estudiantes",
        "carnets", "reportes_admin", "inversionistas", "configuracion"
    ],
    "Gerencia": [
        "dashboard", "gerencia", "clientes", "contratos", "facturacion", "pagos",
        "equipo", "nomina", "reportes", "documentos", "inversionistas", "reportes_admin"
    ],
    "Desarrollador / Technical Lead": [
        "dashboard", "logs", "mantenimiento", "documentacion", "reportes", "tareas"
    ],
    "Analista de Soporte / NOC Analyst": [
        "dashboard", "monitoreo", "estudiantes", "carnets", "tareas", "clientes"
    ],
    "Ejecutivo de Operaciones / Legal": [
        "dashboard", "facturacion", "contratos", "pagos", "reportes_admin", "documentos"
    ],
    "Inversionista": [
        "dashboard", "inversionistas", "reportes", "reportes_admin"
    ]
}

MENU = [
    ("Dashboard",                "dashboard",     "/"),
    ("Gerencia",                 "gerencia",      "/gerencia"),
    ("Contratos",                "contratos",     "/contratos"),
    ("Clientes / Instituciones", "clientes",      "/clientes"),
    ("Facturación",              "facturacion",   "/facturacion"),
    ("Pagos",                    "pagos",         "/pagos"),
    ("Equipo",                   "equipo",        "/equipo"),
    ("Nómina",                   "nomina",        "/nomina"),
    ("Tareas",                   "tareas",        "/tareas"),
    ("Reportes",                 "reportes",      "/reportes"),
    ("Reportes Administrativos", "reportes_admin","/reportes-admin"),
    ("Documentos",               "documentos",    "/documentos"),
    ("Inversionistas / Socios",  "inversionistas","/inversionistas"),
    ("Usuarios",                 "usuarios",      "/usuarios"),
    ("Roles y accesos",          "accesos",       "/accesos"),
    ("Logs de auditoría",        "logs",          "/logs"),
    ("Mantenimiento",            "mantenimiento", "/mantenimiento"),
    ("Documentación técnica",    "documentacion", "/documentacion"),
    ("Monitoreo colegios",       "monitoreo",     "/monitoreo"),
    ("Buscador estudiantes",     "estudiantes",   "/estudiantes"),
    ("Reimpresión carnets",      "carnets",       "/carnets"),
    ("Configuración",            "configuracion", "/configuracion"),
]

MODULOS = {
    "gerencia": {
        "titulo": "Gerencia",
        "boton": "Crear decisión gerencial",
        "descripcion": "Decisiones estratégicas, administrativas y financieras.",
        "icono": "bi-briefcase-fill",
        "fields": [
            {"name": "titulo",  "label": "Título de la decisión",          "type": "text"},
            {"name": "detalle", "label": "Detalle estratégico",            "type": "textarea"},
            {"name": "extra1",  "label": "Área afectada",                  "type": "select",
             "options": ["Sistemas", "Legal", "Finanzas", "Comercial", "RRHH"]},
            {"name": "extra2",  "label": "Impacto financiero COP",         "type": "number"},
            {"name": "extra3",  "label": "Responsable de ejecución",       "type": "text"},
            {"name": "extra4",  "label": "Fecha límite",                   "type": "date"},
            {"name": "estado",  "label": "Estado",                         "type": "select",
             "options": ["Pendiente", "En proceso", "Aprobada", "Finalizada"]},
        ],
        "columns": ["titulo", "extra1", "extra2", "extra3", "extra4", "estado"],
    },
    "clientes": {
        "titulo": "Clientes / Instituciones",
        "boton": "Crear cliente / institución",
        "descripcion": "Registro de colegios, instituciones y contactos principales.",
        "icono": "bi-building",
        "fields": [
            {"name": "titulo",  "label": "Nombre del colegio / institución", "type": "text"},
            {"name": "detalle", "label": "Contacto principal",               "type": "text"},
            {"name": "extra1",  "label": "Teléfono",                         "type": "text"},
            {"name": "extra2",  "label": "Correo",                           "type": "email"},
            {"name": "extra3",  "label": "Ciudad / sede",                    "type": "text"},
            {"name": "extra4",  "label": "NIT / Documento",                  "type": "text"},
            {"name": "estado",  "label": "Estado",                           "type": "select",
             "options": ["Activo", "Inactivo", "En negociación"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"],
    },
    "facturacion": {
        "titulo": "Facturación",
        "boton": "Crear factura",
        "descripcion": "Control de facturas, vencimientos y cobros a instituciones.",
        "icono": "bi-receipt",
        "fields": [
            {"name": "titulo",  "label": "Concepto de factura",        "type": "text"},
            {"name": "detalle", "label": "Cliente / Institución",      "type": "text"},
            {"name": "extra1",  "label": "Valor total COP",            "type": "number"},
            {"name": "extra2",  "label": "Fecha de emisión",           "type": "date"},
            {"name": "extra3",  "label": "Fecha de vencimiento",       "type": "date"},
            {"name": "extra4",  "label": "Método de pago esperado",    "type": "select",
             "options": ["Nequi", "Transferencia Bancaria", "PSE", "Efectivo"]},
            {"name": "extra5",  "label": "Número de factura",          "type": "text"},
            {"name": "estado",  "label": "Estado del cobro",           "type": "select",
             "options": ["Borrador", "Pendiente de pago", "Pagada", "Vencida"]},
        ],
        "columns": ["extra5", "titulo", "detalle", "extra1", "extra2", "extra3", "estado"],
    },
    "pagos": {
        "titulo": "Pagos",
        "boton": "Registrar pago",
        "descripcion": "Pagos recibidos por servicios, licencias y contratos.",
        "icono": "bi-cash-coin",
        "fields": [
            {"name": "titulo",  "label": "Cliente que pagó",           "type": "text"},
            {"name": "detalle", "label": "Concepto pagado",            "type": "text"},
            {"name": "extra1",  "label": "Valor pagado COP",           "type": "number"},
            {"name": "extra2",  "label": "Método de pago",             "type": "select",
             "options": ["Nequi", "Transferencia Bancaria", "PSE", "Efectivo"]},
            {"name": "extra3",  "label": "Fecha del pago",             "type": "date"},
            {"name": "extra4",  "label": "Referencia / Comprobante",   "type": "text"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Confirmado", "Pendiente de verificar", "Rechazado"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"],
    },
    "nomina": {
        "titulo": "Nómina",
        "boton": "Registrar pago de nómina",
        "descripcion": "Pagos de salarios, bonificaciones y deducciones del equipo.",
        "icono": "bi-wallet2",
        "fields": [
            {"name": "titulo",  "label": "Empleado",                   "type": "text"},
            {"name": "detalle", "label": "Cargo",                      "type": "text"},
            {"name": "extra1",  "label": "Salario base COP",           "type": "number"},
            {"name": "extra2",  "label": "Bonificaciones COP",         "type": "number"},
            {"name": "extra3",  "label": "Deducciones COP",            "type": "number"},
            {"name": "extra4",  "label": "Total neto COP",             "type": "number"},
            {"name": "extra5",  "label": "Período (mes/año)",          "type": "text"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Pendiente", "Pagado", "En revisión"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "extra4", "extra5", "estado"],
    },
    "equipo": {
        "titulo": "Equipo",
        "boton": "Agregar miembro",
        "descripcion": "Equipo interno, responsabilidades y cargos.",
        "icono": "bi-people-fill",
        "fields": [
            {"name": "titulo",  "label": "Nombre completo",            "type": "text"},
            {"name": "detalle", "label": "Cargo",                      "type": "text"},
            {"name": "extra1",  "label": "Correo",                     "type": "email"},
            {"name": "extra2",  "label": "Teléfono",                   "type": "text"},
            {"name": "extra3",  "label": "Fecha de ingreso",           "type": "date"},
            {"name": "extra4",  "label": "Tipo de contrato",           "type": "select",
             "options": ["Indefinido", "Fijo", "Prestación de servicios", "Pasantía"]},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Activo", "Inactivo", "Vacaciones", "Licencia"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra4", "estado"],
    },
    "tareas": {
        "titulo": "Tareas",
        "boton": "Crear tarea",
        "descripcion": "Tareas operativas y administrativas del equipo.",
        "icono": "bi-check2-square",
        "fields": [
            {"name": "titulo",  "label": "Título de la tarea",         "type": "text"},
            {"name": "detalle", "label": "Descripción",                "type": "textarea"},
            {"name": "extra1",  "label": "Responsable",                "type": "text"},
            {"name": "extra2",  "label": "Fecha límite",               "type": "date"},
            {"name": "extra3",  "label": "Prioridad",                  "type": "select",
             "options": ["Baja", "Media", "Alta", "Urgente"]},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Pendiente", "En proceso", "Finalizada", "Cancelada"]},
        ],
        "columns": ["titulo", "extra1", "extra2", "extra3", "estado"],
    },
    "reportes": {
        "titulo": "Reportes",
        "boton": "Crear reporte",
        "descripcion": "Filtros, métricas y exportaciones para análisis operativo.",
        "icono": "bi-bar-chart-fill",
        "fields": [
            {"name": "titulo",  "label": "Nombre del reporte",         "type": "text"},
            {"name": "detalle", "label": "Institución",                "type": "text"},
            {"name": "extra1",  "label": "Desde",                      "type": "date"},
            {"name": "extra2",  "label": "Hasta",                      "type": "date"},
            {"name": "extra3",  "label": "Tipo de reporte",            "type": "select",
             "options": ["Financiero", "Soporte Técnico", "Rendimiento de Asistencia", "Operativo"]},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Generado", "Pendiente", "Archivado"]},
        ],
        "columns": ["titulo", "extra3", "detalle", "extra1", "extra2", "estado"],
    },
    "reportes_admin": {
        "titulo": "Reportes administrativos",
        "boton": "Crear reporte administrativo",
        "descripcion": "Ingresos, cuentas por cobrar, gastos, margen y estabilidad.",
        "icono": "bi-graph-up-arrow",
        "fields": [
            {"name": "titulo",  "label": "Nombre del reporte",         "type": "text"},
            {"name": "detalle", "label": "Institución o consolidado",  "type": "text"},
            {"name": "extra1",  "label": "Ingresos brutos COP",        "type": "number"},
            {"name": "extra2",  "label": "Cuentas por cobrar COP",     "type": "number"},
            {"name": "extra3",  "label": "Gastos de operación COP",    "type": "number"},
            {"name": "extra4",  "label": "Margen neto COP",            "type": "number"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Borrador", "Final", "Presentado"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "extra4", "estado"],
    },
    "documentos": {
        "titulo": "Documentos",
        "boton": "Registrar documento",
        "descripcion": "Contratos, soportes, archivos y documentos legales.",
        "icono": "bi-folder2-open",
        "fields": [
            {"name": "titulo",  "label": "Nombre del documento",       "type": "text"},
            {"name": "detalle", "label": "Descripción",                "type": "textarea"},
            {"name": "extra1",  "label": "Tipo",                       "type": "select",
             "options": ["Contrato", "Factura", "Soporte", "Legal", "Técnico", "RRHH"]},
            {"name": "extra2",  "label": "Responsable",                "type": "text"},
            {"name": "extra3",  "label": "Fecha del documento",        "type": "date"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Vigente", "Archivado", "Pendiente"]},
        ],
        "columns": ["titulo", "extra1", "extra2", "extra3", "estado"],
    },
    "inversionistas": {
        "titulo": "Inversionistas / Socios",
        "boton": "Registrar movimiento societario",
        "descripcion": "Aportes, capital, contratos de sociedad y utilidades.",
        "icono": "bi-currency-dollar",
        "fields": [
            {"name": "titulo",  "label": "Socio / inversionista",      "type": "text"},
            {"name": "detalle", "label": "Concepto",                   "type": "text"},
            {"name": "extra1",  "label": "Aporte o capital COP",       "type": "number"},
            {"name": "extra2",  "label": "Porcentaje de participación","type": "number"},
            {"name": "extra3",  "label": "Documento asociado",         "type": "text"},
            {"name": "extra4",  "label": "Fecha del movimiento",       "type": "date"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Activo", "Pendiente", "Cerrado"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra4", "estado"],
    },
    "documentacion": {
        "titulo": "Documentación técnica",
        "boton": "Crear documento técnico",
        "descripcion": "Manuales de código, base de datos, APIs y despliegue.",
        "icono": "bi-code-slash",
        "fields": [
            {"name": "titulo",  "label": "Título del documento",       "type": "text"},
            {"name": "detalle", "label": "Contenido / descripción",    "type": "textarea"},
            {"name": "extra1",  "label": "Categoría",                  "type": "select",
             "options": ["Código", "PostgreSQL", "Railway", "APIs", "Despliegue", "Seguridad"]},
            {"name": "extra2",  "label": "Responsable",                "type": "text"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Borrador", "Revisado", "Publicado"]},
        ],
        "columns": ["titulo", "extra1", "extra2", "estado"],
    },
    "monitoreo": {
        "titulo": "Monitoreo colegios",
        "boton": "Registrar nodo / colegio",
        "descripcion": "Estado de lectores QR, sincronización y actividad diaria.",
        "icono": "bi-wifi",
        "fields": [
            {"name": "titulo",  "label": "Nombre del colegio",         "type": "text"},
            {"name": "detalle", "label": "Última sincronización",      "type": "text"},
            {"name": "extra1",  "label": "Estado del servidor",        "type": "select",
             "options": ["Online", "Offline", "Intermitente"]},
            {"name": "extra2",  "label": "Alumnos activos hoy",        "type": "number"},
            {"name": "extra3",  "label": "Observación técnica",        "type": "text"},
            {"name": "estado",  "label": "Prioridad",                  "type": "select",
             "options": ["Normal", "Media", "Alta", "Crítica"]},
        ],
        "columns": ["titulo", "extra1", "detalle", "extra2", "estado"],
    },
    "estudiantes": {
        "titulo": "Buscador estudiantes",
        "boton": "Registrar estudiante",
        "descripcion": "Búsqueda global por documento, código o institución.",
        "icono": "bi-person-badge",
        "fields": [
            {"name": "titulo",  "label": "Nombre del estudiante",      "type": "text"},
            {"name": "detalle", "label": "Documento o código",         "type": "text"},
            {"name": "extra1",  "label": "Institución",                "type": "text"},
            {"name": "extra2",  "label": "Grado",                      "type": "text"},
            {"name": "extra3",  "label": "Acudiente / teléfono",       "type": "text"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Activo", "Inactivo", "Bloqueado"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"],
    },
    "carnets": {
        "titulo": "Reimpresión carnets",
        "boton": "Crear solicitud de carnet",
        "descripcion": "Historial de solicitudes de QR y carnets de reemplazo.",
        "icono": "bi-credit-card-2-front",
        "fields": [
            {"name": "titulo",  "label": "Nombre del alumno",          "type": "text"},
            {"name": "detalle", "label": "Colegio",                    "type": "text"},
            {"name": "extra1",  "label": "Grado",                      "type": "text"},
            {"name": "extra2",  "label": "Motivo de reimpresión",      "type": "select",
             "options": ["Pérdida", "Daño", "Cambio de datos", "Reposición"]},
            {"name": "extra3",  "label": "Documento del estudiante",   "type": "text"},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Solicitado", "Generado", "Entregado"]},
        ],
        "columns": ["detalle", "titulo", "extra1", "extra2", "estado"],
    },
    "mantenimiento": {
        "titulo": "Mantenimiento",
        "boton": "Crear acción de mantenimiento",
        "descripcion": "Despliegues, cambios y revisión del sistema.",
        "icono": "bi-tools",
        "fields": [
            {"name": "titulo",  "label": "Acción de mantenimiento",    "type": "text"},
            {"name": "detalle", "label": "Detalle técnico",            "type": "textarea"},
            {"name": "extra1",  "label": "Responsable",                "type": "text"},
            {"name": "extra2",  "label": "Fecha programada",           "type": "date"},
            {"name": "extra3",  "label": "Tipo",                       "type": "select",
             "options": ["Preventivo", "Correctivo", "Despliegue", "Actualización"]},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Programado", "En ejecución", "Completado", "Cancelado"]},
        ],
        "columns": ["titulo", "extra1", "extra2", "extra3", "estado"],
    },
    "configuracion": {
        "titulo": "Configuración",
        "boton": "Agregar ajuste",
        "descripcion": "Parámetros generales del sistema.",
        "icono": "bi-gear-fill",
        "fields": [
            {"name": "titulo",  "label": "Nombre del ajuste",          "type": "text"},
            {"name": "detalle", "label": "Valor o descripción",        "type": "text"},
            {"name": "extra1",  "label": "Área",                       "type": "select",
             "options": ["Sistema", "Usuarios", "Diseño", "Seguridad", "Facturación"]},
            {"name": "estado",  "label": "Estado",                     "type": "select",
             "options": ["Activo", "Inactivo"]},
        ],
        "columns": ["titulo", "detalle", "extra1", "estado"],
    },
}

SLUGS = {
    "reportes-admin": "reportes_admin",
}

# ─────────────────────────────────────────────
#  BASE DE DATOS
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_missing(conn, table, column, col_type="TEXT"):
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_db():
    conn = get_db()

    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre   TEXT NOT NULL,
        usuario  TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol      TEXT NOT NULL,
        estado   TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS contratos (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        institucion       TEXT NOT NULL,
        sistema           TEXT NOT NULL,
        fecha_inicio      TEXT NOT NULL,
        fecha_vencimiento TEXT NOT NULL,
        valor             TEXT NOT NULL,
        estado            TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS auditoria (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha    TEXT NOT NULL,
        usuario  TEXT NOT NULL,
        accion   TEXT NOT NULL,
        modulo   TEXT NOT NULL,
        resultado TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS registros (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo TEXT NOT NULL,
        titulo TEXT,
        detalle TEXT,
        estado TEXT,
        fecha  TEXT
    )""")

    for col in ["extra1", "extra2", "extra3", "extra4", "extra5", "extra6"]:
        add_column_if_missing(conn, "registros", col)

    # Usuarios base con contraseñas hasheadas
    usuarios_base = [
        ("Sebastián (Admin)",      "admin",    "admin1234",  "Administrador"),
        ("Gerencia General",       "gerencia", "gerencia123","Gerencia"),
        ("Juan Camilo (Dev)",      "juan",     "juan1234",   "Desarrollador / Technical Lead"),
        ("Laura (NOC)",            "laura",    "laura1234",  "Analista de Soporte / NOC Analyst"),
        ("Martha (Legal)",         "martha",   "martha1234", "Ejecutivo de Operaciones / Legal"),
        ("Carlos (Inversionista)", "carlos",   "carlos1234", "Inversionista"),
    ]

    for nombre, usuario, pwd, rol in usuarios_base:
        existe = conn.execute("SELECT id FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
        if not existe:
            hashed = generate_password_hash(pwd)
            conn.execute(
                "INSERT INTO usuarios (nombre, usuario, password, rol, estado) VALUES (?, ?, ?, ?, ?)",
                (nombre, usuario, hashed, rol, "Activo")
            )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def protegido():
    return "user" in session


def tiene_permiso(modulo):
    return modulo in ROLES.get(session.get("rol", ""), [])


def validar_acceso(modulo):
    if not protegido():
        return redirect(url_for("login"))
    if not tiene_permiso(modulo):
        return redirect(url_for("sin_permiso"))
    return None


def auditar(accion, modulo):
    if "nombre" not in session:
        return
    conn = get_db()
    conn.execute(
        "INSERT INTO auditoria (fecha, usuario, accion, modulo, resultado) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session["nombre"], accion, modulo, "Correcto")
    )
    conn.commit()
    conn.close()


def normalizar_modulo(slug):
    return SLUGS.get(slug, slug.replace("-", "_"))


def ruta_modulo(modulo):
    return modulo.replace("_", "-")


def label_for(config, col):
    for f in config["fields"]:
        if f["name"] == col:
            return f["label"]
    return col


def money(value):
    try:
        n = int(float(str(value).replace(".", "").replace(",", "")))
        return "$" + f"{n:,}".replace(",", ".")
    except Exception:
        return value or ""


def obtener_registros(modulo, busqueda=""):
    conn = get_db()
    if busqueda:
        registros = conn.execute(
            "SELECT * FROM registros WHERE modulo=? AND (titulo LIKE ? OR detalle LIKE ? OR extra1 LIKE ?) ORDER BY id DESC",
            (modulo, f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%")
        ).fetchall()
    else:
        registros = conn.execute(
            "SELECT * FROM registros WHERE modulo=? ORDER BY id DESC", (modulo,)
        ).fetchall()
    conn.close()
    return registros


def obtener_contrato(id):
    conn = get_db()
    contrato = conn.execute("SELECT * FROM contratos WHERE id=?", (id,)).fetchone()
    conn.close()
    return contrato


def logo_base64():
    logo_path = os.path.join(app.root_path, "static", "img", "logo.png")
    if not os.path.exists(logo_path):
        return ""
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


# ─────────────────────────────────────────────
#  PDF / CSV / WORD
# ─────────────────────────────────────────────

def encabezado_pdf(elements, styles):
    logo_path = os.path.join(app.root_path, "static", "img", "logo.png")

    titulo_style = ParagraphStyle("titulo_membrete", parent=styles["Title"],
                                  alignment=TA_CENTER, fontSize=16, leading=20)
    centro_style = ParagraphStyle("centro_membrete", parent=styles["Normal"],
                                  alignment=TA_CENTER, fontSize=9, leading=12)

    logo_img = Image(logo_path, width=70, height=70) if os.path.exists(logo_path) \
        else Paragraph("", styles["Normal"])

    texto = [
        Paragraph("<b>LOGIXWARE</b>", titulo_style),
        Paragraph("SEDE PRINCIPAL", centro_style),
        Paragraph("NIT: 900.999.999-1", centro_style),
        Paragraph("Calle 20 #17-99, Caracolí, Antioquia, Colombia", centro_style),
        Paragraph(f"Impreso: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", centro_style),
    ]

    tabla = Table([[logo_img, texto, ""]], colWidths=[1.4*inch, 7.2*inch, 1.4*inch])
    tabla.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",   (0, 0), (1, 0),   "CENTER"),
        ("BOX",     (0, 0), (-1, -1), 0, colors.white),
    ]))
    elements.append(tabla)
    elements.append(Spacer(1, 24))


def crear_pdf(modulo, registros):
    config = MODULOS[modulo]
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=28, leftMargin=28, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []
    encabezado_pdf(elements, styles)
    elements.append(Paragraph(f"<b>{config['titulo'].upper()}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 25))

    headers = [label_for(config, col).upper() for col in config["columns"]] + ["FECHA"]
    data = [headers]

    for r in registros:
        fila = []
        for col in config["columns"]:
            valor = str(r[col] or "")
            etiqueta = label_for(config, col).lower()
            if any(k in etiqueta for k in ["valor", "cop", "financiero", "capital", "salario", "neto", "bruto"]):
                valor = money(valor)
            fila.append(valor)
        fila.append(str(r["fecha"] or ""))
        data.append(fila)

    if len(data) == 1:
        data.append(["SIN REGISTROS"] + [""] * (len(headers) - 1))

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("GRID",       (0, 0), (-1, -1), 0.7, colors.black),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_contrato_pdf(contrato, tipo="copia"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=45, leftMargin=45, topMargin=28, bottomMargin=35)
    styles = getSampleStyleSheet()

    normal = ParagraphStyle("normal_contrato", parent=styles["Normal"],
                            fontSize=10, leading=15, alignment=TA_LEFT)
    titulo_style = ParagraphStyle("titulo_contrato", parent=styles["Title"],
                                  alignment=TA_CENTER, fontSize=15)

    elements = []
    encabezado_pdf(elements, styles)

    titulo_tipo = "COPIA DE CONTRATO" if tipo == "copia" else "CONTRATO ORIGINAL"
    elements.append(Paragraph(f"<b>{titulo_tipo}</b>", titulo_style))
    elements.append(Spacer(1, 18))

    texto = f"""
    Entre <b>LogixWare</b>, empresa de soluciones tecnológicas educativas,
    y la institución <b>{contrato['institucion']}</b>, se deja constancia del contrato
    asociado al sistema <b>{contrato['sistema']}</b>.<br/><br/>
    <b>Fecha de inicio:</b> {contrato['fecha_inicio']}<br/>
    <b>Fecha de vencimiento:</b> {contrato['fecha_vencimiento']}<br/>
    <b>Valor del contrato:</b> {money(contrato['valor'])}<br/>
    <b>Estado:</b> {contrato['estado']}<br/><br/>
    Este documento se genera como soporte formal para control administrativo, facturación,
    seguimiento operativo y archivo institucional.
    """

    elements.append(Paragraph(texto, normal))
    elements.append(Spacer(1, 50))

    firmas = Table([
        ["______________________________", "______________________________"],
        ["Representante LogixWare",        "Representante Institución"],
    ], colWidths=[3.4*inch, 3.4*inch])
    firmas.setStyle(TableStyle([
        ("ALIGN",    (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(firmas)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_csv(modulo, registros):
    config = MODULOS[modulo]
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [label_for(config, col) for col in config["columns"]] + ["Fecha"]
    writer.writerow(headers)
    for r in registros:
        writer.writerow([r[col] for col in config["columns"]] + [r["fecha"]])
    return output.getvalue()


def crear_word_html(modulo, registros):
    config = MODULOS[modulo]
    headers = [label_for(config, col).upper() for col in config["columns"]] + ["FECHA"]
    rows = ""
    for r in registros:
        rows += "<tr>"
        for col in config["columns"]:
            valor = str(r[col] or "")
            etiqueta = label_for(config, col).lower()
            if any(k in etiqueta for k in ["valor", "cop", "capital", "salario", "neto", "bruto"]):
                valor = money(valor)
            rows += f"<td>{valor}</td>"
        rows += f"<td>{r['fecha'] or ''}</td></tr>"

    if not rows:
        rows = f"<tr><td colspan='{len(headers)}'>SIN REGISTROS</td></tr>"

    logo = logo_base64()
    return f"""<html><head><meta charset="UTF-8">
    <style>
      body{{font-family:Arial,sans-serif;color:#000}}
      .header{{width:100%;border-collapse:collapse;margin-bottom:35px}}
      .header td{{border:none}}
      .logo img{{width:80px;height:80px;object-fit:contain}}
      .info{{text-align:center;font-size:13px}}
      .info h1{{font-size:22px;margin:0 0 8px;font-weight:bold}}
      h2{{margin-top:30px;font-size:20px}}
      .tabla-datos{{width:100%;border-collapse:collapse;margin-top:40px;font-size:12px}}
      .tabla-datos th{{background:#1a1a2e;color:#fff;border:1px solid #000;padding:8px;text-align:center}}
      .tabla-datos td{{border:1px solid #000;padding:8px;text-align:center}}
    </style></head><body>
    <table class="header"><tr>
      <td class="logo"><img src="{logo}"></td>
      <td class="info"><h1>LOGIXWARE</h1>
        <div>NIT: 900.999.999-1</div>
        <div>Calle 20 #17-99, Caracolí, Antioquia</div>
        <div>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
      </td><td style="width:120px;"></td>
    </tr></table>
    <h2>{config['titulo'].upper()}</h2>
    <table class="tabla-datos">
      <tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr>
      {rows}
    </table></body></html>"""


# ─────────────────────────────────────────────
#  CONTEXT PROCESSOR
# ─────────────────────────────────────────────

@app.context_processor
def globales():
    permisos = ROLES.get(session.get("rol", ""), [])
    return {
        "nombre_actual":  session.get("nombre", ""),
        "rol_actual":     session.get("rol", ""),
        "menu_visible":   [m for m in MENU if m[1] in permisos],
        "permisos":       permisos,
        "anio_actual":    datetime.now().year,
    }


# ─────────────────────────────────────────────
#  RUTAS: AUTH
# ─────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND estado='Activo'",
            (request.form["usuario"],)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            session["user"]   = user["usuario"]
            session["nombre"] = user["nombre"]
            session["rol"]    = user["rol"]
            auditar("Inicio de sesión", "Login")
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


@app.route("/logout")
def logout():
    auditar("Cierre de sesión", "Login")
    session.clear()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────
#  RUTAS: DASHBOARD
# ─────────────────────────────────────────────

@app.route("/")
def dashboard():
    if not protegido():
        return redirect(url_for("login"))

    conn = get_db()

    # Estadísticas generales
    total_contratos  = conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    total_usuarios   = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    total_clientes   = conn.execute("SELECT COUNT(*) FROM registros WHERE modulo='clientes'").fetchone()[0]
    total_tareas     = conn.execute("SELECT COUNT(*) FROM registros WHERE modulo='tareas' AND estado='Pendiente'").fetchone()[0]

    # Ingresos del módulo pagos (confirmados)
    pagos_rows = conn.execute(
        "SELECT extra1 FROM registros WHERE modulo='pagos' AND estado='Confirmado'"
    ).fetchall()
    total_ingresos = sum(
        int(float(str(r["extra1"]).replace(".", "").replace(",", "")))
        for r in pagos_rows if r["extra1"]
    )

    # Facturas pendientes
    facturas_pendientes = conn.execute(
        "SELECT COUNT(*) FROM registros WHERE modulo='facturacion' AND estado='Pendiente de pago'"
    ).fetchone()[0]

    # Contratos próximos a vencer (30 días)
    hoy = date.today()
    contratos_todos = conn.execute("SELECT * FROM contratos WHERE estado='Activo'").fetchall()
    contratos_por_vencer = []
    for c in contratos_todos:
        try:
            fv = datetime.strptime(c["fecha_vencimiento"], "%Y-%m-%d").date()
            dias = (fv - hoy).days
            if 0 <= dias <= 30:
                contratos_por_vencer.append({"contrato": c, "dias": dias})
        except Exception:
            pass

    # Últimos 5 contratos
    contratos_recientes = conn.execute("SELECT * FROM contratos ORDER BY id DESC LIMIT 5").fetchall()

    # Últimas 5 tareas
    tareas_recientes = conn.execute(
        "SELECT * FROM registros WHERE modulo='tareas' ORDER BY id DESC LIMIT 5"
    ).fetchall()

    # Actividad reciente (logs)
    logs_recientes = conn.execute(
        "SELECT * FROM auditoria ORDER BY id DESC LIMIT 8"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_contratos=total_contratos,
        total_usuarios=total_usuarios,
        total_clientes=total_clientes,
        total_tareas=total_tareas,
        total_ingresos=money(str(total_ingresos)),
        facturas_pendientes=facturas_pendientes,
        contratos_por_vencer=contratos_por_vencer,
        contratos_recientes=contratos_recientes,
        tareas_recientes=tareas_recientes,
        logs_recientes=logs_recientes,
    )


# ─────────────────────────────────────────────
#  RUTAS: ACCESO DENEGADO / LOGS / ACCESOS
# ─────────────────────────────────────────────

@app.route("/sin-permiso")
def sin_permiso():
    return render_template("modulo.html", titulo="Acceso denegado",
                           descripcion="No tienes permisos para acceder a esta sección.")


@app.route("/logs")
def logs():
    bloqueo = validar_acceso("logs")
    if bloqueo:
        return bloqueo
    conn = get_db()
    logs = conn.execute("SELECT * FROM auditoria ORDER BY id DESC LIMIT 200").fetchall()
    conn.close()
    return render_template("logs.html", logs=logs)


@app.route("/accesos")
def accesos():
    bloqueo = validar_acceso("accesos")
    if bloqueo:
        return bloqueo
    return render_template("accesos.html", roles=ROLES)


# ─────────────────────────────────────────────
#  RUTAS: USUARIOS
# ─────────────────────────────────────────────

@app.route("/usuarios")
def usuarios():
    bloqueo = validar_acceso("usuarios")
    if bloqueo:
        return bloqueo
    conn = get_db()
    usuarios = conn.execute("SELECT * FROM usuarios ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)


@app.route("/usuarios/nuevo", methods=["GET", "POST"])
def nuevo_usuario():
    bloqueo = validar_acceso("usuarios")
    if bloqueo:
        return bloqueo
    if request.method == "POST":
        conn = get_db()
        hashed = generate_password_hash(request.form["password"])
        conn.execute(
            "INSERT INTO usuarios (nombre, usuario, password, rol, estado) VALUES (?, ?, ?, ?, ?)",
            (request.form["nombre"], request.form["usuario"], hashed,
             request.form["rol"], request.form["estado"])
        )
        conn.commit()
        conn.close()
        auditar("Creó usuario", "Usuarios")
        return redirect(url_for("usuarios"))
    return render_template("usuario_form.html", usuario=None, roles=ROLES.keys())


@app.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    bloqueo = validar_acceso("usuarios")
    if bloqueo:
        return bloqueo
    conn = get_db()
    usuario = conn.execute("SELECT * FROM usuarios WHERE id=?", (id,)).fetchone()
    if request.method == "POST":
        nueva_pwd = request.form["password"]
        if nueva_pwd:
            hashed = generate_password_hash(nueva_pwd)
        else:
            hashed = usuario["password"]
        conn.execute(
            "UPDATE usuarios SET nombre=?, usuario=?, password=?, rol=?, estado=? WHERE id=?",
            (request.form["nombre"], request.form["usuario"], hashed,
             request.form["rol"], request.form["estado"], id)
        )
        conn.commit()
        conn.close()
        auditar("Editó usuario", "Usuarios")
        return redirect(url_for("usuarios"))
    conn.close()
    return render_template("usuario_form.html", usuario=usuario, roles=ROLES.keys())


@app.route("/usuarios/eliminar/<int:id>")
def eliminar_usuario(id):
    bloqueo = validar_acceso("usuarios")
    if bloqueo:
        return bloqueo
    conn = get_db()
    conn.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conn.commit()
    conn.close()
    auditar("Eliminó usuario", "Usuarios")
    return redirect(url_for("usuarios"))


# ─────────────────────────────────────────────
#  RUTAS: CONTRATOS
# ─────────────────────────────────────────────

@app.route("/contratos")
def contratos():
    bloqueo = validar_acceso("contratos")
    if bloqueo:
        return bloqueo
    busqueda = request.args.get("q", "")
    conn = get_db()
    if busqueda:
        contratos = conn.execute(
            "SELECT * FROM contratos WHERE institucion LIKE ? OR sistema LIKE ? ORDER BY id DESC",
            (f"%{busqueda}%", f"%{busqueda}%")
        ).fetchall()
    else:
        contratos = conn.execute("SELECT * FROM contratos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("contratos.html", contratos=contratos, busqueda=busqueda)


@app.route("/contratos/nuevo", methods=["GET", "POST"])
def nuevo_contrato():
    bloqueo = validar_acceso("contratos")
    if bloqueo:
        return bloqueo
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO contratos (institucion, sistema, fecha_inicio, fecha_vencimiento, valor, estado) VALUES (?, ?, ?, ?, ?, ?)",
            (request.form["institucion"], request.form["sistema"], request.form["fecha_inicio"],
             request.form["fecha_vencimiento"], request.form["valor"], request.form["estado"])
        )
        conn.commit()
        conn.close()
        auditar("Creó contrato", "Contratos")
        return redirect(url_for("contratos"))
    return render_template("contrato_form.html", contrato=None)


@app.route("/contratos/editar/<int:id>", methods=["GET", "POST"])
def editar_contrato(id):
    bloqueo = validar_acceso("contratos")
    if bloqueo:
        return bloqueo
    conn = get_db()
    contrato = conn.execute("SELECT * FROM contratos WHERE id=?", (id,)).fetchone()
    if request.method == "POST":
        conn.execute(
            "UPDATE contratos SET institucion=?, sistema=?, fecha_inicio=?, fecha_vencimiento=?, valor=?, estado=? WHERE id=?",
            (request.form["institucion"], request.form["sistema"], request.form["fecha_inicio"],
             request.form["fecha_vencimiento"], request.form["valor"], request.form["estado"], id)
        )
        conn.commit()
        conn.close()
        auditar("Editó contrato", "Contratos")
        return redirect(url_for("contratos"))
    conn.close()
    return render_template("contrato_form.html", contrato=contrato)


@app.route("/contratos/eliminar/<int:id>")
def eliminar_contrato(id):
    bloqueo = validar_acceso("contratos")
    if bloqueo:
        return bloqueo
    conn = get_db()
    conn.execute("DELETE FROM contratos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    auditar("Eliminó contrato", "Contratos")
    return redirect(url_for("contratos"))


@app.route("/contratos/pdf/<int:id>/<tipo>")
def contrato_pdf(id, tipo):
    bloqueo = validar_acceso("contratos")
    if bloqueo:
        return bloqueo
    contrato = obtener_contrato(id)
    if not contrato:
        return redirect(url_for("contratos"))
    pdf = crear_contrato_pdf(contrato, tipo)
    return send_file(pdf, as_attachment=True,
                     download_name=f"contrato_{tipo}_{id}.pdf",
                     mimetype="application/pdf")


# ─────────────────────────────────────────────
#  RUTAS: MÓDULOS GENÉRICOS (CRUD)
# ─────────────────────────────────────────────

@app.route("/<path:slug>/export/<fmt>")
def exportar_modulo(slug, fmt):
    modulo = normalizar_modulo(slug)
    if modulo not in MODULOS:
        return redirect(url_for("dashboard"))
    bloqueo = validar_acceso(modulo)
    if bloqueo:
        return bloqueo

    registros = obtener_registros(modulo)
    filename = f"{modulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if fmt == "pdf":
        pdf = crear_pdf(modulo, registros)
        return send_file(pdf, as_attachment=True,
                         download_name=f"{filename}.pdf",
                         mimetype="application/pdf")
    if fmt == "csv":
        csv_data = crear_csv(modulo, registros)
        return Response(csv_data, mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment;filename={filename}.csv"})
    if fmt == "word":
        html = crear_word_html(modulo, registros)
        return Response(html, mimetype="application/msword",
                        headers={"Content-Disposition": f"attachment;filename={filename}.doc"})

    return redirect("/" + ruta_modulo(modulo))


@app.route("/<path:slug>")
def vista_modulo(slug):
    modulo = normalizar_modulo(slug)
    if modulo not in MODULOS:
        return redirect(url_for("dashboard"))
    bloqueo = validar_acceso(modulo)
    if bloqueo:
        return bloqueo

    busqueda = request.args.get("q", "")
    registros = obtener_registros(modulo, busqueda)

    return render_template("crud.html",
                           modulo=modulo,
                           slug=ruta_modulo(modulo),
                           config=MODULOS[modulo],
                           registros=registros,
                           registro=None,
                           busqueda=busqueda)


@app.route("/<path:slug>/nuevo", methods=["GET", "POST"])
def nuevo_modulo(slug):
    modulo = normalizar_modulo(slug)
    if modulo not in MODULOS:
        return redirect(url_for("dashboard"))
    bloqueo = validar_acceso(modulo)
    if bloqueo:
        return bloqueo

    config = MODULOS[modulo]
    if request.method == "POST":
        data = {f["name"]: request.form.get(f["name"], "") for f in config["fields"]}
        conn = get_db()
        conn.execute("""
            INSERT INTO registros
            (modulo, titulo, detalle, estado, fecha, extra1, extra2, extra3, extra4, extra5, extra6)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (modulo, data.get("titulo",""), data.get("detalle",""),
              data.get("estado","Activo"), datetime.now().strftime("%Y-%m-%d"),
              data.get("extra1",""), data.get("extra2",""), data.get("extra3",""),
              data.get("extra4",""), data.get("extra5",""), data.get("extra6","")))
        conn.commit()
        conn.close()
        auditar("Creó registro", config["titulo"])
        return redirect("/" + ruta_modulo(modulo))

    return render_template("crud.html", modulo=modulo, slug=ruta_modulo(modulo),
                           config=config, registros=[], registro=None, creando=True)


@app.route("/<path:slug>/editar/<int:id>", methods=["GET", "POST"])
def editar_modulo(slug, id):
    modulo = normalizar_modulo(slug)
    if modulo not in MODULOS:
        return redirect(url_for("dashboard"))
    bloqueo = validar_acceso(modulo)
    if bloqueo:
        return bloqueo

    config = MODULOS[modulo]
    conn = get_db()
    registro = conn.execute("SELECT * FROM registros WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        data = {f["name"]: request.form.get(f["name"], "") for f in config["fields"]}
        conn.execute("""
            UPDATE registros
            SET titulo=?, detalle=?, estado=?, extra1=?, extra2=?, extra3=?, extra4=?, extra5=?, extra6=?
            WHERE id=?
        """, (data.get("titulo",""), data.get("detalle",""), data.get("estado","Activo"),
              data.get("extra1",""), data.get("extra2",""), data.get("extra3",""),
              data.get("extra4",""), data.get("extra5",""), data.get("extra6",""), id))
        conn.commit()
        conn.close()
        auditar("Editó registro", config["titulo"])
        return redirect("/" + ruta_modulo(modulo))

    registros = conn.execute(
        "SELECT * FROM registros WHERE modulo=? ORDER BY id DESC", (modulo,)
    ).fetchall()
    conn.close()
    return render_template("crud.html", modulo=modulo, slug=ruta_modulo(modulo),
                           config=config, registros=registros, registro=registro, editando=True)


@app.route("/<path:slug>/eliminar/<int:id>")
def eliminar_modulo(slug, id):
    modulo = normalizar_modulo(slug)
    if modulo not in MODULOS:
        return redirect(url_for("dashboard"))
    bloqueo = validar_acceso(modulo)
    if bloqueo:
        return bloqueo

    conn = get_db()
    conn.execute("DELETE FROM registros WHERE id=?", (id,))
    conn.commit()
    conn.close()
    auditar("Eliminó registro", MODULOS[modulo]["titulo"])
    return redirect("/" + ruta_modulo(modulo))


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

# Inicializar base de datos siempre
init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )