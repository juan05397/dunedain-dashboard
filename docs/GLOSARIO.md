# 📖 Glosario de Negocio y Consistencia Terminológica
**Proyecto:** Migración a Arquitectura Modular (FastAPI + Next.js + Turso)  
**Dominio:** Gestión de Clan en Diablo Immortal  
**Fecha de Creación:** 2026-09-06  
**Estado:** 🟡 En Construcción / Relevamiento Inicial  

---

## 1. Términos del Dominio (Diablo Immortal) y del Sistema

| Término Negocio | Término en Código | Término en DB | Término en UI (Streamlit) | Definición Funcional Observada |
| :--- | :--- | :--- | :--- | :--- |
| **Miembro / Jugador** | `jugador`, `miembro` | Tabla `miembros` | "Jugador", "Nombre" | Personaje perteneciente al clan con estado ('Activo' / 'Inactivo'). |
| **Resonancia** | `resonancia` | `miembros.resonancia` | "Resonancia" | Atributo numérico de poder derivado de gemas legendarias. |
| **Índice de Combate (IC)** | `ic` | `miembros.ic` | "IC" | Métrica de combate base del personaje en Diablo Immortal. |
| **Atributos Secundarios** | `armadura`, `penetracion_armadura`, `potencia`, `resistencia` | Columnas en `miembros` | "Atributos Secundarios" | Estadísticas avanzadas de combate registradas en el perfil. |
| **Atributos de Apoyo** | `velocidad_ataque`, `reduccion_recuperacion`, `duracion_beneficiosos` | Columnas en `miembros` | "Atributos de Apoyo" | Porcentajes de velocidad y recuperación del personaje. |
| **Rango Sombra** | `rango_sombra` | `miembros.rango_sombra` | "Rango Sombra" | Rango de facción sombra (Susurrador, Espada, Iniciado, etc.). |
| **Ciclo Inmortal** | `ciclo`, `ciclo_nombre` | Tabla `ciclos_inmortales` | "Ciclo Inmortal", "Ciclo Activo" | Período de reinado/competencia del servidor ('Activo' o 'Finalizado'). |
| **Evento de Clan** | `evento` | Tabla `eventos` | "Evento a gestionar", "Evento" | Actividad competitiva o de clan (Guerra, Rito, Torres, etc.). |
| **Intención de Voto** | `intencion` | `asistencia.intencion` | "Intención de Voto", "Voto en WhatsApp" | Compromiso previo declarado ('Sí puedo', 'No puedo', 'No aseguro', 'No votó'). |
| **Asistencia Real** | `asistio_realmente` | `asistencia.asistio_realmente` | "Asistencia Real", "Asistieron Realmente" | Booleano/entero (0/1) que certifica presencia efectiva in-game. |
| **Estado Fantasma** | `"👻 Fantasma"` | Calculado en runtime | "👻 Fantasma" | Jugador que asistió al evento in-game pero no votó en WhatsApp. |
| **Infracción de Asistencia**| `"🚨 INFRACCIÓN"` | Calculado en runtime | "🚨 INFRACCIÓN" | Jugador que votó 'Sí puedo' pero NO asistió in-game. |
| **Sala de Guerra** | `sala_asignada` | `asistencia.sala_asignada` | "Sala de Guerra", "SALA" | Categoría y número de sala táctica (Sublime, Eminente, Célebre, Imponente, máx. 8). |
| **Habilidad de Guerra** | `habilidad` | `asistencia.habilidad` | "Habilidad", "HABILIDAD" | Rol/habilidad táctica asignada en sala (ej. ROCA, etc.). |
| **Sanción** | `sancion` | Tabla `sanciones` | "Sanciones y Advertencias" | Registro disciplinario asociado a un miembro con tipo y motivo. |
| **Usuario del Sistema** | `usuario` | Tabla `usuarios` | "Usuario", "Gestión de Accesos" | Operador de la plataforma de comando con rol ('admin' / 'usuario'). |

---

## 2. Inconsistencias y Puntos de Atención Detectados

1. **Nombre del Clan:** La plataforma está nombrada como `ÐÛΝΞÐΛIN Dashboard`, pero las plantillas de mensajes generadas en el Armador de Salas firman como `Admin. RΛGИΛЯØK`.
2. **Normalización de Salas:** Coexisten nomenclaturas antiguas (`"Sala 1 (8 pts)"`) y actuales (`"1 (SUBLIME)"`).
3. **Estado de Asistencia:** En tabla `asistencia`, el campo `estado_asistencia` contiene valores fijos como `'Procesado'`, mientras que el verdadero estado de cumplimiento se deduce en runtime de la combinación de `intencion` y `asistio_realmente`.
