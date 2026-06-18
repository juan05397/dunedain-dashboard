import streamlit as st
import sqlite3
import pandas as pd
import re
import os
import sys
from datetime import date
from database import conectar_bd, obtener_ciclo_activo

def preparar_bd():
    """Actualiza las tablas agregando las nuevas columnas si no existen."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    # Agregar columnas a la tabla asistencia
    try:
        cursor.execute("ALTER TABLE asistencia ADD COLUMN intencion TEXT DEFAULT 'No votó'")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE asistencia ADD COLUMN asistio_realmente INTEGER DEFAULT 0")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE asistencia ADD COLUMN sala_asignada TEXT DEFAULT 'No asignado'")
    except Exception:
        pass
        
    # Agregar columnas a la tabla estadisticas_guerra
    try:
        cursor.execute("ALTER TABLE estadisticas_guerra ADD COLUMN evento_id INTEGER")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE estadisticas_guerra ADD COLUMN fecha DATE")
    except Exception:
        pass
        
    conexion.commit()
    conexion.close()


def mostrar():
    preparar_bd()  # Ejecutamos la validación de la BD al abrir el módulo

    st.title("📝 Control Maestro de Asistencia")
    st.markdown(
        "Gestiona las encuestas de WhatsApp, registra la asistencia real en el juego y audita el compromiso del clan.")

    # ==========================================
    # CONTROLES GLOBALES DE EVENTO
    # ==========================================
    try:
        conexion = conectar_bd()
        df_eventos = pd.read_sql_query(
            "SELECT id, nombre FROM eventos", conexion)
        conexion.close()
    except Exception:
        df_eventos = pd.DataFrame()

    ciclo_activo = obtener_ciclo_activo()
    if not ciclo_activo:
        st.error("❌ No existe un ciclo inmortal activo en el sistema.")
        st.info("💡 Un administrador debe crear un ciclo inmortal activo para poder gestionar asistencias.")
        return

    ciclo_id = ciclo_activo[0]
    ciclo = f"Ciclo {ciclo_id}"

    col_ev1, col_ev2, col_ev3 = st.columns(3)
    with col_ev1:
        evento_seleccionado = st.selectbox(
            "Evento a gestionar:", df_eventos['nombre'] if not df_eventos.empty else ["Sin eventos"])
    with col_ev2:
        fecha_evento = st.date_input("Fecha del Evento:", date.today())
    with col_ev3:
        st.text_input("Ciclo Activo:", value=f"Ciclo {ciclo_id} (Desde: {ciclo_activo[1]})", disabled=True)

    if df_eventos.empty:
        st.warning("⚠️ No hay eventos creados en la base de datos.")
        return

    evento_id = df_eventos[df_eventos['nombre']
                           == evento_seleccionado]['id'].values[0]

    st.divider()

    # ==========================================
    # PESTAÑAS DEL FLUJO DE TRABAJO
    # ==========================================
    tab_carga, tab_auditoria = st.tabs([
        "📋 Carga de Asistencia y Salas",
        "📊 Auditoría de Asistencia"
    ])

    # Mapeo de intenciones para compatibilidad con el módulo de auditoría
    db_to_ui_intencion = {
        'Sí puedo': 'SÍ PUEDO',
        'No puedo': 'NO PUEDO',
        'No aseguro': 'NO ASEGURO',
        'No votó': 'NO VOTO'
    }

    ui_to_db_intencion = {
        'SÍ PUEDO': 'Sí puedo',
        'NO PUEDO': 'No puedo',
        'NO ASEGURO': 'No aseguro',
        'NO VOTO': 'No votó'
    }

    # --- TAB 1: CARGA DE ASISTENCIA Y SALAS ---
    with tab_carga:
        st.subheader("Planilla de Control de Asistencia y Distribución de Salas")
        st.info("💡 Haz doble clic sobre 'Intención de Voto', 'Sala de Guerra' o 'Asistencia Real' para editar los campos.")

        # Obtener los datos actuales de los miembros activos y cruzar con su asistencia
        try:
            conexion = conectar_bd()
            query_miembros = """
                SELECT 
                    m.id AS miembro_id,
                    m.nombre AS Nombre,
                    m.clase AS Clase,
                    m.resonancia AS Resonancia,
                    a.intencion,
                    a.sala_asignada,
                    a.asistio_realmente
                FROM miembros m
                LEFT JOIN asistencia a ON m.id = a.miembro_id AND a.evento_id = ? AND a.fecha = ?
                WHERE m.estado = 'Activo'
                ORDER BY m.nombre
            """
            df_miembros = pd.read_sql_query(query_miembros, conexion, params=(int(evento_id), str(fecha_evento)))
            conexion.close()
        except Exception as e:
            st.error(f"Error al obtener los miembros: {e}")
            df_miembros = pd.DataFrame()

        if not df_miembros.empty:
            # Mapear valores de base de datos a UI
            df_miembros["Intención de Voto"] = df_miembros["intencion"].map(db_to_ui_intencion).fillna("NO VOTO")
            df_miembros["Sala de Guerra"] = df_miembros["sala_asignada"].fillna("No asignado")
            df_miembros["Asistencia Real"] = df_miembros["asistio_realmente"].apply(lambda x: True if x == 1 else False)

            # Dropear columnas temporales de BD
            df_miembros = df_miembros.drop(columns=["intencion", "sala_asignada", "asistio_realmente"])

            # Asegurar el orden de las columnas para st.data_editor
            df_miembros = df_miembros[["miembro_id", "Nombre", "Clase", "Resonancia", "Intención de Voto", "Sala de Guerra", "Asistencia Real"]]
            
            # Ajustar la numeración de los registros iniciando desde 1 y agregar la columna "Num Activo"
            df_miembros.insert(0, "Num Activo", range(1, len(df_miembros) + 1))

            # Mostrar st.data_editor configurado
            df_editado = st.data_editor(
                df_miembros,
                column_config={
                    "miembro_id": None,  # Oculta la columna del ID de miembro
                    "Num Activo": st.column_config.NumberColumn("Num Activo", disabled=True, format="%d"),
                    "Nombre": st.column_config.TextColumn("Nombre / Jugador", disabled=True),
                    "Clase": st.column_config.TextColumn("Clase", disabled=True),
                    "Resonancia": st.column_config.NumberColumn("Resonancia", disabled=True),
                    "Intención de Voto": st.column_config.SelectboxColumn(
                        "Intención de Voto",
                        options=["NO VOTO", "SÍ PUEDO", "NO PUEDO", "NO ASEGURO"],
                        required=True
                    ),
                    "Sala de Guerra": st.column_config.SelectboxColumn(
                        "Sala de Guerra",
                        options=[
                            "No asignado", "Sala 1 (8 Pts)", "Sala 2 (8 Pts)", "Sala 3 (8 Pts)",
                            "Sala 1 (4 Pts)", "Sala 2 (4 Pts)", "Sala 3 (4 Pts)",
                            "Sala 1 (2 Pts)", "Sala 2 (2 Pts)", "Sala 3 (2 Pts)",
                            "Sala 1 (1 Pt)", "Sala 2 (1 Pt)", "Sala 3 (1 Pt)"
                        ],
                        required=True
                    ),
                    "Asistencia Real": st.column_config.CheckboxColumn("Asistencia Real", default=False)
                },
                disabled=["Num Activo", "Nombre", "Clase", "Resonancia"],
                use_container_width=True,
                hide_index=True,
                key="editor_asistencia_salas_grid"
            )

            # --- CONTADOR DE VOTOS EN TIEMPO REAL ---
            if df_editado is not None and not df_editado.empty:
                st.write("")
                st.markdown("##### 📊 Resumen de Respuestas (WhatsApp)")
                
                # Obtener conteos dinámicos
                votos = df_editado["Intención de Voto"].value_counts()
                si_puedo = int(votos.get("SÍ PUEDO", 0))
                no_puedo = int(votos.get("NO PUEDO", 0))
                no_aseguro = int(votos.get("NO ASEGURO", 0))
                no_voto = int(votos.get("NO VOTO", 0))
                
                col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                with col_v1:
                    st.metric("🟢 SÍ PUEDO", si_puedo)
                with col_v2:
                    st.metric("🔴 NO PUEDO", no_puedo)
                with col_v3:
                    st.metric("🟡 NO ASEGURO", no_aseguro)
                with col_v4:
                    st.metric("⚪ NO VOTO", no_voto)
                
                st.write("")

            # Botón de guardar
            if st.button("💾 Actualizar y Guardar Asistencia y Salas", type="primary", use_container_width=True):
                # 1. Validación de Salas: máximo 8 jugadores por sala (excluyendo "No asignado")
                room_counts = df_editado[df_editado["Sala de Guerra"] != "No asignado"]["Sala de Guerra"].value_counts()
                exceeded_rooms = []
                for room, count in room_counts.items():
                    if count > 8:
                        exceeded_rooms.append(f"**{room}** (tiene {count} jugadores asignados, máximo 8)")

                if exceeded_rooms:
                    st.error("🚫 **El guardado se ha bloqueado porque las siguientes salas superan el límite de 8 jugadores:**\n\n" + "\n".join([f"- {r}" for r in exceeded_rooms]))
                else:
                    try:
                        conexion_save = conectar_bd()
                        cursor_save = conexion_save.cursor()
                        
                        warnings_list = []
                        
                        # 2. Iterar y persistir cambios con UPSERT en asistencia
                        for index, row in df_editado.iterrows():
                            miembro_id = int(row['miembro_id'])
                            jugador = row['Nombre']
                            intencion_ui = row['Intención de Voto']
                            sala_ui = row['Sala de Guerra']
                            asistencia_ui = row['Asistencia Real']
                            
                            # Mapear de regreso a formato de base de datos
                            intencion_db = ui_to_db_intencion.get(intencion_ui, 'No votó')
                            sala_db = sala_ui
                            asistio_realmente_db = 1 if asistencia_ui else 0
                            
                            # Si no asistió, verificar cuántas inasistencias acumuladas posee en el ciclo activo
                            if not asistencia_ui:
                                cursor_save.execute(
                                    "SELECT COUNT(*) FROM asistencia WHERE miembro_id = ? AND ciclo = ? AND asistio_realmente = 0 AND (evento_id != ? OR fecha != ?)",
                                    (miembro_id, ciclo, int(evento_id), str(fecha_evento))
                                )
                                inasistencias_previas = cursor_save.fetchone()[0]
                                total_inasistencias = inasistencias_previas + 1
                                if total_inasistencias >= 3:
                                    warnings_list.append(f"⚠️ **{jugador}** acumula **{total_inasistencias}** inasistencias en el ciclo activo.")
                            
                            # Realizar UPSERT en la tabla asistencia
                            cursor_save.execute(
                                "SELECT id FROM asistencia WHERE miembro_id=? AND evento_id=? AND ciclo=? AND fecha=?",
                                (miembro_id, int(evento_id), ciclo, str(fecha_evento))
                            )
                            registro = cursor_save.fetchone()
                            
                            if registro:
                                cursor_save.execute(
                                    """UPDATE asistencia 
                                       SET intencion=?, sala_asignada=?, asistio_realmente=? 
                                       WHERE id=?""",
                                    (intencion_db, sala_db, asistio_realmente_db, registro[0])
                                )
                            else:
                                cursor_save.execute(
                                    """INSERT INTO asistencia 
                                       (miembro_id, evento_id, ciclo, fecha, estado_asistencia, intencion, sala_asignada, asistio_realmente) 
                                       VALUES (?, ?, ?, ?, 'Procesado', ?, ?, ?)""",
                                    (miembro_id, int(evento_id), ciclo, str(fecha_evento), intencion_db, sala_db, asistio_realmente_db)
                                )
                        
                        conexion_save.commit()
                        conexion_save.close()
                        
                        st.success("✅ Asistencia y distribución de salas guardadas con éxito.")
                        
                        # Disparar alertas de inasistencia acumuladas (si existen)
                        if warnings_list:
                            for warn_msg in warnings_list:
                                st.warning(warn_msg)
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error técnico al guardar los datos: {e}")
        else:
            st.warning("No hay miembros activos registrados en la base de datos.")

    # --- TAB 2: AUDITORÍA ---
    with tab_auditoria:
        st.subheader("Reporte de Cumplimiento Histórico (Ciclo Activo)")
        st.markdown(
            "Visualiza la sábana de asistencia de estilo Excel, análisis de brecha de confirmaciones y KPIs del ciclo.")

        try:
            conexion = conectar_bd()
            # 1. Consulta de Datos (SQL a Pandas)
            query_audit = """
                SELECT m.nombre as jugador, m.clase, e.nombre as evento, a.fecha, a.intencion, a.asistio_realmente
                FROM asistencia a
                JOIN miembros m ON a.miembro_id = m.id
                JOIN eventos e ON a.evento_id = e.id
                WHERE a.ciclo = ?
            """
            df_audit = pd.read_sql_query(query_audit, conexion, params=(ciclo,))
            conexion.close()
        except Exception as e:
            st.error(f"Ocurrió un error al consultar los datos de la base de datos: {e}")
            df_audit = pd.DataFrame()

        # 3. Prevención de Errores (DataFrames Vacíos)
        if df_audit.empty:
            st.info("No hay datos de asistencia para mostrar en este ciclo.")
        else:
            # 2. Panel de KPIs y Estadísticas
            total_eventos = df_audit['fecha'].nunique()
            
            # Promedio de Asistencia General por evento
            asist_por_evento = df_audit.groupby('fecha')['asistio_realmente'].sum()
            total_jugadores_por_evento = df_audit.groupby('fecha')['jugador'].count()
            promedio_asistencia = round((asist_por_evento / total_jugadores_por_evento).mean() * 100, 1) if total_eventos > 0 else 0.0
            
            # Tasa de Cumplimiento (% de veces que los que votaron "Sí puedo" realmente asistieron)
            df_si_puedo = df_audit[df_audit['intencion'] == 'Sí puedo']
            if not df_si_puedo.empty:
                tasa_cumplimiento = round((df_si_puedo['asistio_realmente'].sum() / len(df_si_puedo)) * 100, 1)
            else:
                tasa_cumplimiento = 0.0

            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("📅 Eventos Realizados", total_eventos)
            col_kpi2.metric("⚔️ Promedio Asistencia Real", f"{promedio_asistencia}%")
            col_kpi3.metric("🎯 Tasa de Cumplimiento", f"{tasa_cumplimiento}%")

            st.write("")
            st.divider()
            
            # 3. Gráficos de Análisis de Brecha (Voto vs. Realidad)
            st.subheader("📈 Análisis de Brecha (Voto vs. Realidad)")
            st.markdown("Comparación temporal del total de confirmaciones (WhatsApp) frente a la asistencia real en juego.")
            
            df_brecha = df_audit.groupby('fecha').agg(
                Confirmaron_Si=('intencion', lambda x: (x == 'Sí puedo').sum()),
                Asistieron_Realmente=('asistio_realmente', 'sum')
            ).reset_index()
            
            # Ordenar cronológicamente
            df_brecha = df_brecha.sort_values('fecha')
            
            # Crear un dataframe listo para graficar con nombres de columna amigables
            df_chart = df_brecha.rename(columns={
                'Confirmaron_Si': 'Votaron "Sí puedo" (WhatsApp)',
                'Asistieron_Realmente': 'Asistieron Realmente (In-Game)'
            })
            
            # Graficar usando st.line_chart
            st.line_chart(df_chart.set_index('fecha'))

            st.write("")
            st.divider()

            # 4. Tabla Dinámica Estilo Excel (Sábana de Asistencia)
            st.subheader("📊 Sábana de Asistencia Matricial")
            st.markdown("Matriz histórica de celdas cruzando intenciones y asistencia real para cada fecha.")
            
            # Función lambda para evaluar el cruce de celdas
            def determinar_indicador(row):
                voto = row['intencion']
                fue = row['asistio_realmente']
                
                if fue == 1:
                    if voto in ['No votó', None, '']:
                        return "👻 Fantasma"
                    else:
                        return "✅ OK"
                else:
                    if voto == 'Sí puedo':
                        return "🚨 INFRACCIÓN"
                    elif voto == 'No puedo':
                        return "⚪ Justificado"
                    elif voto == 'No aseguro':
                        return "🟠 Duda"
                    else:
                        return "❌ Ausente"

            df_audit['indicador'] = df_audit.apply(determinar_indicador, axis=1)
            
            # Generar la tabla dinámica pivotada
            df_pivot = pd.pivot_table(
                df_audit,
                index=['jugador', 'clase'],
                columns='fecha',
                values='indicador',
                aggfunc=lambda x: x.iloc[0] if len(x) > 0 else "❌ Ausente"
            )
            
            # Completar registros nulos
            df_pivot = df_pivot.fillna("❌ Ausente")
            
            # Calcular columna acumulativa "Contar Asistencia"
            df_pivot['Contar Asistencia'] = (df_pivot == '✅ OK').sum(axis=1)
            
            # Renombrar índices para presentación visual limpia
            df_pivot_visual = df_pivot.rename_axis(index={'jugador': 'Jugador', 'clase': 'Clase'})
            
            # Mostrar st.dataframe con la columna "Contar Asistencia" resaltada
            st.dataframe(
                df_pivot_visual.style.map(lambda x: 'background-color: #d4edda; color: #155724; font-weight: bold;', subset=['Contar Asistencia']),
                use_container_width=True
            )

            # 5. Funcionalidad de Exportación compatible con Excel (BOM utf-8-sig)
            csv_data = df_pivot_visual.to_csv(index=True).encode('utf-8-sig')
            
            st.download_button(
                label="📥 Descargar Sábana de Asistencia (CSV)",
                data=csv_data,
                file_name=f"sabana_asistencia_{ciclo.replace(' ', '_').lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )
