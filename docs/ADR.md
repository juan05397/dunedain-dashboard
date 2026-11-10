# 🏛️ Registro de Decisiones de Arquitectura (ADR)
**Proyecto:** Migración a Arquitectura Modular (FastAPI + Next.js + Turso)  
**Documento:** Acumulativo de Decisiones de Gobernanza y Negocio  
**Estado:** Activo  

---

## Índice de Decisiones
* [ADR-001: Adopción del Proceso de Relevamiento Funcional As-Is Previo a Migración](#adr-001-adopción-del-proceso-de-relevamiento-funcional-as-is-previo-a-migración)
* [ADR-002: Identidad Oficial del Clan (RΛGИΛЯØK)](#adr-002-identidad-oficial-del-clan-rλgиλяøk)
* [ADR-003: Invariante Operativa de Ciclo Inmortal Activo Obligatorio](#adr-003-invariante-operativa-de-ciclo-inmortal-activo-obligatorio)
* [ADR-004: Tipología de Eventos de Clan (Fijos vs. Dinámicos)](#adr-004-tipología-de-eventos-de-clan-fijos-vs-dinámicos)

---

### ADR-001: Adopción del Proceso de Relevamiento Funcional As-Is Previo a Migración
* **Fecha:** 2026-09-06
* **Módulo Relacionado:** General / Gobernanza
* **Estado:** 🟢 APROBADO (Confirmado explícitamente por el usuario)
* **Decisión Tomada:** Establecer una etapa formal de relevamiento documental funcional 100% "As-Is" en modo solo lectura, previo a escribir código en FastAPI o Next.js. Toda regla debe contar con evidencia en código o confirmación en chat, respaldada por un sistema de semáforo (🔴/🟡/🟢).
* **Contexto y Justificación:** La base de código actual contiene reglas de negocio implícitas, lógicas embebidas e inconsistencias operativas que deben quedar mapeadas como fuente de verdad inmutable antes de desacoplar el sistema.
* **Confirmación Explícita del Usuario:** "si" (2026-09-06).

---

### ADR-002: Identidad Oficial del Clan (RΛGИΛЯØK)
* **Fecha:** 2026-09-06
* **Módulo Relacionado:** General / UI / Armador de Salas
* **Estado:** 🟢 APROBADO (Confirmado explícitamente por el usuario)
* **Decisión Tomada:** Reconocer que la identidad oficial actual del clan es **RΛGИΛЯØK**. El nombre original del repositorio y de la base de datos local (`ÐÛΝΞÐΛIN`, `clan_dunedain.db`) corresponde a la identidad histórica previa.
* **Contexto y Justificación:** En la base de datos y títulos figuraba `ÐÛΝΞÐΛIN`, mientras que los mensajes tácticos firman como `Admin. RΛGИΛЯØK`.
* **Confirmación Explícita del Usuario:** "no se cambio el nombre del clan ahora se llama RΛGИΛЯØK" (2026-09-06).

---

### ADR-003: Invariante Operativa de Ciclo Inmortal Activo Obligatorio
* **Fecha:** 2026-09-06
* **Módulo Relacionado:** M01 (Núcleo y Ciclos Inmortales) / M04 (Asistencia)
* **Estado:** 🟢 APROBADO (Confirmado explícitamente por el usuario)
* **Decisión Tomada:** Se define como regla de negocio absoluta que **en todo momento debe existir exactamente un Ciclo Inmortal en estado 'Activo'**. No se contemplan estados operativos de receso sin ciclo.
* **Contexto y Justificación:** Todos los módulos operacionales (asistencias, estadísticas y armado de salas) requieren vincularse a un ciclo vigente para poder registrar actividades.
* **Confirmación Explícita del Usuario:** "siempre tiene que ver un ciclo abierto en todo momento" (2026-09-06).

---

### ADR-004: Tipología de Eventos de Clan (Fijos vs. Dinámicos)
* **Fecha:** 2026-09-06
* **Módulo Relacionado:** M01 (Núcleo y Ciclos Inmortales) / M04 (Asistencia) / M05 (Salas)
* **Estado:** 🟢 APROBADO (Confirmado explícitamente por el usuario)
* **Decisión Tomada:** Los eventos base obligatorios e inmutables del clan son **Guerra de Sombras Jueves** y **Guerra de Sombras Sábado**. El resto de los eventos registrados (Pelea de Torres, Vigilia de Espadas / Rito, Limpieza de Torres) son de naturaleza dinámica y configurables por los administradores.
* **Contexto y Justificación:** La Guerra de Sombras es la columna vertebral competitiva semanal del juego; otros eventos varían según el reinado y decisiones estratégicas.
* **Confirmación Explícita del Usuario:** "los unicos que son fijo siempre son Guerra de Sombras Jueves, Guerra de Sombras Sábado los demas pueden variar mucho y por eso los administradores lo agregan ahorita" (2026-09-06).
