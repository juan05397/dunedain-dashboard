import sqlite3


def conectar_bd():
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
        except sqlite3.OperationalError:
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
