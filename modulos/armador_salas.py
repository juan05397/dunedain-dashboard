import streamlit as st
import pandas as pd
import re
import datetime
from database import conectar_bd


def normalizar_sala_db(sala_db):
    if not sala_db:
        return ""
    # Remover espacios en los extremos
    s = sala_db.strip()
    if s.lower() == "no asignado":
        return "No asignado"
    
    # Buscar patrones como "sala 1 (8 pts)" o "sala 2 (1 pt)"
    match = re.search(r'sala\s*(\d+)\s*\(\s*(\d+)\s*(?:pts|pt|puntos|punto)?\s*\)', s, re.IGNORECASE)
    if match:
        num_sala = match.group(1)
        puntos = match.group(2)
        return f"Sala {num_sala} ({puntos} Pts)"
        
    return s


def mostrar():
    st.title("🗺️ Armador de Salas - Guerra Sombría")
    st.markdown(
        "Busca a los jugadores en el recuadro y el sistema armará las tablas automáticamente simulando tu Excel.")

    # 1. Estructura de salas para control de estado
    estructura_salas = [
        {"puntos": 8, "cantidad": 3},
        {"puntos": 4, "cantidad": 3},
        {"puntos": 2, "cantidad": 3},
        {"puntos": 1, "cantidad": 3}
    ]

    # 2. Control de estado y limpieza al cambiar de evento
    if 'ultimo_evento_seleccionado' not in st.session_state:
        st.session_state['ultimo_evento_seleccionado'] = None

    if 'selector_evento_armador' in st.session_state:
        evento_actual = st.session_state['selector_evento_armador']
        if evento_actual != st.session_state['ultimo_evento_seleccionado']:
            # Limpiar todas las claves de las salas de st.session_state
            for categoria in estructura_salas:
                pts = categoria["puntos"]
                for i in range(categoria["cantidad"]):
                    nombre_sala = f"Sala {i+1} ({pts} Pts)"
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
                    SELECT m.nombre, a.sala_asignada 
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
                pts = categoria["puntos"]
                for i in range(categoria["cantidad"]):
                    nombre_sala = f"Sala {i+1} ({pts} Pts)"
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
        pts = categoria["puntos"]
        st.markdown(f"### 🏆 Salas de {pts} Puntos")

        cols = st.columns(3)

        for i in range(categoria["cantidad"]):
            nombre_sala = f"Sala {i+1} ({pts} Pts)"

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

    st.subheader("📱 Formato para WhatsApp / Discord")
    st.info("💡 Haz clic en el **ícono de copiar** en la esquina superior derecha del recuadro negro. Al pegarlo en WhatsApp o Discord, mantendrá el formato de columnas exacto.")

    texto_whatsapp = "```\n"
    texto_whatsapp += "⚔️ ASIGNACIÓN DE SALAS - GUERRA SOMBRÍA ⚔️\n\n"

    for categoria in estructura_salas:
        pts = categoria["puntos"]
        cantidad = categoria["cantidad"]

        # CORRECCIÓN: Buscamos las salas exactamente con su nombre original (con minúsculas)
        nombres_salas = [f"Sala {i+1} ({pts} Pts)" for i in range(cantidad)]

        if any(len(selecciones_globales[sala]) > 0 for sala in nombres_salas):

            # Para imprimir en mayúsculas sin romper la búsqueda, usamos .upper() aquí
            encabezados = [sala.upper().ljust(22) for sala in nombres_salas]
            texto_whatsapp += "".join(encabezados) + "\n"
            texto_whatsapp += "-" * 62 + "\n"

            for i in range(8):
                fila_vacia = True
                fila_texto = ""

                for x, sala in enumerate(nombres_salas):
                    lista_jugadores = selecciones_globales[sala]

                    if i < len(lista_jugadores):
                        nombre = lista_jugadores[i]
                        fila_vacia = False
                    else:
                        nombre = ""

                    if x < 2:
                        fila_texto += nombre.ljust(22)
                    else:
                        fila_texto += nombre

                if not fila_vacia:
                    texto_whatsapp += fila_texto.rstrip() + "\n"

            texto_whatsapp += "\n"

    texto_whatsapp += "```"

    if len(todos_seleccionados) > 0:
        st.code(texto_whatsapp, language="text")
    else:
        st.info(
            "Comienza a asignar jugadores en la parte superior para generar el texto de forma automática.")
