from flask import Flask, render_template, request, redirect, url_for, session, Response, send_file
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import csv
import io
import os
import base64

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

app = Flask(__name__)

# Configuración segura de Llave Secreta desde el entorno o fallback seguro
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "logixware_secret_key")

# Detección dinámica de Base de Datos (PostgreSQL en Railway / SQLite en Local)
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_NAME = "LogixWAre.db"

ROLES = {
    "Administrador": [
        "dashboard", "gerencia", "contratos", "clientes", "facturacion", "pagos",
        "equipo", "tareas", "reportes", "documentos", "usuarios", "accesos",
        "logs", "mantenimiento", "documentacion", "monitoreo", "estudiantes",
        "carnets", "reportes_admin", "inversionistas", "configuracion"
    ],
    "Gerencia": [
        "dashboard", "gerencia", "clientes", "contratos", "facturacion", "pagos",
        "equipo", "reportes", "documentos", "inversionistas", "reportes_admin"
    ],
    "Desarrollador / Technical Lead": [
        "dashboard", "logs", "mantenimiento", "documentacion", "reportes"
    ],
    "Analista de Soporte / NOC Analyst": [
        "dashboard", "monitoreo", "estudiantes", "carnets", "tareas", "clientes"
    ],
    "Ejecutivo de Operaciones / Legal": [
        "dashboard", "facturacion", "contratos", "pagos", "reportes_admin", "documentos"
    ],
    "Inversionista": [
        "dashboard", "inversionistas", "reportes"
    ]
}

MENU = [
    ("Dashboard", "dashboard", "/"),
    ("Gerencia", "gerencia", "/gerencia"),
    ("Contratos", "contratos", "/contratos"),
    ("Clientes / Instituciones", "clientes", "/clientes"),
    ("Facturación", "facturacion", "/facturacion"),
    ("Pagos", "pagos", "/pagos"),
    ("Equipo", "equipo", "/equipo"),
    ("Tareas", "tareas", "/tareas"),
    ("Reportes", "reportes", "/reportes"),
    ("Documentos", "documentos", "/documentos"),
    ("Usuarios", "usuarios", "/usuarios"),
    ("Roles y accesos", "accesos", "/accesos"),
    ("Logs de auditoría", "logs", "/logs"),
    ("Mantenimiento", "mantenimiento", "/mantenimiento"),
    ("Documentación técnica", "documentacion", "/documentacion"),
    ("Monitoreo colegios", "monitoreo", "/monitoreo"),
    ("Buscador estudiantes", "estudiantes", "/estudiantes"),
    ("Reimpresión carnets", "carnets", "/carnets"),
    ("Reportes administrativos", "reportes_admin", "/reportes-admin"),
    ("Inversionistas / Socios", "inversionistas", "/inversionistas"),
    ("Configuración", "configuracion", "/configuracion")
]

MODULOS = {
    "gerencia": {
        "titulo": "Gerencia",
        "boton": "Crear decisión gerencial",
        "descripcion": "Decisiones estratégicas, administrativas y financieras de LogixWare.",
        "fields": [
            {"name": "titulo", "label": "Título de la decisión", "type": "text"},
            {"name": "detalle", "label": "Detalle estratégico o administrativo", "type": "textarea"},
            {"name": "extra1", "label": "Área afectada", "type": "select", "options": ["Sistemas", "Legal", "Finanzas", "Comercial"]},
            {"name": "extra2", "label": "Impacto financiero COP", "type": "number"},
            {"name": "extra3", "label": "Responsable de ejecución", "type": "text"},
            {"name": "extra4", "label": "Fecha límite", "type": "date"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Pendiente", "En proceso", "Aprobada", "Finalizada"]}
        ],
        "columns": ["titulo", "extra1", "extra2", "extra3", "extra4", "estado"]
    },
    "clientes": {
        "titulo": "Clientes / Instituciones",
        "boton": "Crear cliente / institución",
        "descripcion": "Registro de colegios, instituciones y contactos principales.",
        "fields": [
            {"name": "titulo", "label": "Nombre del colegio / institución", "type": "text"},
            {"name": "detalle", "label": "Contacto principal", "type": "text"},
            {"name": "extra1", "label": "Teléfono", "type": "text"},
            {"name": "extra2", "label": "Correo", "type": "email"},
            {"name": "extra3", "label": "Ciudad / sede", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Activo", "Inactivo", "En negociación"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"]
    },
    "facturacion": {
        "titulo": "Facturación",
        "boton": "Crear factura",
        "descripcion": "Control de facturas, vencimientos y cobros a instituciones.",
        "fields": [
            {"name": "titulo", "label": "Concepto de factura", "type": "text"},
            {"name": "detalle", "label": "Cliente / Institución", "type": "text"},
            {"name": "extra1", "label": "Valor total COP", "type": "number"},
            {"name": "extra2", "label": "Fecha de emisión", "type": "date"},
            {"name": "extra3", "label": "Fecha de vencimiento", "type": "date"},
            {"name": "extra4", "label": "Método de pago esperado", "type": "select", "options": ["Nequi", "Transferencia Bancaria", "PSE"]},
            {"name": "estado", "label": "Estado del cobro", "type": "select", "options": ["Borrador", "Pendiente de pago", "Pagada", "Vencida"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "extra4", "estado"]
    },
    "pagos": {
        "titulo": "Pagos",
        "boton": "Registrar pago",
        "descripcion": "Pagos recibidos por servicios, licencias y contratos.",
        "fields": [
            {"name": "titulo", "label": "Cliente que pagó", "type": "text"},
            {"name": "detalle", "label": "Concepto pagado", "type": "text"},
            {"name": "extra1", "label": "Valor pagado COP", "type": "number"},
            {"name": "extra2", "label": "Método de pago", "type": "select", "options": ["Nequi", "Transferencia Bancaria", "PSE", "Efectivo"]},
            {"name": "extra3", "label": "Fecha del pago", "type": "date"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Confirmado", "Pendiente de verificar", "Rechazado"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"]
    },
    "documentacion": {
        "titulo": "Documentación técnica",
        "boton": "Crear documento técnico",
        "descripcion": "Manuales de código, PostgreSQL, Railway, APIs y diseño Liquid Glass.",
        "fields": [
            {"name": "titulo", "label": "Título del documento", "type": "text"},
            {"name": "detalle", "label": "Contenido / descripción técnica", "type": "textarea"},
            {"name": "extra1", "label": "Categoría", "type": "select", "options": ["Código", "PostgreSQL", "Railway", "APIs", "Liquid Glass", "Despliegue"]},
            {"name": "extra2", "label": "Responsable", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Borrador", "Revisado", "Publicado"]}
        ],
        "columns": ["titulo", "extra1", "extra2", "estado"]
    },
    "monitoreo": {
        "titulo": "Monitoreo colegios",
        "boton": "Registrar nodo / colegio",
        "descripcion": "Estado de lectores QR, sincronización y actividad diaria.",
        "fields": [
            {"name": "titulo", "label": "Nombre del colegio", "type": "text"},
            {"name": "detalle", "label": "Última sincronización de portería", "type": "text"},
            {"name": "extra1", "label": "Estado del servidor", "type": "select", "options": ["Online", "Offline", "Intermitente"]},
            {"name": "extra2", "label": "Alumnos activos hoy", "type": "number"},
            {"name": "extra3", "label": "Observación técnica", "type": "text"},
            {"name": "estado", "label": "Prioridad", "type": "select", "options": ["Normal", "Media", "Alta", "Crítica"]}
        ],
        "columns": ["titulo", "extra1", "detalle", "extra2", "estado"]
    },
    "estudiantes": {
        "titulo": "Buscador estudiantes",
        "boton": "Registrar estudiante",
        "descripcion": "Búsqueda global por documento, código o institución.",
        "fields": [
            {"name": "titulo", "label": "Nombre del estudiante", "type": "text"},
            {"name": "detalle", "label": "Documento o código", "type": "text"},
            {"name": "extra1", "label": "Institución", "type": "text"},
            {"name": "extra2", "label": "Grado", "type": "text"},
            {"name": "extra3", "label": "Acudiente / teléfono", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Activo", "Inactivo", "Bloqueado"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "estado"]
    },
    "carnets": {
        "titulo": "Reimpresión carnets",
        "boton": "Crear solicitud de carnet",
        "descripcion": "Historial de solicitudes de QR y carnets de reemplazo.",
        "fields": [
            {"name": "titulo", "label": "Nombre del alumno", "type": "text"},
            {"name": "detalle", "label": "Colegio", "type": "text"},
            {"name": "extra1", "label": "Grado", "type": "text"},
            {"name": "extra2", "label": "Motivo de reimpresión", "type": "select", "options": ["Pérdida", "Daño", "Cambio de datos", "Reposición"]},
            {"name": "extra3", "label": "Documento del estudiante", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Solicitado", "Generado", "Entregado"]}
        ],
        "columns": ["detalle", "titulo", "extra1", "extra2", "estado"]
    },
    "inversionistas": {
        "titulo": "Inversionistas / Socios",
        "boton": "Registrar movimiento societario",
        "descripcion": "Aportes, capital, contratos de sociedad y utilidades.",
        "fields": [
            {"name": "titulo", "label": "Socio / inversionista", "type": "text"},
            {"name": "detalle", "label": "Concepto", "type": "text"},
            {"name": "extra1", "label": "Aporte o capital COP", "type": "number"},
            {"name": "extra2", "label": "Porcentaje de participación", "type": "number"},
            {"name": "extra3", "label": "Documento asociado", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Activo", "Pendiente", "Cerrado"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "estado"]
    },
    "reportes": {
        "titulo": "Reportes",
        "boton": "Crear reporte",
        "descripcion": "Filtros, métricas y exportaciones para análisis operativo.",
        "fields": [
            {"name": "titulo", "label": "Nombre del reporte", "type": "text"},
            {"name": "detalle", "label": "Institución", "type": "text"},
            {"name": "extra1", "label": "Desde", "type": "date"},
            {"name": "extra2", "label": "Hasta", "type": "date"},
            {"name": "extra3", "label": "Tipo de reporte", "type": "select", "options": ["Financiero", "Soporte Técnico", "Rendimiento de Asistencia"]},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Generado", "Pendiente", "Archivado"]}
        ],
        "columns": ["titulo", "extra3", "detalle", "extra1", "extra2", "estado"]
    },
    "reportes_admin": {
        "titulo": "Reportes administrativos",
        "boton": "Crear reporte administrativo",
        "descripcion": "Ingresos, cuentas por cobrar, gastos, margen y estabilidad.",
        "fields": [
            {"name": "titulo", "label": "Nombre del reporte", "type": "text"},
            {"name": "detalle", "label": "Institución o consolidado", "type": "text"},
            {"name": "extra1", "label": "Ingresos brutos COP", "type": "number"},
            {"name": "extra2", "label": "Cuentas por cobrar COP", "type": "number"},
            {"name": "extra3", "label": "Gastos de operación COP", "type": "number"},
            {"name": "extra4", "label": "Margen neto COP", "type": "number"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Borrador", "Final", "Presentado"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "extra3", "extra4", "estado"]
    },
    "equipo": {
        "titulo": "Equipo",
        "boton": "Agregar miembro",
        "descripcion": "Equipo interno, responsabilidades y cargos.",
        "fields": [
            {"name": "titulo", "label": "Nombre completo", "type": "text"},
            {"name": "detalle", "label": "Cargo", "type": "text"},
            {"name": "extra1", "label": "Correo", "type": "email"},
            {"name": "extra2", "label": "Teléfono", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Activo", "Inactivo"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "extra2", "estado"]
    },
    "tareas": {
        "titulo": "Tareas",
        "boton": "Crear tarea",
        "descripcion": "Tareas operativas y administrativas.",
        "fields": [
            {"name": "titulo", "label": "Título de la tarea", "type": "text"},
            {"name": "detalle", "label": "Descripción", "type": "textarea"},
            {"name": "extra1", "label": "Responsable", "type": "text"},
            {"name": "extra2", "label": "Fecha límite", "type": "date"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Pendiente", "En proceso", "Finalizada"]}
        ],
        "columns": ["titulo", "extra1", "extra2", "estado"]
    },
    "documentos": {
        "titulo": "Documentos",
        "boton": "Registrar documento",
        "descripcion": "Contratos, soportes, archivos y documentos legales.",
        "fields": [
            {"name": "titulo", "label": "Nombre del documento", "type": "text"},
            {"name": "detalle", "label": "Descripción", "type": "textarea"},
            {"name": "extra1", "label": "Tipo", "type": "select", "options": ["Contrato", "Factura", "Soporte", "Legal", "Técnico"]},
            {"name": "extra2", "label": "Responsable", "type": "text"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Vigente", "Archivado", "Pendiente"]}
        ],
        "columns": ["titulo", "extra1", "extra2", "estado"]
    },
    "mantenimiento": {
        "titulo": "Mantenimiento",
        "boton": "Crear acción de mantenimiento",
        "descripcion": "Modo mantenimiento, despliegues, cambios y revisión del sistema.",
        "fields": [
            {"name": "titulo", "label": "Acción de mantenimiento", "type": "text"},
            {"name": "detalle", "label": "Detalle técnico", "type": "textarea"},
            {"name": "extra1", "label": "Responsable", "type": "text"},
            {"name": "extra2", "label": "Fecha programada", "type": "date"},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Programado", "En ejecución", "Finalizado"]}
        ],
        "columns": ["titulo", "extra1", "extra2", "estado"]
    },
    "configuracion": {
        "titulo": "Configuración",
        "boton": "Crear ajuste",
        "descripcion": "Parámetros generales del sistema.",
        "fields": [
            {"name": "titulo", "label": "Nombre del ajuste", "type": "text"},
            {"name": "detalle", "label": "Valor o descripción", "type": "text"},
            {"name": "extra1", "label": "Área", "type": "select", "options": ["Sistema", "Usuarios", "Diseño", "Seguridad", "Facturación"]},
            {"name": "estado", "label": "Estado", "type": "select", "options": ["Activo", "Inactivo"]}
        ],
        "columns": ["titulo", "detalle", "extra1", "estado"]
    }
}

SLUGS = {"reportes-admin": "reportes_admin"}

# Clase Adaptadora para unificar consultas SQLite y PostgreSQL
class EnvoltorioFila:
    def __init__(self, data_dict):
        self._data = data_dict
    def __getitem__(self, key):
        return self._data.get(key)
    def keys(self):
        return self._data.keys()

class WrapperConexion:
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres
    def execute(self, query, params=()):
        if self.is_postgres:
            # Reemplazar los '?' de SQLite por '%s' de PostgreSQL
            query = query.replace('?', '%s')
            # Manejo del AUTOINCREMENT implícito en Postgres SERIAL/BIGSERIAL
            if "AUTOINCREMENT" in query:
                query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()

def get_db():
    global DATABASE_URL
    if DATABASE_URL:
        # Corrección por si Railway inyecta postgres:// hely de postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return WrapperConexion(conn, is_postgres=True)
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return WrapperConexion(conn, is_postgres=False)

def add_column_if_missing(conn, table, column):
    if conn.is_postgres:
        cursor = conn.conn.cursor()
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='{table}' AND column_name='{column}'
        """)
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
    else:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")

def init_db():
    conn = get_db()
    
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT NOT NULL,
        estado TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS contratos (
        id SERIAL PRIMARY KEY,
        institucion TEXT NOT NULL,
        sistema TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_vencimiento TEXT NOT NULL,
        valor TEXT NOT NULL,
        estado TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS auditoria (
        id SERIAL PRIMARY KEY,
        fecha TEXT NOT NULL,
        usuario TEXT NOT NULL,
        accion TEXT NOT NULL,
        modulo TEXT NOT NULL,
        resultado TEXT NOT NULL
    )""")

    conn.execute("""CREATE TABLE IF NOT EXISTS registros (
        id SERIAL PRIMARY KEY,
        modulo TEXT NOT NULL,
        titulo TEXT,
        detalle TEXT,
        estado TEXT,
        fecha TEXT
    )""")

    for col in ["extra1", "extra2", "extra3", "extra4", "extra5", "extra6"]:
        add_column_if_missing(conn, "registros", col)

    usuarios_base = [
        ("Sebastián", "admin", "1234", "Administrador", "Activo"),
        ("Gerencia General", "gerencia", "1234", "Gerencia", "Activo"),
        ("Juan Camilo", "juan", "1234", "Desarrollador / Technical Lead", "Activo"),
        ("Laura NOC", "laura", "1234", "Analista de Soporte / NOC Analyst", "Activo"),
        ("Martha Legal", "martha", "1234", "Ejecutivo de Operaciones / Legal", "Activo"),
        ("Carlos Inversionista", "carlos", "1234", "Inversionista", "Activo")
    ]

    for u in usuarios_base:
        existe = conn.execute("SELECT id FROM usuarios WHERE usuario=?", (u[1],)).fetchone()
        if not existe:
            conn.execute("INSERT INTO usuarios (nombre, usuario, password, rol, estado) VALUES (?, ?, ?, ?, ?)", u)

    conn.commit()
    conn.close()

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
    except:
        return value or ""

def obtener_registros(modulo):
    conn = get_db()
    registros = conn.execute("SELECT * FROM registros WHERE modulo=? ORDER BY id DESC", (modulo,)).fetchall()
    conn.close()
    return registros

def obtener_contrato(id):
    conn = get_db()
    contrato = conn.execute("SELECT * FROM contratos WHERE id=?", (id,)).fetchone()
    conn.close()
    return contrato

def encabezado_pdf(elements, styles):
    logo_path = os.path.join(app.root_path, "static", "img", "logo.png")

    titulo = ParagraphStyle(
        "titulo_membrete",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20
    )

    centro = ParagraphStyle(
        "centro_membrete",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12
    )

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=75, height=75)
    else:
        logo = Paragraph("", styles["Normal"])

    texto = [
        Paragraph("<b>LOGIXWARE</b>", titulo),
        Paragraph("SEDE PRINCIPAL", centro),
        Paragraph("Resolución institucional demo 2026", centro),
        Paragraph("DANE: 199999999999 | NIT: 900.999.999-1", centro),
        Paragraph("Dirección: Calle 20#17-99 CARACOLI-ANTIQUIA., Colombia", centro),
        Paragraph(f"Fecha de impresión: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", centro)
    ]

    tabla = Table(
        [[logo, texto, ""]],
        colWidths=[1.4 * inch, 7.2 * inch, 1.4 * inch]
    )

    tabla.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
    ]))

    elements.append(tabla)
    elements.append(Spacer(1, 24))

def crear_pdf(modulo, registros):
    config = MODULOS[modulo]
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=28,
        leftMargin=28,
        topMargin=24,
        bottomMargin=24
    )

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

            if "valor" in etiqueta or "cop" in etiqueta or "financiero" in etiqueta or "capital" in etiqueta:
                valor = money(valor)

            fila.append(valor)

        fila.append(str(r["fecha"] or ""))
        data.append(fila)

    if len(data) == 1:
        data.append(["SIN REGISTROS"] + [""] * (len(headers) - 1))

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.yellow),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return buffer

def crear_contrato_pdf(contrato, tipo="copia"):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=28,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        "normal_contrato",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        alignment=TA_LEFT
    )

    titulo = ParagraphStyle(
        "titulo_contrato",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=15
    )

    elements = []
    encabezado_pdf(elements, styles)

    titulo_tipo = "COPIA DE CONTRATO" if tipo == "copia" else "CONTRATO ORIGINAL"
    elements.append(Paragraph(f"<b>{titulo_tipo}</b>", titulo))
    elements.append(Spacer(1, 18))

    texto = f"""
    Entre <b>LogixWare</b>, sistema interno empresarial para soluciones tecnológicas educativas,
    y la institución <b>{contrato['institucion']}</b>, se deja constancia del contrato asociado al
    sistema <b>{contrato['sistema']}</b>.
    <br/><br/>
    <b>Fecha de inicio:</b> {contrato['fecha_inicio']}<br/>
    <b>Fecha de vencimiento:</b> {contrato['fecha_vencimiento']}<br/>
    <b>Valor del contrato:</b> {money(contrato['valor'])}<br/>
    <b>Estado:</b> {contrato['estado']}<br/><br/>
    Este documento se genera como soporte formal para control administrativo, facturación,
    seguimiento operativo y archivo institucional.
    <br/><br/>
    El presente documento puede ser usado como copia de consulta o como original interno según
    el tipo de descarga seleccionada en el sistema.
    """

    elements.append(Paragraph(texto, normal))
    elements.append(Spacer(1, 50))

    firmas = Table([
        ["______________________________", "______________________________"],
        ["Representante LogixWare", "Representante Institución"],
    ], colWidths=[3.4 * inch, 3.4 * inch])

    firmas.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(firmas)
    doc.build(firmas)

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

def logo_base64():
    logo_path = os.path.join(app.root_path, "static", "img", "logo.png")

    if not os.path.exists(logo_path):
        return ""

    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/png;base64,{encoded}"

def crear_word_html(modulo, registros):
    config = MODULOS[modulo]
    headers = [label_for(config, col).upper() for col in config["columns"]] + ["FECHA"]

    rows = ""

    for r in registros:
        rows += "<tr>"

        for col in config["columns"]:
            valor = str(r[col] or "")
            etiqueta = label_for(config, col).lower()

            if "valor" in etiqueta or "cop" in etiqueta or "financiero" in etiqueta or "capital" in etiqueta:
                valor = money(valor)

            rows += f"<td>{valor}</td>"

        rows += f"<td>{r['fecha'] or ''}</td>"
        rows += "</tr>"

    if not rows:
        rows = f"<tr><td colspan='{len(headers)}'>SIN REGISTROS</td></tr>"

    logo = logo_base64()

    html = f"""
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{
          font-family: Arial, Helvetica, sans-serif;
          color: #000;
        }}

        .header {{
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 35px;
        }}

        .header td {{
          border: none;
        }}

        .logo {{
          width: 120px;
          text-align: center;
        }}

        .logo img {{
          width: 90px;
          height: 90px;
          object-fit: contain;
        }}

        .info {{
          text-align: center;
          font-size: 13px;
        }}

        .info h1 {{
          font-size: 22px;
          margin: 0 0 8px;
          font-weight: bold;
        }}

        h2 {{
          margin-top: 30px;
          font-size: 20px;
        }}

        .tabla-datos {{
          width: 100%;
          border-collapse: collapse;
          margin-top: 40px;
          font-size: 12px;
        }}

        .tabla-datos th {{
          background: #ffff00;
          color: #000000;
          border: 1px solid #000;
          padding: 8px;
          font-weight: bold;
          text-align: center;
        }}

        .tabla-datos td {{
          border: 1px solid #000;
          padding: 8px;
          text-align: center;
        }}
      </style>
    </head>

    <body>
      <table class="header">
        <tr>
          <td class="logo">
            <img src="{logo}">
          </td>

          <td class="info">
            <h1>LOGIXWARE</h1>
            <div>SEDE PRINCIPAL</div>
            <div>Resolución institucional demo 2026</div>
            <div>DANE: 199999999999 | NIT: 900.999.999-1</div>
            <div>Dirección: Calle 20#17-99 CARACOLI-ANTIQUIA., Colombia</div>
            <div>Fecha de impresión: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
          </td>

          <td style="width:120px;"></td>
        </tr>
      </table>

      <h2>{config['titulo'].upper()}</h2>

      <table class="tabla-datos">
        <tr>
          {''.join(f'<th>{h}</th>' for h in headers)}
        </tr>

        {rows}
      </table>
    </body>
    </html>
    """

    return html

@app.context_processor
def globales():
    permisos = ROLES.get(session.get("rol", ""), [])
    return {
        "nombre_actual": session.get("nombre", ""),
        "rol_actual": session.get("rol", ""),
        "menu_visible": [m for m in MENU if m[1] in permisos],
        "permisos": permisos
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND password=? AND estado='Activo'",
            (request.form["usuario"], request.form["password"])
        ).fetchone()
        conn.close()

        if user:
            session["user"] = user["usuario"]
            session["nombre"] = user["nombre"]
            session["rol"] = user["rol"]
            auditar("Inicio de sesión", "Login")
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

@app.route("/logout")
def logout():
    auditar("Cierre de sesión", "Login")
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    if not protegido():
        return redirect(url_for("login"))

    conn = get_db()
    contratos = conn.execute("SELECT * FROM contratos ORDER BY id DESC LIMIT 5").fetchall()
    total_contratos = conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    total_usuarios = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        contratos=contratos,
        total_contratos=total_contratos,
        total_usuarios=total_usuarios
    )

@app.route("/sin-permiso")
def sin_permiso():
    return render_template(
        "modulo.html",
        titulo="Acceso denegado",
        descripcion="No tienes permisos para entrar a esta sección."
    )

@app.route("/logs")
def logs():
    bloqueo = validar_acceso("logs")
    if bloqueo:
        return bloqueo

    conn = get_db()
    logs = conn.execute("SELECT * FROM auditoria ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    return render_template("logs.html", logs=logs)

@app.route("/accesos")
def accesos():
    bloqueo = validar_acceso("accesos")
    if bloqueo:
        return bloqueo

    return render_template("accesos.html", roles=ROLES)

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
        try:
            conn.execute(
                "INSERT INTO usuarios (nombre, usuario, password, rol, estado) VALUES (?, ?, ?, ?, ?)",
                (
                    request.form["nombre"],
                    request.form["usuario"],
                    request.form["password"],
                    request.form["rol"],
                    request.form["estado"]
                )
            )
            conn.commit()
            auditar("Crear usuario", "Usuarios")
        except Exception as e:
            print(f"Error al guardar usuario: {e}")
        finally:
            conn.close()
        return redirect(url_for("usuarios"))

    return render_template("nuevo_usuario.html")

# Inicializar Base de Datos al arrancar la App
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)