import streamlit as st
import pandas as pd
from database import conectar_bd


def mostrar():
    st.title("🗺️ Armador de Salas - Guerra Sombría")
    st.markdown(
        "Busca a los jugadores en el recuadro y el sistema armará las tablas automáticamente simulando tu Excel.")

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

    estructura_salas = [
        {"puntos": 8, "cantidad": 3},
        {"puntos": 4, "cantidad": 3},
        {"puntos": 2, "cantidad": 3},
        {"puntos": 1, "cantidad": 3}
    ]

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

                seleccion = st.multiselect(
                    f"Jugadores {nombre_sala}",
                    options=nombres_activos,
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
