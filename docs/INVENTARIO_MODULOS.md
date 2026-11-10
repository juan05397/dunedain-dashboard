# 📦 Inventario de Módulos y Mapa de Dependencias As-Is
**Proyecto:** Relevamiento Funcional para Migración a Arquitectura Modular  
**Sistema:** Dunedain Dashboard (Gestión de Clan Diablo Immortal)  
**Fecha:** 2026-09-06  
**Estado:** 🟡 Borrador Inicial para Aprobación de Orden de Trabajo  

---

## 1. Módulos Propuestos y Responsabilidad Funcional Tentativa

### M01: Núcleo de Persistencia y Ciclos Inmortales
* **Archivos:** `database.py`, `modulos/ciclo_inmortal.py`
* **Entidades DB:** `ciclos_inmortales`, `eventos`, `clases`
* **Responsabilidad:** Conexión a Turso/libSQL con fallback local a SQLite. Inicialización de esquemas (`preparar_db`). Gestión del ciclo temporal del servidor ('Activo' / 'Finalizado'). Es el ancla temporal de todas las estadísticas y asistencias.

### M02: Seguridad, Autenticación y Usuarios
* **Archivos:** `app.py` (líneas 83-198), `modulos/admin_usuarios.py`
* **Entidades DB:** `usuarios`
* **Responsabilidad:** Control de acceso, login con hash de contraseñas (`werkzeug.security`), política de cambio obligatorio de contraseña en primer ingreso (`debe_cambiar_pass = 1`), roles de sistema (`admin` vs `usuario`), CRUD y blanqueo de contraseñas de operadores.

### M03: Gestión de Miembros (Roster, Altas, Bajas y Clases)
* **Archivos:** `modulos/alta_baja.py`, `modulos/admin_clases.py`
* **Entidades DB:** `miembros`, `clases`, `alias_whatsapp`
* **Responsabilidad:** Ciclo de vida de los jugadores del clan: Alta manual, reactivación de ex-miembros, baja con motivo formal, carga masiva vía CSV/Excel, actualización de estadísticas de combate (Resonancia, IC, Atributos Secundarios, Rango Sombra) y catálogo de clases de Diablo Immortal.

### M04: Control Maestro de Asistencia y Auditoría
* **Archivos:** `modulos/asistencia.py`
* **Entidades DB:** `asistencia`, `miembros`, `eventos`, `ciclos_inmortales`
* **Responsabilidad:** Registro masivo de intenciones de voto (WhatsApp) y asistencia real in-game por evento/fecha/ciclo. Precálculo de alertas por acumulación de inasistencias (>=3). Sábana matricial estilo Excel cruzando votos y realidad (OK, Fantasma, Infracción, Justificado, Duda, Ausente) y exportación a CSV.

### M05: Táctica y Armador de Salas de Guerra
* **Archivos:** `modulos/armador_salas.py`
* **Entidades DB:** Consulta `asistencia`, `miembros`, `eventos`
* **Responsabilidad:** Distribución táctica de jugadores en salas de guerra (Sublime, Eminente, Célebre, Imponente) con capacidad máxima de 8 por sala. Asignación de habilidades. Detección de duplicados. Generador de mensajes personalizados para WhatsApp/Discord segmentados por evento (Guerra 19:30 hs vs Vigilia/Rito 20:00 hs) y exportación en archivo de texto.

### M06: Régimen Disciplinario: Sanciones y Advertencias
* **Archivos:** `modulos/sanciones.py`
* **Entidades DB:** `sanciones`, `tipos_sancion`, `miembros`
* **Responsabilidad:** Imputación de sanciones disciplinarias a miembros, catálogo de tipos de sanción, consulta de historial sancionatorio y remoción de sanciones.

### M07: Estadísticas de Guerra y Combate
* **Archivos:** `modulos/estadisticas.py`
* **Entidades DB:** `estadisticas_guerra`, `miembros`, `eventos`
* **Responsabilidad:** Carga y consolidación de métricas individuales de combate en Guerra de Sombras (Kills, Asistencias, Muertes Sufridas, Puntaje/Porcentaje) por ciclo y evento. Ranking y rendimiento del clan.

### M08: Dashboard Ejecutivo y Resumen Global
* **Archivos:** `modulos/datos_resumen.py`, `generate_excel.py`
* **Entidades DB:** Consulta transversal de todas las tablas
* **Responsabilidad:** Vista ejecutiva para oficiales y líderes: KPIs del clan (total miembros, promedio resonancia, promedio IC, distribución por clases), tarjetas individuales detalladas con métricas acumuladas y generación de libro Excel multi-hoja con formato profesional (`generate_excel.py`).

---

## 2. Mapa de Dependencias entre Módulos

```text
[M01: Núcleo DB & Ciclos] <----+
       ^                       |
       |                       +--------------------+
[M02: Autenticación]           |                    |
       ^                       |                    |
       |                       v                    v
[M03: Miembros & Clases] ---> [M04: Asistencia]  [M06: Sanciones]
       |                              |             |
       +------------+-----------------+             |
       |            |                               |
       v            v                               v
[M07: Stats Guerra] [M05: Armador de Salas] <-------+
       |                    |
       +--------------------+
       v
[M08: Dashboard Ejecutivo & Resumen Global]
```

---

## 3. Propuesta de Orden de Trabajo para Relevamiento en Profundidad

Siguiendo el principio de dependencias y criticidad operativa:
1. **M01: Núcleo de Persistencia, Conexión y Ciclos Inmortales** (Fundación de datos y temporalidad).
2. **M02: Seguridad, Autenticación y Gestión de Usuarios** (Gobernanza de acceso y roles).
3. **M03: Gestión de Miembros (Roster, Altas, Bajas y Clases)** (Entidad central de negocio).
4. **M04: Control Maestro de Asistencia y Auditoría** (Módulo operativo más crítico junto a Salas).
5. **M05: Táctica y Armador de Salas de Guerra** (Lógica de asignación y comunicación).
6. **M06: Régimen Disciplinario: Sanciones y Advertencias**.
7. **M07: Estadísticas de Guerra y Combate**.
8. **M08: Dashboard Ejecutivo y Resumen Global**.
