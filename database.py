import sqlite3
import os
import streamlit as st

def conectar_bd():
    db_url = None
    db_token = None
    
    # 1. Intentar obtener credenciales de Turso desde st.secrets
    try:
        if "TURSO_DATABASE_URL" in st.secrets:
            db_url = st.secrets["TURSO_DATABASE_URL"]
        if "TURSO_AUTH_TOKEN" in st.secrets:
            db_token = st.secrets["TURSO_AUTH_TOKEN"]
    except Exception:
        pass
        
    # 2. Fallback a variables de entorno si st.secrets no está disponible
    if not db_url:
        db_url = os.environ.get("TURSO_DATABASE_URL")
    if not db_token:
        db_token = os.environ.get("TURSO_AUTH_TOKEN")
        
    # 3. Si tenemos las credenciales, intentamos conectar a Turso usando libsql
    if db_url and db_token:
        try:
            import libsql
            conn = libsql.connect(database=db_url, auth_token=db_token)
            try:
                conn.execute("PRAGMA foreign_keys = ON")
            except Exception:
                pass
            return conn
        except Exception as e:
            try:
                st.warning(f"⚠️ Error al conectar a Turso: {e}. Usando base de datos local como fallback.")
            except Exception:
                print(f"Error al conectar a Turso: {e}. Usando base de datos local.")
                
    # 4. Fallback local a SQLite
    conn = sqlite3.connect('clan_dunedain.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def preparar_db():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ciclos_inmortales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_desde TEXT NOT NULL,
            fecha_hasta TEXT,
            estado TEXT CHECK(estado IN ('Activo', 'Finalizado')) NOT NULL DEFAULT 'Activo'
        )
    ''')
    
    # Columnas nuevas de gestión, auditoría e histórica de PvP
    columnas_nuevas = [
        ("alta_realizada_por", "TEXT"),
        ("baja_realizada_por", "TEXT"),
        ("motivo_baja", "TEXT"),
        ("armadura", "INTEGER"),
        ("penetracion_armadura", "INTEGER"),
        ("potencia", "INTEGER"),
        ("resistencia", "INTEGER"),
        ("velocidad_ataque", "TEXT"),
        ("reduccion_recuperacion", "TEXT"),
        ("duracion_beneficiosos", "TEXT"),
        ("rango_sombra", "TEXT")
    ]
    for col_name, col_type in columnas_nuevas:
        try:
            cursor.execute(f"ALTER TABLE miembros ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass
            
    # Crear e inicializar la tabla de clases
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM clases")
    if cursor.fetchone()[0] == 0:
        clases_defecto = [
            "Bárbaro", "Guerrero Divino", "Cazador de Demonios", "Monje", "Nigromante",
            "Arcanista", "Caballero Sangriento", "Tempestario", "Druida", "Brujo", "Desconocida"
        ]
        cursor.executemany("INSERT INTO clases (nombre) VALUES (?)", [(c,) for c in clases_defecto])
        
    # Crear la tabla de alias de WhatsApp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alias_whatsapp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            whatsapp_name TEXT UNIQUE,
            miembro_id INTEGER,
            FOREIGN KEY (miembro_id) REFERENCES miembros(id) ON DELETE CASCADE
        )
    ''')
            
    conn.commit()
    conn.close()


# Inicializar base de datos
preparar_db()


def obtener_ciclo_activo():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha_desde, estado FROM ciclos_inmortales WHERE estado = 'Activo'")
    res = cursor.fetchone()
    conn.close()
    return res


OPCIONES_TELEFONO = [
    "🇦🇷 +54",  # Argentina
    "🇧🇴 +591", # Bolivia
    "🇧🇷 +55",  # Brasil
    "🇨🇱 +56",  # Chile
    "🇨🇴 +57",  # Colombia
    "🇪🇨 +593", # Ecuador
    "🇬🇾 +592", # Guyana
    "🇵🇾 +595", # Paraguay
    "🇵🇪 +51",  # Perú
    "🇸🇷 +597", # Surinam
    "🇺🇾 +598", # Uruguay
    "🇻🇪 +58"   # Venezuela
]


def parsear_telefono(telefono_str):
    if not telefono_str:
        return 0, ""
    
    telefono_str = str(telefono_str).strip()
    
    # Primero: buscar si comienza exactamente con alguna de las opciones del selectbox
    for idx, opt in enumerate(OPCIONES_TELEFONO):
        if telefono_str.startswith(opt):
            return idx, telefono_str[len(opt):].strip()
            
    # Segundo: buscar si comienza con el código numérico directamente (ej. "+51")
    # Se ordena de mayor a menor longitud de código para evitar colisiones (ej. "+591" antes de "+51")
    code_mappings = []
    for idx, opt in enumerate(OPCIONES_TELEFONO):
        parts = opt.split()
        if len(parts) >= 2:
            code_mappings.append((idx, opt, parts[-1]))
    code_mappings.sort(key=lambda x: len(x[2]), reverse=True)
    
    for idx, opt, code in code_mappings:
        if telefono_str.startswith(code):
            return idx, telefono_str[len(code):].strip()
            
    # Valor por defecto: índice 0 (Argentina) y retornamos el string completo
    return 0, telefono_str

