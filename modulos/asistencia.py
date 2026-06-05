import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import date
from database import conectar_bd, obtener_ciclo_activo


def preparar_bd():
    """Actualiza la tabla asistencia agregando las nuevas columnas si no existen."""
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(
            "ALTER TABLE asistencia ADD COLUMN intencion TEXT DEFAULT 'No votó'")
        cursor.execute(
            "ALTER TABLE asistencia ADD COLUMN asistio_realmente INTEGER DEFAULT 0")
        conexion.commit()
        conexion.close()
    except sqlite3.OperationalError:
        # Si da error es porque las columnas ya fueron creadas anteriormente, continuamos normal.
        pass


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
    tab_encuesta, tab_real, tab_auditoria = st.tabs([
        "📱 1. Cargar Votos (WhatsApp)",
        "✅ 2. Cargar Asistencia Real",
        "📊 3. Auditoría de Asistencia"
    ])

    # Función auxiliar para procesar listas de nombres y guardarlas en la BD
    def procesar_y_guardar(lista_cruda, campo_bd, valor_guardar):
        nombres = [nom.strip() for nom in re.split(
            r'[,\n\t]+', lista_cruda) if nom.strip()]
        if not nombres:
            return 0, []

        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre FROM miembros WHERE estado='Activo'")
        miembros_activos = {fila[1].lower(): fila[0]
                            for fila in cursor.fetchall()}

        encontrados = 0
        no_registrados = []

        for nom in nombres:
            nom_l = nom.lower()
            if nom_l in miembros_activos:
                m_id = miembros_activos[nom_l]

                # Buscamos si ya tiene registro para este evento
                cursor.execute("SELECT id FROM asistencia WHERE miembro_id=? AND evento_id=? AND ciclo=? AND fecha=?",
                               (m_id, int(evento_id), ciclo, str(fecha_evento)))
                registro = cursor.fetchone()

                if registro:
                    cursor.execute(
                        f"UPDATE asistencia SET {campo_bd}=? WHERE id=?", (valor_guardar, registro[0]))
                else:
                    # Si no existe, creamos el registro inicializando las variables
                    intencion_val = valor_guardar if campo_bd == 'intencion' else 'No votó'
                    asistio_val = valor_guardar if campo_bd == 'asistio_realmente' else 0

                    cursor.execute('''INSERT INTO asistencia 
                                      (miembro_id, evento_id, ciclo, fecha, estado_asistencia, intencion, asistio_realmente) 
                                      VALUES (?, ?, ?, ?, 'Procesado', ?, ?)''',
                                   (m_id, int(evento_id), ciclo, str(fecha_evento), intencion_val, asistio_val))
                encontrados += 1
            else:
                no_registrados.append(nom)

        conexion.commit()
        conexion.close()
        return encontrados, no_registrados

    # --- PASO 1: CARGA DE ENCUESTA ---
    with tab_encuesta:
        st.subheader("Resultados de la Encuesta Previa")
        st.markdown(
            "Pega aquí las listas de jugadores debajo de cada opción de tu encuesta de WhatsApp.")

        col_si, col_no, col_duda = st.columns(3)
        with col_si:
            txt_si = st.text_area("🟢 Votaron: SÍ PUEDO", height=200)
        with col_no:
            txt_no = st.text_area("🔴 Votaron: NO PUEDO", height=200)
        with col_duda:
            txt_duda = st.text_area("🟡 Votaron: NO ASEGURO", height=200)

        if st.button("💾 Guardar Encuesta", type="primary"):
            errores_globales = []
            exito_total = 0

            e1, err1 = procesar_y_guardar(txt_si, 'intencion', 'Sí puedo')
            e2, err2 = procesar_y_guardar(txt_no, 'intencion', 'No puedo')
            e3, err3 = procesar_y_guardar(txt_duda, 'intencion', 'No aseguro')

            exito_total = e1 + e2 + e3
            errores_globales.extend(err1 + err2 + err3)

            if exito_total > 0:
                st.success(
                    f"✅ Se registraron las intenciones de {exito_total} miembros activos.")
            if errores_globales:
                st.error("❌ Los siguientes nombres no están en la lista de activos o están mal escritos:\n" +
                         ", ".join(set(errores_globales)))

    # --- PASO 2: CARGA REAL ---
    with tab_real:
        st.subheader("Asistencia Comprobada In-Game")
        col_izq, col_der = st.columns([2, 1])
        texto_real = ""

        with col_izq:
            tab_texto, tab_archivo = st.tabs(
                ["📋 Pegar Nombres", "📁 Subir Archivo"])
            with tab_texto:
                nombres_reales = st.text_area(
                    "Pega los nombres de los que asistieron al juego:", height=200, key="txt_real")
                if nombres_reales:
                    texto_real = nombres_reales
            with tab_archivo:
                archivo_subido = st.file_uploader(
                    "Sube un archivo con los nombres", type=['txt', 'csv'])
                if archivo_subido is not None:
                    texto_real = archivo_subido.getvalue().decode("utf-8")
                    st.success("✅ Archivo leído correctamente.")

        with col_der:
            st.info("💡 Al guardar, el sistema marcará a estas personas como presentes y cruzará los datos con lo que votaron en la encuesta.")
            if st.button("🚀 Guardar Asistencia Real", use_container_width=True, type="primary"):
                if texto_real.strip():
                    exitos, errores = procesar_y_guardar(
                        texto_real, 'asistio_realmente', 1)
                    if exitos > 0:
                        st.success(
                            f"✅ Se marcó la asistencia real de {exitos} miembros.")
                    if errores:
                        st.error(
                            "❌ Nombres no encontrados en activos:\n" + ", ".join(set(errores)))
                else:
                    st.warning("No has ingresado ningún nombre o archivo.")

    # --- PASO 3: AUDITORÍA ---
    with tab_auditoria:
        st.subheader("Reporte de Cumplimiento")

        if st.button("🔄 Generar / Actualizar Reporte", use_container_width=True):
            try:
                conexion = conectar_bd()
                query_activos = "SELECT id, nombre, clase FROM miembros WHERE estado='Activo'"
                query_asistencia = "SELECT miembro_id, intencion, asistio_realmente FROM asistencia WHERE evento_id=? AND fecha=? AND ciclo=?"

                df_activos = pd.read_sql_query(query_activos, conexion)
                df_asistencia = pd.read_sql_query(query_asistencia, conexion, params=(
                    int(evento_id), str(fecha_evento), ciclo))
                conexion.close()

                # Unimos todos los miembros activos con sus registros de asistencia de hoy
                df_final = pd.merge(
                    df_activos, df_asistencia, left_on='id', right_on='miembro_id', how='left')
                df_final['intencion'] = df_final['intencion'].fillna('No votó')
                df_final['asistio_realmente'] = df_final['asistio_realmente'].fillna(
                    0).astype(int)

                # Lógica visual para detectar infractores
                def determinar_estado(row):
                    voto = row['intencion']
                    fue = row['asistio_realmente']

                    if fue == 1:
                        if voto == 'No votó':
                            return "🟢 Asistió (Presente Sorpresa)"
                        return "🟢 Asistió al Evento"
                    else:
                        if voto == 'Sí puedo':
                            return "🚨 INFRACCIÓN (Faltó tras confirmar)"
                        elif voto == 'No puedo':
                            return "⚪ Ausencia Justificada"
                        elif voto == 'No aseguro':
                            return "🟠 Ausente (Avisó duda)"
                        else:
                            return "🟡 Ausente Injustificado (No votó)"

                df_final['Estado Final'] = df_final.apply(
                    determinar_estado, axis=1)

                # Seleccionar columnas para mostrar
                df_mostrar = df_final[['nombre', 'clase', 'intencion', 'Estado Final']].rename(
                    columns={'nombre': 'Jugador', 'clase': 'Clase',
                             'intencion': 'Voto en WhatsApp'}
                )

                # Métricas Rápidas
                total = len(df_mostrar)
                asistieron = len(df_final[df_final['asistio_realmente'] == 1])
                infractores = len(
                    df_final[df_final['Estado Final'].str.contains('INFRACCIÓN')])

                c1, c2, c3 = st.columns(3)
                c1.metric("👥 Activos Convocados", total)
                c2.metric("⚔️ Asistencia Real",
                          f"{asistieron} ({round((asistieron/total)*100, 1) if total > 0 else 0}%)")
                c3.metric("🚨 Infracciones (Confirmó y no fue)", infractores)

                st.dataframe(df_mostrar.sort_values(by='Estado Final'),
                             use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Ocurrió un error al generar el reporte: {e}")
