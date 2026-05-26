import streamlit as st
import pandas as pd
import sqlite3
from database import conectar_bd


def calcular_efectividad(kills, asistencias, muertes):
    # Fórmula estándar KDA (Kills, Deaths, Assists) para medir eficiencia en juegos.
    # Si las muertes son 0, usamos 1 para evitar un error matemático de división por cero.
    muertes_reales = muertes if muertes > 0 else 1
    return round((kills + asistencias) / muertes_reales, 2)


def mostrar():
    st.title("⚔️ Estadísticas de Combate")
    st.markdown(
        "Sube los resultados de la guerra para evaluar la efectividad del clan.")

    # ==========================================
    # SECCIÓN 1: VALIDACIÓN Y CARGA DEL ARCHIVO
    # ==========================================
    st.subheader("📤 Subir Resultados (Solo CSV o XLSX)")
    archivo = st.file_uploader(
        "Arrastra aquí el archivo de estadísticas de la batalla", type=['csv', 'xlsx'])

    if archivo is not None:
        try:
            # Detectar formato
            if archivo.name.endswith('.csv'):
                df_subido = pd.read_csv(archivo)
            else:
                df_subido = pd.read_excel(archivo)

            # --- VALIDACIÓN 1: Columnas requeridas ---
            columnas_requeridas = ['Jugador',
                                   'Muertes', 'Asistencias', 'Kills']
            columnas_archivo = [c.strip() for c in df_subido.columns]
            df_subido.columns = columnas_archivo  # Normalizar espacios en blanco

            faltan = [
                col for col in columnas_requeridas if col not in columnas_archivo]

            if faltan:
                st.error(f"❌ **Estructura de archivo inválida.**")
                st.warning(
                    f"Faltan las siguientes columnas: {', '.join(faltan)}")
                st.info(
                    "Asegúrate de que la primera fila de tu archivo tenga exactamente estas palabras: Jugador, Muertes, Asistencias, Kills.")
            else:
                # Limpiar datos: Convertir posibles espacios vacíos en 0
                for col in ['Muertes', 'Asistencias', 'Kills']:
                    df_subido[col] = pd.to_numeric(
                        df_subido[col], errors='coerce').fillna(0).astype(int)

                # --- VALIDACIÓN 2: Verificación estricta de Activos ---
                conexion = conectar_bd()
                df_activos = pd.read_sql_query(
                    "SELECT id, nombre FROM miembros WHERE estado='Activo'", conexion)
                conexion.close()

                miembros_bd = {fila['nombre'].lower(): fila['id']
                               for _, fila in df_activos.iterrows()}

                no_registrados = []
                registros_validos = []

                for _, fila in df_subido.iterrows():
                    nom = str(fila['Jugador']).strip()
                    nom_lower = nom.lower()

                    if nom_lower in miembros_bd:
                        efectividad = calcular_efectividad(
                            fila['Kills'], fila['Asistencias'], fila['Muertes'])
                        registros_validos.append((
                            miembros_bd[nom_lower],
                            "Global",  # Se elimina el concepto de ciclo en este módulo según tu solicitud
                            fila['Kills'],
                            fila['Asistencias'],
                            fila['Muertes'],
                            efectividad
                        ))
                    else:
                        no_registrados.append(nom)

                # Si hay UN solo jugador que no está activo, el sistema se bloquea por seguridad.
                if no_registrados:
                    st.error(
                        "🚫 **CARGA BLOQUEADA: Jugadores no registrados o dados de baja detectados.**")
                    st.warning(", ".join(set(no_registrados)))
                    st.info("💡 Solución: El sistema no guarda datos de personas ajenas al clan. Ve a 'Alta / Baja' para ingresarlos o corrige sus nombres en tu archivo Excel y vuelve a subirlo.")
                else:
                    st.success(
                        f"✅ Archivo perfecto. Se detectaron {len(registros_validos)} jugadores activos listos para guardar.")

                    # Vista previa interactiva de lo que se va a guardar
                    df_subido['Efectividad'] = df_subido.apply(lambda x: calcular_efectividad(
                        x['Kills'], x['Asistencias'], x['Muertes']), axis=1)
                    st.dataframe(df_subido, use_container_width=True)

                    if st.button("💾 Confirmar y Guardar Estadísticas", type="primary"):
                        try:
                            conexion_write = conectar_bd()
                            cursor = conexion_write.cursor()
                            cursor.executemany('''
                                INSERT INTO estadisticas_guerra 
                                (miembro_id, ciclo, kills, asistencias, muertes_sufridas, puntaje_porcentaje) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', registros_validos)
                            conexion_write.commit()
                            conexion_write.close()
                            st.success(
                                "🎉 ¡Estadísticas guardadas en el registro histórico!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error técnico al guardar: {e}")

        except Exception as e:
            st.error(
                f"❌ Error al leer el archivo. Asegúrate de que el documento no esté dañado. ({e})")

    st.divider()

    # ==========================================
    # SECCIÓN 2: GRILLA Y MÉTRICAS DEL CLAN
    # ==========================================
    st.subheader("🏆 Desempeño Histórico del Clan (Solo Activos)")

    try:
        conexion = conectar_bd()
        # Esta consulta cruza los miembros con sus estadísticas.
        # El "WHERE m.estado = 'Activo'" asegura que si das de baja a alguien, desaparece automáticamente de aquí.
        query = '''
            SELECT 
                m.nombre AS Jugador,
                m.clase AS Clase,
                SUM(e.kills) AS Total_Kills,
                SUM(e.asistencias) AS Total_Asistencias,
                SUM(e.muertes_sufridas) AS Total_Muertes
            FROM miembros m
            LEFT JOIN estadisticas_guerra e ON m.id = e.miembro_id
            WHERE m.estado = 'Activo'
            GROUP BY m.id
        '''
        df_stats = pd.read_sql_query(query, conexion)
        conexion.close()

        # Limpieza para aquellos que son nuevos y aún no tienen guerras jugadas
        df_stats.fillna(0, inplace=True)
        for col in ['Total_Kills', 'Total_Asistencias', 'Total_Muertes']:
            df_stats[col] = df_stats[col].astype(int)

        # Calcular el puntaje para la grilla
        df_stats['Puntaje Efectividad'] = df_stats.apply(lambda x: calcular_efectividad(
            x['Total_Kills'], x['Total_Asistencias'], x['Total_Muertes']), axis=1)

        # Separar solo a los que ya han participado en guerras para las métricas globales
        df_participantes = df_stats[df_stats['Total_Kills'] +
                                    df_stats['Total_Asistencias'] + df_stats['Total_Muertes'] > 0]

        if not df_participantes.empty:
            # --- AGREGADO: MÉTRICAS GLOBALES EN LA PARTE SUPERIOR ---
            kills_clan = df_participantes['Total_Kills'].sum()
            asistencias_clan = df_participantes['Total_Asistencias'].sum()
            muertes_clan = df_participantes['Total_Muertes'].sum()
            efectividad_clan = calcular_efectividad(
                kills_clan, asistencias_clan, muertes_clan)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("⚔️ Kills del Clan", f"{kills_clan:,}")
            col2.metric("🛡️ Asistencias del Clan", f"{asistencias_clan:,}")
            col3.metric("💀 Muertes Sufridas", f"{muertes_clan:,}")
            col4.metric("🔥 Efectividad Global",
                        f"{efectividad_clan}", help="Métrica global basada en la fórmula KDA")

            # --- AGREGADO: PODIO DE LOS MEJORES JUGADORES (MVPs) ---
            st.write("")
            st.markdown("### 🥇 Top 3 MVPs del Clan")
            top_3 = df_participantes.sort_values(
                by='Puntaje Efectividad', ascending=False).head(3).reset_index()

            t_cols = st.columns(3)
            medallas = ["🥇 1er Lugar", "🥈 2do Lugar", "🥉 3er Lugar"]
            for i in range(len(top_3)):
                with t_cols[i]:
                    st.info(
                        f"**{medallas[i]}**\n\n**{top_3.loc[i, 'Jugador']}** ({top_3.loc[i, 'Clase']})\n\nPuntaje: **{top_3.loc[i, 'Puntaje Efectividad']}**")

            # --- AGREGADO: GRILLA INTERACTIVA CON BUSCADOR ---
            st.write("")
            st.markdown("### 📊 Grilla Completa de Personajes")
            st.info("💡 **Buscador habilitado:** Pasa el ratón sobre la tabla y usa el ícono de la lupa 🔍 en la esquina superior derecha para buscar un jugador específico.")

            st.dataframe(
                df_stats.sort_values(
                    by='Puntaje Efectividad', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(
                "Aún no hay datos de combate registrados. ¡Sube tu primer archivo CSV o XLSX de guerra para comenzar!")

    except Exception as e:
        st.error(f"Error al cargar la visualización de estadísticas: {e}")
