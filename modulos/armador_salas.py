import streamlit as st
import pandas as pd
import re
import datetime
from database import conectar_bd


def normalizar_sala_db(sala_db):
    if not sala_db: return ""
    s = sala_db.strip()
    if s.lower() == "no asignado": return "No asignado"

    # Detectar formato antiguo: "Sala 1 (8 pts)" y mapearlo al nuevo
    mapeo_puntos = {"8": "SUBLIME", "4": "EMINENTE", "2": "CELEBRE", "1": "IMPONENTE"}
    import re
    match_old = re.search(r'sala\s*(\d+)\s*\(\s*(\d+)\s*(?:pts|pt|puntos|punto)?\s*\)', s, re.IGNORECASE)
    if match_old:
        num, pts = match_old.group(1), match_old.group(2)
        return f"{num} ({mapeo_puntos.get(pts, 'SUBLIME')})"

    # Detectar formato nuevo: "1 (SUBLIME)"
    match_new = re.search(r'(\d+)\s*\((SUBLIME|EMINENTE|CELEBRE|IMPONENTE)\)', s, re.IGNORECASE)
    if match_new:
        return f"{match_new.group(1)} ({match_new.group(2).upper()})"

    return s


def mostrar():
    st.title("🗺️ Armador de Salas - Guerra Sombría")
    st.markdown(
        "Busca a los jugadores en el recuadro y el sistema armará las tablas automáticamente simulando tu Excel.")

    # 1. Estructura de salas para control de estado
    estructura_salas = [
        {"puntos": 8, "cantidad": 3, "nombre": "SUBLIME"},
        {"puntos": 4, "cantidad": 3, "nombre": "EMINENTE"},
        {"puntos": 2, "cantidad": 3, "nombre": "CELEBRE"},
        {"puntos": 1, "cantidad": 3, "nombre": "IMPONENTE"}
    ]

    # 2. Control de estado y limpieza al cambiar de evento
    if 'ultimo_evento_seleccionado' not in st.session_state:
        st.session_state['ultimo_evento_seleccionado'] = None

    if 'selector_evento_armador' in st.session_state:
        evento_actual = st.session_state['selector_evento_armador']
        if evento_actual != st.session_state['ultimo_evento_seleccionado']:
            # Limpiar todas las claves de las salas de st.session_state
            for categoria in estructura_salas:
                for i in range(categoria["cantidad"]):
                    nombre_sala = f"{i+1} ({categoria['nombre']})"
                    if nombre_sala in st.session_state:
                        del st.session_state[nombre_sala]
            
            # Guardar el nuevo evento y forzar rerun
            st.session_state['ultimo_evento_seleccionado'] = evento_actual
            st.rerun()

    try:
        conexion = conectar_bd()
        df_activos = pd.read_sql_query(
            "SELECT nombre, clase, resonancia, ic FROM miembros WHERE estado='Activo' ORDER BY nombre", conexion)
        conexion.close()
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return

    if df_activos.empty:
        st.info("No hay miembros activos registrados para armar las salas.")
        return

    nombres_activos = df_activos['nombre'].tolist()
    datos_jugadores = df_activos.set_index('nombre').to_dict('index')

    # Crear mapeo de nombres activos normalizados para comparación segura
    nombres_activos_normalizados = {str(n).strip().lower(): n for n in nombres_activos}

    # ==========================================
    # PRECARGA AUTOMÁTICA DE EVENTOS Y SALAS
    # ==========================================
    try:
        conexion_ev = conectar_bd()
        df_eventos = pd.read_sql_query("SELECT id, nombre FROM eventos", conexion_ev)
        conexion_ev.close()
    except Exception as e:
        df_eventos = pd.DataFrame()
        st.error(f"Error al obtener los eventos: {e}")

    evento_id = None
    distribucion_salas = {}
    habilidades_jugadores = {}
    fecha_mas_reciente = None

    if not df_eventos.empty:
        # Calcular el índice por defecto según el día de la semana actual
        indice_defecto = 0
        try:
            dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            dias_es_sin_tilde = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
            
            dia_actual_es = dias_es[datetime.date.today().weekday()]
            dia_actual_es_sin = dias_es_sin_tilde[datetime.date.today().weekday()]
            
            for idx, row in df_eventos.iterrows():
                nombre_ev_lower = str(row['nombre']).lower()
                if dia_actual_es in nombre_ev_lower or dia_actual_es_sin in nombre_ev_lower:
                    indice_defecto = idx
                    break
            else:
                # Si no coincide con el día de la semana, seleccionar el último evento registrado
                indice_defecto = len(df_eventos) - 1
        except Exception:
            indice_defecto = len(df_eventos) - 1

        evento_seleccionado = st.selectbox(
            "Seleccionar Evento para Precargar Salas:",
            options=df_eventos['nombre'],
            index=indice_defecto,
            key='selector_evento_armador'
        )
        
        # Sincronizar el primer valor al iniciar
        if st.session_state['ultimo_evento_seleccionado'] is None:
            st.session_state['ultimo_evento_seleccionado'] = evento_seleccionado
            
        evento_id = df_eventos[df_eventos['nombre'] == evento_seleccionado]['id'].values[0]
        
        try:
            conexion_as = conectar_bd()
            cursor_as = conexion_as.cursor()
            cursor_as.execute(
                "SELECT MAX(fecha) FROM asistencia WHERE evento_id = ?",
                (int(evento_id),)
            )
            row_fecha = cursor_as.fetchone()
            if row_fecha and row_fecha[0] is not None:
                fecha_mas_reciente = row_fecha[0]
            
            if fecha_mas_reciente:
                query_dist = """
                    SELECT m.nombre, a.sala_asignada, a.habilidad 
                    FROM asistencia a
                    JOIN miembros m ON a.miembro_id = m.id
                    WHERE a.evento_id = ? AND a.fecha = ? AND m.estado = 'Activo'
                """
                df_dist = pd.read_sql_query(query_dist, conexion_as, params=(int(evento_id), str(fecha_mas_reciente)))
                
                if not df_dist.empty:
                    for _, row in df_dist.iterrows():
                        sala_raw = row['sala_asignada']
                        nombre_raw = row['nombre']
                        if sala_raw:
                            sala_norm = normalizar_sala_db(sala_raw)
                            if sala_norm != 'No asignado':
                                if sala_norm not in distribucion_salas:
                                    distribucion_salas[sala_norm] = []
                                distribucion_salas[sala_norm].append(nombre_raw)

                        habilidad_raw = row['habilidad'] if 'habilidad' in row and pd.notna(row['habilidad']) and row['habilidad'] != 'Seleccione' else "ROCA"
                        habilidad_limpia = habilidad_raw.split(" ", 1)[1] if " " in str(habilidad_raw) else str(habilidad_raw)
                        habilidades_jugadores[nombre_raw] = habilidad_limpia.upper()
            conexion_as.close()
        except Exception as e:
            st.error(f"Error al cargar la última asignación de salas: {e}")

        # --- AUTO-SINCRONIZACIÓN DE CACHÉ (INVALIDACIÓN DE MEMORIA) ---
        # Ordenamos los nombres de los jugadores y de las salas para que la representación en cadena sea determinista
        distribucion_estable = {s: sorted(players) for s, players in distribucion_salas.items()}
        current_db_hash = str(sorted(distribucion_estable.items()))
        
        last_db_hash = st.session_state.get('last_db_hash_armador')
        
        if last_db_hash != current_db_hash:
            # Borrar de session_state las claves de las salas para obligar a tomar los nuevos defaults de la BD
            for categoria in estructura_salas:
                for i in range(categoria["cantidad"]):
                    nombre_sala = f"{i+1} ({categoria['nombre']})"
                    if nombre_sala in st.session_state:
                        del st.session_state[nombre_sala]
            
            # Guardar el nuevo hash y forzar rerun
            st.session_state['last_db_hash_armador'] = current_db_hash
            st.rerun()

        # Mensajes de estado sobre la precarga
        if fecha_mas_reciente and distribucion_salas:
            st.info(f"💡 Se ha precargado la última distribución del evento registrada el **{fecha_mas_reciente}**.")
        elif fecha_mas_reciente:
            st.info(f"ℹ️ No hay una distribución de salas guardada para este evento en la fecha registrada ({fecha_mas_reciente}).")
        else:
            st.info("ℹ️ No hay una distribución de salas guardada para este evento en esta fecha.")

    selecciones_globales = {}
    todos_seleccionados = []

    # ==========================================
    # CONSTRUCTOR DE LA INTERFAZ ESTILO EXCEL
    # ==========================================
    for categoria in estructura_salas:
        st.markdown(f"### 🏆 {categoria['nombre']}")

        cols = st.columns(3)

        for i in range(categoria["cantidad"]):
            nombre_sala = f"{i+1} ({categoria['nombre']})"

            with cols[i]:
                st.markdown(
                    f"<h5 style='text-align: center; color: #4DA8DA;'>{nombre_sala}</h5>", unsafe_allow_html=True)

                # Obtener los jugadores asignados previamente a esta sala (solo si siguen activos en el sistema)
                default_jugadores = []
                for p_raw in distribucion_salas.get(nombre_sala, []):
                    p_clean = str(p_raw).strip().lower()
                    if p_clean in nombres_activos_normalizados:
                        default_jugadores.append(nombres_activos_normalizados[p_clean])

                seleccion = st.multiselect(
                    f"Jugadores {nombre_sala}",
                    options=nombres_activos,
                    default=default_jugadores,
                    max_selections=8,
                    key=nombre_sala,
                    label_visibility="collapsed",
                    placeholder="🔍 Buscar jugador..."
                )

                selecciones_globales[nombre_sala] = seleccion
                todos_seleccionados.extend(seleccion)

                filas_tabla = []
                reso_total = 0
                ic_total = 0

                for j in range(8):
                    if j < len(seleccion):
                        jugador = seleccion[j]
                        reso = datos_jugadores[jugador]['resonancia']
                        ic = datos_jugadores[jugador]['ic']
                        clase = datos_jugadores[jugador]['clase']

                        reso_total += reso
                        ic_total += ic

                        filas_tabla.append(
                            {"#": j+1, "Jugador": jugador, "Reso": reso, "Clase": clase})
                    else:
                        filas_tabla.append(
                            {"#": j+1, "Jugador": "---", "Reso": None, "Clase": "---"})

                df_sala = pd.DataFrame(filas_tabla)

                st.dataframe(
                    df_sala,
                    column_config={
                        "#": st.column_config.NumberColumn(width="small"),
                        "Jugador": st.column_config.TextColumn(width="medium"),
                        "Reso": st.column_config.NumberColumn(width="small"),
                        "Clase": st.column_config.TextColumn(width="medium"),
                    },
                    hide_index=True,
                    use_container_width=True
                )

                if seleccion:
                    ic_promedio = int(ic_total / len(seleccion))
                    st.markdown(
                        f"<div style='text-align: center; font-size: 0.9em; padding-bottom: 15px; color: #a0a0a0;'>💎 Reso Total: <b>{reso_total:,}</b> | ⚔️ IC Prom: <b>{ic_promedio:,}</b></div>", unsafe_allow_html=True)
                else:
                    st.write("")

        st.divider()

    # ==========================================
    # VALIDACIONES Y GENERADOR DE TEXTO (BLOQUE MONOSPACIADO)
    # ==========================================
    duplicados = set(
        [x for x in todos_seleccionados if todos_seleccionados.count(x) > 1])
    if duplicados:
        st.error(
            f"⚠️ ¡Atención! Has asignado a los siguientes jugadores en más de una sala: **{', '.join(duplicados)}**")

    st.subheader("📱 Mensajes Individuales para WhatsApp / Discord")
    st.info("💡 Despliega la sala correspondiente para copiar el mensaje individual de cada jugador.")

    if len(todos_seleccionados) > 0:
        for categoria in estructura_salas:
            cat_nombre = categoria["nombre"]
            for i in range(categoria["cantidad"]):
                num_sala = i + 1
                nombre_sala_key = f"{num_sala} ({cat_nombre})"
                jugadores_sala = selecciones_globales.get(nombre_sala_key, [])
                
                if jugadores_sala:
                    with st.expander(f"Mensajes para SALA {cat_nombre} {num_sala} ({len(jugadores_sala)} jugadores)"):
                        for jugador in jugadores_sala:
                            st.markdown(f"**Para el jugador: {jugador}**")
                            
                            habilidad_asignada = habilidades_jugadores.get(jugador, "ROCA")
                            
                            # Plantilla del mensaje
                            mensaje = (
                                f"Hola *{jugador}* 👋\n\n"
                                f"Te recuerdo que *hoy tenemos Guerra a las 19:30 hs. server* ⚔️🔥\n\n"
                                f"Contamos especialmente con tu apoyo en:\n\n"
                                f"🏛️ *SALA {cat_nombre} {num_sala}*\n"
                                f"🪨 *HABILIDAD {habilidad_asignada}*\n\n"
                                f"No olvides tomar tus *bendiciones unos minutos antes de que comience la guerra*. 🙏\n\n"
                                f"Tu participación es muy importante para el equipo y necesitamos que estés preparado para cumplir con esta función. 💪\n\n"
                                f"¡Muchas gracias por tu compromiso y por darlo todo por el clan! ❤️🔥\n\n"
                                f"*¡Vamos con toda por la victoria! 🏆🔥*\n\n"
                                f"Atte.\n"
                                f"*Admin. RΛGИΛЯØK*"
                            )
                            
                            st.code(mensaje, language="text")
    else:
        st.info("Comienza a asignar jugadores en la parte superior para generar los mensajes de forma automática.")
