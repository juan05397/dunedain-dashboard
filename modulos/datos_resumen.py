import streamlit as st
import pandas as pd
from database import conectar_bd


def mostrar():
    st.title("🛡️ Panel de Gestión - Base de Datos")
    try:
        conexion = conectar_bd()

        # 1. Consultar Activos (Omitimos traer el 'id' de la BD)
        df_activos = pd.read_sql_query(
            "SELECT nombre, clase, resonancia, ic, estado, alta_realizada_por FROM miembros WHERE estado='Activo' ORDER BY nombre", conexion)

        # 2. Consultar Inactivos/Expulsados (Agregamos la fecha de baja para que sea útil)
        df_inactivos = pd.read_sql_query(
            "SELECT nombre, clase, resonancia, ic, estado, fecha_baja, motivo_baja, baja_realizada_por FROM miembros WHERE estado IN ('Inactivo', 'Expulsado') ORDER BY fecha_baja DESC", conexion)

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

        # --- SECCIÓN DE GRÁFICOS NATIVOS DE STREAMLIT ---
        if not df_activos.empty:
            with st.expander("📈 Ver Gráficos de Progresión y Fuerza del Clan", expanded=True):
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.markdown("<h5 style='text-align: center; color: #a9b0ba;'>👥 Distribución de Clases Activas</h5>", unsafe_allow_html=True)
                    df_clases = df_activos['clase'].value_counts().reset_index()
                    df_clases.columns = ['Clase', 'Cantidad']
                    st.bar_chart(df_clases.set_index('Clase'), y='Cantidad', color='#4DA8DA', height=300)
                
                with col_chart2:
                    st.markdown("<h5 style='text-align: center; color: #a9b0ba;'>💎 Fuerza: Resonancia vs. Índice de Combate (IC)</h5>", unsafe_allow_html=True)
                    # Gráfico de dispersión para correlacionar estadísticas
                    st.scatter_chart(df_activos, x='resonancia', y='ic', color='clase', height=300)
                
                st.write("")
                st.markdown("<h5 style='text-align: center; color: #a9b0ba;'>📊 Resonancia Promedio por Clase</h5>", unsafe_allow_html=True)
                df_prom_reso = df_activos.groupby('clase')['resonancia'].mean().reset_index()
                df_prom_reso.columns = ['Clase', 'Resonancia Promedio']
                df_prom_reso['Resonancia Promedio'] = df_prom_reso['Resonancia Promedio'].fillna(0).astype(int)
                st.bar_chart(df_prom_reso.set_index('Clase'), y='Resonancia Promedio', color='#f39c12', height=250)

        st.divider()

        # Pestañas de Visualización
        tab_activos, tab_inactivos, tab_buscador = st.tabs(
            ["🟢 Miembros Activos", "🔴 Miembros Inactivos / Bajas", "🔍 Buscador de Jugadores Premium"])

        with tab_activos:
            st.markdown(f"**Lista oficial del clan**")
            # Renombrar columnas para visualización amigable
            df_activos_visual = df_activos.rename(columns={
                'nombre': 'Nombre',
                'clase': 'Clase',
                'resonancia': 'Resonancia',
                'ic': 'IC',
                'estado': 'Estado',
                'alta_realizada_por': 'Alta realizada por'
            })
            st.dataframe(df_activos_visual, use_container_width=True, hide_index=True)

        with tab_inactivos:
            st.markdown("**Historial de jugadores retirados o vetados**")

            if not df_inactivos.empty:
                registros_por_pagina = 100
                total_registros = len(df_inactivos)

                df_inactivos_visual = df_inactivos.rename(columns={
                    'nombre': 'Nombre',
                    'clase': 'Clase',
                    'resonancia': 'Resonancia',
                    'ic': 'IC',
                    'estado': 'Estado',
                    'fecha_baja': 'Fecha Baja',
                    'motivo_baja': 'Motivo de Baja',
                    'baja_realizada_por': 'Baja realizada por'
                })

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
                    df_mostrar = df_inactivos_visual.iloc[inicio:fin]

                    st.info(
                        f"Mostrando registros **{inicio + 1} al {min(fin, total_registros)}** de un total de {total_registros}.")
                    st.dataframe(
                        df_mostrar, use_container_width=True, hide_index=True)
                else:
                    # Si hay menos de 100, se muestran todos normalmente
                    st.dataframe(
                        df_inactivos_visual, use_container_width=True, hide_index=True)
            else:
                st.info("No hay miembros inactivos registrados en el historial.")

        with tab_buscador:
            st.subheader("🔍 Buscador Avanzado e Historial de Personajes")
            st.markdown("Filtra y analiza el expediente completo de cualquier jugador activo o inactivo del clan.")

            # --- Rango dinámico para Sliders ---
            try:
                conexion_rango = conectar_bd()
                cursor_r = conexion_rango.cursor()
                cursor_r.execute("SELECT MAX(resonancia) as max_res, MAX(ic) as max_ic FROM miembros")
                rango_data = cursor_r.fetchone()
                conexion_rango.close()
                limite_res = int(rango_data[0]) if (rango_data and rango_data[0] is not None) else 7000
                limite_ic = int(rango_data[1]) if (rango_data and rango_data[1] is not None) else 40000
            except:
                limite_res = 7000
                limite_ic = 40000
            
            limite_res = max(limite_res, 100)
            limite_ic = max(limite_ic, 100)

            # Controles interactivos de Filtro
            col_fil1, col_fil2, col_fil3 = st.columns(3)
            with col_fil1:
                nombre_busqueda = st.text_input("Buscar por Nombre (Nick):", placeholder="🔍 Ej: Juan...").strip()
            with col_fil2:
                clases_busqueda = st.multiselect(
                    "Filtrar por Clase:",
                    ["Nigromante", "Guerrero Divino", "Cazador de Demonios", "Bárbaro", "Monje", "Arcanista", "Druida", "Tempestario", "Caballero Sangriento"]
                )
            with col_fil3:
                solo_activos_sel = st.checkbox("Mostrar solo jugadores ACTIVOS", value=True)

            col_slide1, col_slide2 = st.columns(2)
            with col_slide1:
                rango_reso = st.slider("Rango de Resonancia:", 0, limite_res, (0, limite_res), step=50)
            with col_slide2:
                rango_ic = st.slider("Rango de Índice de Combate (IC):", 0, limite_ic, (0, limite_ic), step=50)

            # Carga completa para el buscador
            try:
                conexion_b = conectar_bd()
                df_todos = pd.read_sql_query(
                    "SELECT id, nombre, clase, resonancia, ic, telefono, usa_discord, usa_whatsapp, estado, fecha_ingreso, fecha_baja, alta_realizada_por, baja_realizada_por, motivo_baja, armadura, penetracion_armadura, potencia, resistencia, velocidad_ataque, reduccion_recuperacion, duracion_beneficiosos, rango_sombra FROM miembros ORDER BY nombre",
                    conexion_b
                )
                conexion_b.close()
            except:
                df_todos = pd.DataFrame()

            if not df_todos.empty:
                # Aplicación de filtros
                df_filtrado = df_todos.copy()
                if nombre_busqueda:
                    df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(nombre_busqueda, case=False)]
                if clases_busqueda:
                    df_filtrado = df_filtrado[df_filtrado['clase'].isin(clases_busqueda)]
                if solo_activos_sel:
                    df_filtrado = df_filtrado[df_filtrado['estado'] == 'Activo']
                
                df_filtrado = df_filtrado[
                    (df_filtrado['resonancia'] >= rango_reso[0]) & (df_filtrado['resonancia'] <= rango_reso[1]) &
                    (df_filtrado['ic'] >= rango_ic[0]) & (df_filtrado['ic'] <= rango_ic[1])
                ]

                if df_filtrado.empty:
                    st.info("⚠️ Ningún miembro coincide con los criterios de búsqueda seleccionados.")
                else:
                    st.write(f"💡 Se encontraron **{len(df_filtrado)}** personajes que coinciden con los filtros.")
                    opciones_nombres = df_filtrado['nombre'].tolist()
                    jugador_seleccionado = st.selectbox("Selecciona un miembro para desplegar su ficha histórica:", opciones_nombres)

                    if jugador_seleccionado:
                        row = df_filtrado[df_filtrado['nombre'] == jugador_seleccionado].iloc[0]
                        miembro_id = int(row['id'])

                        # Carga cruzada de datos históricos
                        try:
                            conexion_cruzada = conectar_bd()
                            # 1. Combate
                            df_combate = pd.read_sql_query(
                                "SELECT SUM(kills) as t_kills, SUM(asistencias) as t_asist, SUM(muertes_sufridas) as t_muertes, COUNT(id) as total_batallas FROM estadisticas_guerra WHERE miembro_id = ?",
                                conexion_cruzada, params=(miembro_id,)
                            )
                            # 2. Asistencias (Con evento_id para filtrar)
                            df_asist_hist = pd.read_sql_query(
                                "SELECT asistio_realmente, intencion, fecha, evento_id FROM asistencia WHERE miembro_id = ? ORDER BY fecha DESC",
                                conexion_cruzada, params=(miembro_id,)
                            )
                            # 3. Sanciones
                            df_sanciones_hist = pd.read_sql_query(
                                "SELECT s.motivo, s.fecha, t.nombre as tipo FROM sanciones s JOIN tipos_sancion t ON s.tipo_sancion_id = t.id WHERE s.miembro_id = ? ORDER BY s.fecha DESC",
                                conexion_cruzada, params=(miembro_id,)
                            )
                            conexion_cruzada.close()
                        except:
                            df_combate = pd.DataFrame()
                            df_asist_hist = pd.DataFrame()
                            df_sanciones_hist = pd.DataFrame()

                        # Cálculos matemáticos
                        t_kills = int(df_combate['t_kills'].iloc[0]) if (not df_combate.empty and pd.notna(df_combate['t_kills'].iloc[0])) else 0
                        t_asist = int(df_combate['t_asist'].iloc[0]) if (not df_combate.empty and pd.notna(df_combate['t_asist'].iloc[0])) else 0
                        t_muertes = int(df_combate['t_muertes'].iloc[0]) if (not df_combate.empty and pd.notna(df_combate['t_muertes'].iloc[0])) else 0
                        total_batallas = int(df_combate['total_batallas'].iloc[0]) if (not df_combate.empty and pd.notna(df_combate['total_batallas'].iloc[0])) else 0
                        
                        muertes_reales = t_muertes if t_muertes > 0 else 1
                        kda = round((t_kills + t_asist) / muertes_reales, 2)

                        # --- CÁLCULOS DE ASISTENCIA DETALLADOS ---
                        total_eventos = len(df_asist_hist)
                        asistencias_reales = len(df_asist_hist[df_asist_hist['asistio_realmente'] == 1]) if not df_asist_hist.empty else 0
                        porcentaje_asistencia = round((asistencias_reales / total_eventos) * 100, 1) if total_eventos > 0 else 0
                        infracciones = len(df_asist_hist[(df_asist_hist['asistio_realmente'] == 0) & (df_asist_hist['intencion'] == 'Sí puedo')]) if not df_asist_hist.empty else 0

                        # 1. Guerra de Sombras (evento_id IN (1, 2))
                        if not df_asist_hist.empty and 'evento_id' in df_asist_hist.columns and 'asistio_realmente' in df_asist_hist.columns:
                            df_guerra = df_asist_hist[df_asist_hist['evento_id'].isin([1, 2])]
                            participaciones_guerra = len(df_guerra[df_guerra['asistio_realmente'] == 1])
                            total_guerra = len(df_guerra)
                            pct_guerra = round((participaciones_guerra / total_guerra) * 100, 1) if total_guerra > 0 else 0.0
                            ultima_guerra_row = df_guerra[df_guerra['asistio_realmente'] == 1]
                            ultima_guerra = ultima_guerra_row['fecha'].iloc[0] if not ultima_guerra_row.empty else "Ninguna"
                        else:
                            participaciones_guerra = 0
                            pct_guerra = 0.0
                            ultima_guerra = "Ninguna"

                        # 2. Actividades del Clan (Todas)
                        participaciones_clan = asistencias_reales
                        total_clan = total_eventos
                        pct_clan = porcentaje_asistencia
                        resumen_clan = f"Asistió a {participaciones_clan} de {total_clan} eventos convocados. Infracciones: {infracciones}."

                        advertencias = len(df_sanciones_hist[df_sanciones_hist['tipo'] == 'Parcial']) if not df_sanciones_hist.empty else 0
                        veto = len(df_sanciones_hist[df_sanciones_hist['tipo'] == 'Definitiva']) if not df_sanciones_hist.empty else 0

                        # Atributos Secundarios (Informativos, vacíos en esta versión)
                        def display_val(val):
                            if pd.isna(val) or val is None or str(val).strip() == "":
                                return ""
                            return str(val)

                        armadura = display_val(row.get('armadura'))
                        pen_armadura = display_val(row.get('penetracion_armadura'))
                        potencia = display_val(row.get('potencia'))
                        resistencia = display_val(row.get('resistencia'))
                        vel_ataque = display_val(row.get('velocidad_ataque'))
                        red_recup = display_val(row.get('reduccion_recuperacion'))
                        dur_benef = display_val(row.get('duracion_beneficiosos'))
                        rango_sombra = display_val(row.get('rango_sombra'))

                        # ==========================================
                        # TARJETA/FICHA PREMIUM (3 COLUMNAS)
                        # ==========================================
                        st.write("")
                        st.markdown(f"### 🛡️ Expediente Oficial: **{jugador_seleccionado}**")
                        
                        col_c1, col_c2, col_c3 = st.columns(3)
                        
                        # Columna 1: Perfil
                        with col_c1:
                            st.markdown(
                                f"""
                                <div style='background-color: #1e2732; padding: 20px; border-radius: 10px; border-left: 5px solid #4DA8DA; min-height: 380px;'>
                                    <h4 style='color: #4DA8DA; margin-top: 0;'>👤 Datos de Perfil</h4>
                                    <p style='margin: 4px 0;'><b>Estado:</b> {'🟢 Activo' if row['estado'] == 'Activo' else '🔴 ' + row['estado']}</p>
                                    <p style='margin: 4px 0;'><b>Clase:</b> {row['clase']}</p>
                                    <p style='margin: 4px 0;'><b>Resonancia:</b> {row['resonancia']:,} 💎</p>
                                    <p style='margin: 4px 0;'><b>Índice de Combate (IC):</b> {row['ic']:,} ⚔️</p>
                                    <p style='margin: 4px 0;'><b>Teléfono:</b> {row['telefono'] if row['telefono'] else 'Sin contacto'}</p>
                                    <p style='margin: 4px 0;'><b>Canales:</b> {'📱 WhatsApp ' if row['usa_whatsapp'] else ''}{'🎮 Discord' if row['usa_discord'] else ''}</p>
                                    <p style='margin: 4px 0;'><b>Alta:</b> {row['fecha_ingreso']}</p>
                                    <hr style='border-color: #2c3e50; margin: 10px 0;'>
                                    <h5 style='color: #4DA8DA; margin: 5px 0;'>Atributos Secundarios:</h5>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Armadura:</b> {armadura}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Penetración de Armadura:</b> {pen_armadura}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Potencia:</b> {potencia}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Resistencia:</b> {resistencia}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Velocidad de Ataque:</b> {vel_ataque}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Reducción de Recuperación de Habilidades:</b> {red_recup}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Duración de Efectos Beneficiosos:</b> {dur_benef}</p>
                                    <p style='margin: 2px 0; font-size: 0.9em;'><b>Rango de Sombra Actual:</b> {rango_sombra}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                        # Columna 2: Desempeño
                        with col_c2:
                            badge_guerra = ""
                            if kda >= 3.0:
                                badge_guerra = "<span style='background-color: #2ecc71; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>🔥 ÉLITE</span>"
                            elif kda >= 1.5:
                                badge_guerra = "<span style='background-color: #3498db; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>⚔️ COMBATIENTE</span>"
                            elif total_batallas > 0:
                                badge_guerra = "<span style='background-color: #f1c40f; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>⚠️ PRÁCTICA</span>"
                            else:
                                badge_guerra = "<span style='background-color: #7f8c8d; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>SIN REGISTROS</span>"

                            st.markdown(
                                f"""
                                <div style='background-color: #1e2732; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; min-height: 380px;'>
                                    <h4 style='color: #2ecc71; margin-top: 0;'>⚔️ Desempeño de Guerra</h4>
                                    <p style='margin: 8px 0;'><b>Batallas Registradas:</b> {total_batallas}</p>
                                    <p style='margin: 8px 0;'><b>Kills Totales:</b> {t_kills} 💀</p>
                                    <p style='margin: 8px 0;'><b>Asistencias Totales:</b> {t_asist} 🛡️</p>
                                    <p style='margin: 8px 0;'><b>Muertes Totales:</b> {t_muertes} ⚰️</p>
                                    <p style='margin: 8px 0;'><b>Ratio de Efectividad (KDA):</b> <span style='font-size: 1.2em; font-weight: bold; color: #2ecc71;'>{kda}</span></p>
                                    <div style='margin-top: 15px;'>{badge_guerra}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # Columna 3: Asistencia y Compromiso
                        with col_c3:
                            color_compromiso = "#2ecc71"
                            badge_compromiso = "<span style='background-color: #2ecc71; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>🏆 IMPECABLE</span>"
                            
                            if veto > 0 or row['estado'] == 'Expulsado':
                                color_compromiso = "#e74c3c"
                                badge_compromiso = "<span style='background-color: #e74c3c; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>🚫 VETADO</span>"
                            elif infracciones > 1 or advertencias > 1:
                                color_compromiso = "#e67e22"
                                badge_compromiso = "<span style='background-color: #e67e22; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>🚨 EN ALERTA</span>"
                            elif porcentaje_asistencia < 60.0 and total_eventos > 2:
                                color_compromiso = "#f1c40f"
                                badge_compromiso = "<span style='background-color: #f1c40f; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;'>⚠️ BAJO</span>"

                            st.markdown(
                                f"""
                                <div style='background-color: #1e2732; padding: 20px; border-radius: 10px; border-left: 5px solid {color_compromiso}; min-height: 380px;'>
                                    <h4 style='color: {color_compromiso}; margin-top: 0;'>⚖️ Actividad del Clan</h4>
                                    <p style='margin: 6px 0; font-size: 1.0em;'><b>🏰 Guerra de Sombras:</b></p>
                                    <p style='margin: 4px 15px; font-size: 0.95em;'>• Participaciones: {participaciones_guerra}</p>
                                    <p style='margin: 4px 15px; font-size: 0.95em;'>• Asistencia: {pct_guerra}%</p>
                                    <p style='margin: 4px 15px; font-size: 0.95em;'>• Última: {ultima_guerra}</p>
                                    <p style='margin: 6px 0; font-size: 1.0em;'><b>📅 Actividades del Clan (General):</b></p>
                                    <p style='margin: 4px 15px; font-size: 0.95em;'>• Participaciones: {participaciones_clan}</p>
                                    <p style='margin: 4px 15px; font-size: 0.95em;'>• Asistencia: {pct_clan}%</p>
                                    <p style='margin: 4px 15px; font-size: 0.9em; color: #a0a0a0;'>• Resumen: {resumen_clan}</p>
                                    <div style='margin-top: 15px;'>{badge_compromiso}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # --- Tablas Expandibles Detalladas ---
                        st.write("")
                        col_hist1, col_hist2 = st.columns(2)
                        with col_hist1:
                            with st.expander("📅 Bitácora Reciente de Asistencias (Últimos 10 eventos)"):
                                if not df_asist_hist.empty:
                                    df_asist_show = df_asist_hist.copy()
                                    df_asist_show['asistio_realmente'] = df_asist_show['asistio_realmente'].apply(lambda x: '🟢 Sí' if x == 1 else '🔴 No')
                                    df_asist_show.rename(columns={'asistio_realmente': 'Asistió Realmente', 'intencion': 'Voto en WhatsApp', 'fecha': 'Fecha Evento'}, inplace=True)
                                    st.dataframe(df_asist_show.head(10), use_container_width=True, hide_index=True)
                                else:
                                    st.info("Este miembro no posee convocatorias de asistencia registradas.")
                        
                        with col_hist2:
                            with st.expander("⚖️ Bitácora de Sanciones y Advertencias Históricas"):
                                if not df_sanciones_hist.empty:
                                    df_sanc_show = df_sanciones_hist.copy()
                                    df_sanc_show.rename(columns={'motivo': 'Motivo / Causa', 'fecha': 'Fecha Registro', 'tipo': 'Tipo de Sanción'}, inplace=True)
                                    st.dataframe(df_sanc_show, use_container_width=True, hide_index=True)
                                else:
                                    st.success("Expediente limpio. No posee advertencias ni sanciones registradas. ✨")
            else:
                st.info("No se encontraron miembros registrados en la base de datos.")

    except Exception as e:
        st.error(
            f"⚠️ No se pudieron cargar los datos en este momento. Error: {e}")
