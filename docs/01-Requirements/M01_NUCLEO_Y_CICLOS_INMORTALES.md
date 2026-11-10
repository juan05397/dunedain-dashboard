# 📋 ESPECIFICACIÓN FUNCIONAL AS-IS: M01 — NÚCLEO DE PERSISTENCIA Y CICLOS INMORTALES

**Módulo:** M01 — Núcleo de Persistencia, Conexión y Ciclos Inmortales  
**Versión:** 1.0 (Borrador Inicial As-Is)  
**Fecha:** 2026-09-06  
**Estado:** 🟡 AMARILLO (Borrador presentado, a la espera de validación de preguntas)  

---

## 4.1 Ficha del Módulo y Responsabilidad Funcional
* **Objetivo Operativo:** Proveer la capa base de conectividad a la base de datos (Turso libSQL / SQLite local) y gobernar la línea de tiempo del clan a través de los **Ciclos Inmortales**. Un ciclo inmortal representa la era de reinado del servidor en *Diablo Immortal*, delimitando temporalmente todas las asistencias, distribuciones de salas y estadísticas de guerra.
* **Actores y Roles Intervinientes:**
  * **Administrador (`rol = 'admin'`):** Único rol autorizado para acceder a la gestión de ciclos (crear, cerrar, auditar y eliminar ciclos históricos).
  * **Operador / Usuario (`rol = 'usuario'`):** Rol de solo lectura/consumo indirecto. No tiene acceso visual al módulo; su operatoria en otros módulos consume el ciclo activo de forma transparente.
  * **Sistema / Motor:** Ejecuta la inicialización de esquemas y conexión resiliente al arrancar cualquier consulta.

---

## 4.2 Evidencia As-Is (Archivos Fuente, Funciones y Tablas)
* **Archivos Analizados:**
  * [`database.py`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py) (Líneas 1 a 265)
  * [`modulos/ciclo_inmortal.py`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py) (Líneas 1 a 205)
* **Funciones Clave:**
  * `conectar_bd()`: [`database.py:6-45`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py#L6-L45). Gestión de credenciales Turso y fallback local SQLite con activación de claves foráneas (`PRAGMA foreign_keys = ON`).
  * `preparar_db()`: [`database.py:47-179`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py#L47-L179). DDL implícito, migración de columnas y siembra inicial de 11 clases.
  * `obtener_ciclo_activo()`: [`database.py:210-216`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py#L210-L216). Consulta de ciclo vigente con cache `@st.cache_data(ttl=60)`.
  * `obtener_eventos()`: [`database.py:194-198`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py#L194-L198). Catálogo de eventos activos.
  * `obtener_historial_ciclos()`: [`modulos/ciclo_inmortal.py:8-12`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L8-L12). Grilla histórica de ciclos ordenados descendentemente por ID.
  * `calcular_duracion(desde_str, hasta_str)`: [`modulos/ciclo_inmortal.py:15-30`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L15-L30). Cálculo de días transcurridos y conversión a semanas.
  * `mostrar()`: [`modulos/ciclo_inmortal.py:33-205`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L33-L205). Pantalla administrativa completa (Estado actual, Crear ciclo, Cerrar ciclo y Eliminar ciclo histórico protegido).
* **Tablas Consultadas/Modificadas:**
  * `ciclos_inmortales` (Lectura, Inserción, Modificación, Eliminación)
  * `eventos` (Lectura)
  * `asistencia` (Lectura para integridad referencial previa a borrado)
  * `estadisticas_guerra` (Lectura para integridad referencial previa a borrado)

---

## 4.3 Reglas de Negocio Observadas

1. **Control de Acceso RBAC Estricto:**
   * Evidencia: [`modulos/ciclo_inmortal.py:39-41`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L39-L41).
   * Si `st.session_state.get('rol') != 'admin'`, la interfaz bloquea completamente la renderización con un mensaje de error y aborta el flujo con `return`.
2. **Unicidad de Ciclo Activo (Regla de Oro de Negocio):**
   * Evidencia: [`modulos/ciclo_inmortal.py:74-76`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L74-L76), [`database.py:57`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/database.py#L57), confirmado en chat (ADR-003).
   * No se permite crear un nuevo ciclo si ya existe uno en estado `'Activo'`. El ciclo actual debe ser cerrado previamente.
3. **Validación de Superposición Cronológica (No Solapamiento):**
   * Evidencia: [`modulos/ciclo_inmortal.py:83-94`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L83-L94).
   * La fecha de inicio (`fecha_desde`) del nuevo ciclo debe ser estrictamente posterior a la fecha de fin del último ciclo cerrado: `fecha_desde > MAX(fecha_hasta)`. Si `fecha_desde <= max_hasta`, la creación es rechazada.
4. **Consistencia Temporal de Cierre:**
   * Evidencia: [`modulos/ciclo_inmortal.py:124-126`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L124-L126).
   * Al finalizar el ciclo activo, la fecha de cierre debe ser cronológicamente igual o posterior a su fecha de inicio: `fecha_hasta >= fecha_desde`.
5. **Cálculo Dinámico de Duración del Reinado:**
   * Evidencia: [`modulos/ciclo_inmortal.py:21-28`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L21-L28).
   * Si el ciclo está finalizado: `días = (fecha_hasta - fecha_desde)`, `semanas = round(días / 7, 1)`.
   * Si el ciclo está activo: `días = (hoy - fecha_desde)`, `semanas = round(días / 7, 1)`.
6. **Protección de Integridad Referencial en Eliminación (Soft-Block):**
   * Evidencia: [`modulos/ciclo_inmortal.py:184-194`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/ciclo_inmortal.py#L184-L194).
   * Está terminantemente prohibido eliminar un ciclo de la base de datos si existen registros dependientes en las tablas `asistencia` (`ciclo = 'Ciclo {id}'`) o `estadisticas_guerra` (`ciclo = 'Ciclo {id}'`). Requiere además activar explícitamente un checkbox de confirmación en UI.

---

## 4.4 Casos Borde, Inconsistencias y Bugs Detectados

1. **Inconsistencia Crítica de Tipo en Llave Foránea (`ciclo`):**
   * *Hallazgo:* En `ciclos_inmortales`, la clave primaria es un entero autonumérico `id` (ej. `2`). Sin embargo, en las tablas dependientes `asistencia` y `estadisticas_guerra`, la columna `ciclo` no es una clave foránea formal entera, sino un string de texto formateado como `'Ciclo 2'`.
   * *Riesgo:* Desacoplamiento de integridad referencial a nivel motor de base de datos; si en el futuro se renombrara el ciclo o cambiara el prefijo, las consultas romperían la vinculación histórica.
2. **Cero Tolerancia a Períodos Sin Ciclo Activo:**
   * *Hallazgo:* Si un administrador finaliza un ciclo y no crea de inmediato el siguiente, la aplicación entra en estado huérfano. En [`asistencia.py:64-68`](file:///c:/Users/BRILLO/OneDrive/Escritorio/%C3%90%C3%9B%CE%9D%CE%9E%C3%90%CE%9BIN/modulos/asistencia.py#L64-L68), el módulo de asistencia muestra un cartel rojo y bloquea toda la pantalla de carga si `obtener_ciclo_activo()` devuelve `None`.
   * *Mitigación Confirmada:* ADR-003 ratifica que siempre debe existir un ciclo activo.
3. **Ausencia de Transacción Atómica en Cierre/Apertura:**
   * *Hallazgo:* El proceso de "Cerrar ciclo viejo" y "Crear ciclo nuevo" se hace en dos formularios y dos clics separados. Esto abre una ventana de inconsistencia temporal donde el sistema puede quedar sin ciclo activo entre ambos clics.
4. **Vulnerabilidad de Entrada en Fechas (Formato String vs Date):**
   * *Hallazgo:* En SQLite/Turso, las fechas se persisten como texto `TEXT`. Si se inserta manualmente una fecha sin padding (ej. `2026-6-8` vs `2026-06-08`), la validación de orden alfabético y parsing fallará con un `ValueError` en `calcular_duracion()`.

---

## 4.5 Datos y Esquema Relacionado

### Esquema Físico Observado

```sql
CREATE TABLE ciclos_inmortales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_desde TEXT NOT NULL,
    fecha_hasta TEXT,
    estado TEXT CHECK(estado IN ('Activo', 'Finalizado')) NOT NULL DEFAULT 'Activo'
);

CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);
```

### Relaciones Observadas en Código (No forzadas por DDL)

| Tabla Origen | Columna Origen | Tabla Destino | Columna Destino | Tipo de Relación | Comportamiento |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `asistencia` | `ciclo` (TEXT) | `ciclos_inmortales` | `'Ciclo ' || id` | Lógica / Implícita | Restringe eliminación en UI |
| `estadisticas_guerra` | `ciclo` (TEXT) | `ciclos_inmortales` | `'Ciclo ' || id` | Lógica / Implícita | Restringe eliminación en UI |

---

## 4.6 Hallazgos y Deuda Técnica Funcional

1. **Gestión de Conexiones por Operación:** Cada función abre una conexión con `conectar_bd()` y la cierra al terminar, lo cual genera alta latencia si se usa Turso en la nube (handshake TLS repetido) en lugar de un pool de conexiones persistente.
2. **Uso de Caché de Streamlit (`@st.cache_data(ttl=60)`):** La sincronización entre administradores concurrentes depende de un TTL de 60 segundos o de invocar manualmente `st.cache_data.clear()`.
3. **Catálogo de Eventos sin Interfaz de Gestión:** Aunque la tabla `eventos` existe y se consulta constantemente, no existe en la aplicación una pantalla para que el administrador cree, edite o desactive eventos dinámicos; se asumen cargados previamente en la base.

---

## 4.7 Matriz de Semáforo del Módulo M01

| Sección | Componente Evaluado | Estado | Justificación / Evidencia |
| :---: | :--- | :---: | :--- |
| **4.1** | Ficha del Módulo y Responsabilidad | 🟢 | Objetivos, roles y alcance verificados en código. |
| **4.2** | Evidencia As-Is | 🟢 | Código fuente y funciones mapeadas con exactitud de líneas. |
| **4.3** | Reglas de Negocio Observadas | 🟢 | Lógica de unicidad, fechas, duración y borrado respaldada en código y ADR-003. |
| **4.4** | Casos Borde, Inconsistencias y Bugs | 🟡 | Se detectó desnormalización (`'Ciclo X'`) y brecha entre cierre y alta de ciclo. Requiere validación de preguntas. |
| **4.5** | Datos y Esquema Relacionado | 🟢 | DDL verificado directamente contra la base de datos real. |
| **4.6** | Hallazgos y Deuda Técnica | 🟢 | Conexiones, caché y falta de interfaz de eventos identificadas con claridad. |
| **4.8** | Validación de Preguntas Pendientes | 🟡 | 4 preguntas formuladas a continuación para cerrar el módulo en verde. |

> **Estado Consolidado del Módulo M01:** 🟡 **AMARILLO (62.5% 🟢)**

---

## 4.8 Preguntas Pendientes de Validación (Ronda M01)

1. **Transición Atómica de Ciclo:** Dado que el sistema requiere que siempre haya un ciclo activo (ADR-003), en el comportamiento actual un admin debe cerrar primero el ciclo 1 y luego crear el ciclo 2 (dejando un lapso sin ciclo). En el sistema actual, ¿los administradores cierran el ciclo el mismo día que inicia el nuevo, o qué hacen operativamente cuando un reinado termina el domingo a la noche?
2. **Identificador de Ciclo en la Práctica:** En el juego *Diablo Immortal*, los clanes a veces llaman a los ciclos por número correlativo ("Ciclo 1", "Ciclo 2") o por nombre de fantasía / era. En el sistema actual solo se guarda el número autoincremental `id`. ¿Es suficiente mantener únicamente el número correlativo o en algún momento necesitaron ponerle nombre al ciclo?
3. **Gestión de Eventos Dinámicos:** En la pregunta anterior confirmaste que los eventos fuera de Guerra de Sombras son dinámicos y los agregan los administradores. En el código actual no hay pantalla para agregar eventos en `eventos`. ¿Cómo agregan hoy los administradores un evento nuevo como "Vigilia de Espadas" (directamente en la base de datos / script, o falta esa pantalla en el sistema actual)?
4. **Estandarización de Llave Foránea para Migración (Impacto Futuro):** En la base de datos actual, las asistencias guardan el texto `'Ciclo 2'` en lugar del entero `2`. Para la futura migración a FastAPI, ¿deseas mantener ese texto literal para compatibilidad histórica o normalizarlo a una relación numérica estándar de base de datos (`ciclo_id = 2`)?
