import sqlite3
import os
import streamlit as st
import pandas as pd

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
    # 1. Crear esquemas de todas las tablas
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clanes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                sigla TEXT,
                logo_path TEXT,
                descripcion TEXT,
                estado TEXT DEFAULT 'Activo'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ciclos_inmortales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_desde TEXT NOT NULL,
                fecha_hasta TEXT,
                estado TEXT CHECK(estado IN ('Activo', 'Finalizado')) NOT NULL DEFAULT 'Activo'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE
            )
        ''')
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
    except Exception:
        pass

    # 1b. Inicializar Clanes por defecto si la tabla está vacía
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clanes")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO clanes (id, nombre, sigla, logo_path, descripcion, estado)
                VALUES (1, 'ÐÛΝΞÐΛIN', 'DUN', 'Logo1.jpeg', 'Clan Principal', 'Activo')
            """)
            cursor.execute("""
                INSERT INTO clanes (id, nombre, sigla, logo_path, descripcion, estado)
                VALUES (2, 'Segundo Clan', 'CLAN2', 'Diablo Inmortal.png', 'Clan Secundario', 'Activo')
            """)
        conn.commit()
        conn.close()
    except Exception:
        pass
        
    # 2. Modificaciones de columnas en miembros (ALTER TABLE)
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='miembros'")
        miembros_exists = cursor.fetchone() is not None
        if miembros_exists:
            cursor.execute("SELECT * FROM miembros LIMIT 0")
            columnas_existentes = {col[0].lower() for col in cursor.description}
            
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
                ("rango_sombra", "TEXT"),
                ("clan_id", "INTEGER DEFAULT 1")
            ]
            for col_name, col_type in columnas_nuevas:
                if col_name.lower() not in columnas_existentes:
                    try:
                        cursor.execute(f"ALTER TABLE miembros ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass
            # Asegurar que miembros sin clan asignado apunten al Clan 1
            cursor.execute("UPDATE miembros SET clan_id = 1 WHERE clan_id IS NULL")
        conn.commit()
        conn.close()
    except Exception:
        pass

    # 3. Modificaciones de columnas en asistencia
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='asistencia'")
        if cursor.fetchone() is not None:
            cursor.execute("SELECT * FROM asistencia LIMIT 0")
            columnas_existentes = {col[0].lower() for col in cursor.description}
            columnas_asistencia = [
                ("intencion", "TEXT DEFAULT 'No votó'"),
                ("asistio_realmente", "INTEGER DEFAULT 0"),
                ("sala_asignada", "TEXT DEFAULT 'No asignado'"),
                ("habilidad", "TEXT DEFAULT 'Seleccione'")
            ]
            for col_name, col_type in columnas_asistencia:
                if col_name.lower() not in columnas_existentes:
                    try:
                        cursor.execute(f"ALTER TABLE asistencia ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass
        conn.commit()
        conn.close()
    except Exception:
        pass

    # 4. Modificaciones de columnas en estadisticas_guerra
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='estadisticas_guerra'")
        if cursor.fetchone() is not None:
            cursor.execute("SELECT * FROM estadisticas_guerra LIMIT 0")
            columnas_existentes = {col[0].lower() for col in cursor.description}
            columnas_stats = [
                ("evento_id", "INTEGER"),
                ("fecha", "DATE")
            ]
            for col_name, col_type in columnas_stats:
                if col_name.lower() not in columnas_existentes:
                    try:
                        cursor.execute(f"ALTER TABLE estadisticas_guerra ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass
        conn.commit()
        conn.close()
    except Exception:
        pass

    # 4b. Modificaciones de columnas en usuarios y asignación de superadmin
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if cursor.fetchone() is not None:
            cursor.execute("SELECT * FROM usuarios LIMIT 0")
            cols_usuarios = {col[0].lower() for col in cursor.description}
            if "clan_id" not in cols_usuarios:
                try:
                    cursor.execute("ALTER TABLE usuarios ADD COLUMN clan_id INTEGER DEFAULT 1")
                except Exception:
                    pass
            cursor.execute("UPDATE usuarios SET clan_id = 1 WHERE clan_id IS NULL")
            # Promover a Tuku03 a superadmin si existe
            cursor.execute("UPDATE usuarios SET rol = 'superadmin' WHERE LOWER(usuario) = 'tuku03'")
        conn.commit()
        conn.close()
    except Exception:
        pass
        
    # 5. Inicialización de datos por defecto (clases)
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clases")
        if cursor.fetchone()[0] == 0:
            clases_defecto = [
                "Bárbaro", "Guerrero Divino", "Cazador de Demonios", "Monje", "Nigromante",
                "Arcanista", "Caballero Sangriento", "Tempestario", "Druida", "Brujo", "Desconocida"
            ]
            cursor.executemany("INSERT INTO clases (nombre) VALUES (?)", [(c,) for c in clases_defecto])
        conn.commit()
        conn.close()
    except Exception:
        pass


# Inicializar base de datos
preparar_db()


@st.cache_data(ttl=60)
def obtener_clanes():
    conexion = conectar_bd()
    df = pd.read_sql_query("SELECT id, nombre, sigla, logo_path, descripcion, estado FROM clanes WHERE estado = 'Activo' ORDER BY id", conexion)
    conexion.close()
    return df


def obtener_clan_por_id(clan_id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, sigla, logo_path, descripcion, estado FROM clanes WHERE id = ?", (int(clan_id),))
    row = cursor.fetchone()
    conexion.close()
    if row:
        return {
            "id": row[0],
            "nombre": row[1],
            "sigla": row[2],
            "logo_path": row[3],
            "descripcion": row[4],
            "estado": row[5]
        }
    return None


def actualizar_clan(clan_id, nombre, sigla, logo_path=None, descripcion=""):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    if logo_path:
        cursor.execute(
            "UPDATE clanes SET nombre = ?, sigla = ?, logo_path = ?, descripcion = ? WHERE id = ?",
            (nombre, sigla, logo_path, descripcion, int(clan_id))
        )
    else:
        cursor.execute(
            "UPDATE clanes SET nombre = ?, sigla = ?, descripcion = ? WHERE id = ?",
            (nombre, sigla, descripcion, int(clan_id))
        )
    conexion.commit()
    conexion.close()
    st.cache_data.clear()


def rotar_miembro_clan(miembro_id, clan_destino_id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE miembros SET clan_id = ? WHERE id = ?",
        (int(clan_destino_id), int(miembro_id))
    )
    conexion.commit()
    conexion.close()
    st.cache_data.clear()


@st.cache_data(ttl=60)
def obtener_roster_activos(clan_id=None):
    if clan_id is None:
        try:
            clan_id = st.session_state.get('clan_id', 1)
        except Exception:
            clan_id = 1
    conexion = conectar_bd()
    df = pd.read_sql_query(
        "SELECT id, nombre, clase, resonancia, ic, telefono, clan_id FROM miembros WHERE estado='Activo' AND clan_id = ? ORDER BY nombre",
        conexion,
        params=(int(clan_id),)
    )
    conexion.close()
    return df


@st.cache_data(ttl=60)
def obtener_eventos():
    conexion = conectar_bd()
    df = pd.read_sql_query("SELECT id, nombre FROM eventos", conexion)
    conexion.close()
    return df


@st.cache_data(ttl=60)
def obtener_clases():
    conexion = conectar_bd()
    df = pd.read_sql_query("SELECT id, nombre FROM clases ORDER BY id", conexion)
    conexion.close()
    return df


@st.cache_data(ttl=60)
def obtener_ciclo_activo():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha_desde, estado FROM ciclos_inmortales WHERE estado = 'Activo'")
    res = cursor.fetchone()
    conn.close()
    return res


OPCIONES_TELEFONO = [
    "🇦🇷 +54",   # Argentina
    "🇧🇴 +591",  # Bolivia
    "🇧🇷 +55",   # Brasil
    "🇨🇱 +56",   # Chile
    "🇨🇴 +57",   # Colombia
    "🇪🇨 +593",  # Ecuador
    "🇪🇸 +34",   # España
    "🇬🇾 +592",  # Guyana
    "🇲🇽 +52",   # México
    "🇵🇾 +595",  # Paraguay
    "🇵🇪 +51",   # Perú
    "🇵🇹 +351",  # Portugal
    "🇸🇷 +597",  # Surinam
    "🇺🇾 +598",  # Uruguay
    "🇻🇪 +58"    # Venezuela
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
    code_mappings = []
    for idx, opt in enumerate(OPCIONES_TELEFONO):
        parts = opt.split()
        if len(parts) >= 2:
            code_mappings.append((idx, opt, parts[-1]))
    code_mappings.sort(key=lambda x: len(x[2]), reverse=True)
    
    for idx, opt, code in code_mappings:
        if telefono_str.startswith(code):
            return idx, telefono_str[len(code):].strip()
            
    return 0, telefono_str
