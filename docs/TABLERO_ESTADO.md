# 🚦 Tablero de Control y Estado Global de Relevamiento
**Proyecto:** Migración a Arquitectura Modular (FastAPI + Next.js + Turso)  
**Fecha de Actualización:** 2026-09-06  
**Criterio de Semáforo:**  
* 🔴 **ROJO:** En relevamiento, bloqueado o con dudas críticas pendientes.  
* 🟡 **AMARILLO:** Borrador presentado, con observaciones del usuario o preguntas en discusión.  
* 🟢 **VERDE:** 100% revisado, sin dudas pendientes y aprobado explícitamente por el usuario.  

---

| ID | Módulo Funcional | Archivos Fuente As-Is | Estado Actual | % Puntos 🟢 | Última Actualización |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **M00** | **Gobernanza, Glosario e Inventario Inicial** | Raíz, `app.py`, `database.py` | 🟢 | 100% | 2026-09-06 |
| **M01** | **Núcleo: Conexión, DB y Ciclos Inmortales** | `database.py`, `ciclo_inmortal.py` | 🟡 | 62.5% | 2026-09-06 |
| **M02** | **Seguridad, Autenticación y Usuarios** | `app.py`, `admin_usuarios.py` | 🔴 | 0% | 2026-09-06 |
| **M03** | **Gestión de Miembros (Roster, Altas/Bajas y Clases)** | `alta_baja.py`, `admin_clases.py` | 🔴 | 0% | 2026-09-06 |
| **M04** | **Control Maestro de Asistencia y Auditoría** | `asistencia.py` | 🔴 | 0% | 2026-09-06 |
| **M05** | **Táctica y Armador de Salas de Guerra** | `armador_salas.py` | 🔴 | 0% | 2026-09-06 |
| **M06** | **Régimen Disciplinario: Sanciones** | `sanciones.py` | 🔴 | 0% | 2026-09-06 |
| **M07** | **Estadísticas de Guerra y Rendimiento** | `estadisticas.py` | 🔴 | 0% | 2026-09-06 |
| **M08** | **Dashboard Ejecutivo y Resumen Global** | `datos_resumen.py`, `generate_excel.py` | 🔴 | 0% | 2026-09-06 |

*Progreso Global del Relevamiento:* **20.3%**
