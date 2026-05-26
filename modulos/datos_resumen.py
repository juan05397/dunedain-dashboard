import streamlit as st
import pandas as pd
from database import conectar_bd


def mostrar():
    st.title("🛡️ Panel de Gestión - Base de Datos")
    try:
        conexion = conectar_bd()

        # 1. Consultar Activos (Omitimos traer el 'id' de la BD)
        df_activos = pd.read_sql_query(
            "SELECT nombre, clase, resonancia, ic, estado FROM miembros WHERE estado='Activo' ORDER BY nombre", conexion)

        # 2. Consultar Inactivos/Expulsados (Agregamos la fecha de baja para que sea útil)
        df_inactivos = pd.read_sql_query(
            "SELECT nombre, clase, resonancia, ic, estado, fecha_baja FROM miembros WHERE estado IN ('Inactivo', 'Expulsado') ORDER BY fecha_baja DESC", conexion)

        conexion.close()

        # Generar numeración consecutiva (Posición del 1 en adelante)
        if not df_activos.empty:
            df_activos.insert(0, '#', range(1, len(df_activos) + 1))

        if not df_inactivos.empty:
            df_inactivos.insert(0, '#', range(1, len(df_inactivos) + 1))

        # Panel Superior de Métricas
        st.subheader("📊 Métricas del Clan")
        col1, col2, col3 = st.columns(3)
        col1.metric("Miembros Activos", f"{len(df_activos)} / 100")
        col2.metric("Resonancia Promedio", int(
            df_activos['resonancia'].mean()) if not df_activos.empty else 0)
        col3.metric("IC Promedio", int(
            df_activos['ic'].mean()) if not df_activos.empty else 0)

        st.divider()

        # Pestañas de Visualización
        tab_activos, tab_inactivos = st.tabs(
            ["🟢 Miembros Activos", "🔴 Miembros Inactivos / Bajas"])

        with tab_activos:
            st.markdown(f"**Lista oficial del clan**")
            # Streamlit permite scroll nativo, pero al estar numerados del 1 al 100 será fácil ver los cupos
            st.dataframe(df_activos, use_container_width=True, hide_index=True)

        with tab_inactivos:
            st.markdown("**Historial de jugadores retirados o vetados**")

            if not df_inactivos.empty:
                registros_por_pagina = 100
                total_registros = len(df_inactivos)

                # Lógica de Paginación: Solo se muestra si hay más de 100 registros
                if total_registros > registros_por_pagina:
                    total_paginas = (total_registros // registros_por_pagina) + \
                        (1 if total_registros % registros_por_pagina > 0 else 0)

                    # Selector de página
                    pagina_actual = st.number_input(
                        "Página:", min_value=1, max_value=total_paginas, value=1, step=1)

                    # Cortar el dataframe según la página
                    inicio = (pagina_actual - 1) * registros_por_pagina
                    fin = inicio + registros_por_pagina
                    df_mostrar = df_inactivos.iloc[inicio:fin]

                    st.info(
                        f"Mostrando registros **{inicio + 1} al {min(fin, total_registros)}** de un total de {total_registros}.")
                    st.dataframe(
                        df_mostrar, use_container_width=True, hide_index=True)
                else:
                    # Si hay menos de 100, se muestran todos normalmente
                    st.dataframe(
                        df_inactivos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay miembros inactivos registrados en el historial.")

    except Exception as e:
        st.error(
            f"⚠️ No se pudieron cargar los datos en este momento. Error: {e}")
