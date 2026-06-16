import sqlite3

# Conectar a tu base de datos local
conexion = sqlite3.connect('clan_dunedain.db')

# Activar el modo WAL
conexion.execute('PRAGMA journal_mode = WAL;')

# Guardar y cerrar
conexion.close()

print("✅ ¡Modo WAL activado con éxito! Tu base de datos ya está lista para Turso.")
