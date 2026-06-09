import streamlit as st
import sqlite3
import pandas as pd
import re
import os
import sys
from datetime import date
from database import conectar_bd, obtener_ciclo_activo
import pytesseract
from PIL import Image, ImageOps

# Configurar ruta de tesseract en Windows si aplica
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extraer_nombres_ocr(imagen_upload):
    try:
        image = Image.open(imagen_upload)
        # Preprocesamiento obligatorio: escala de grises y mejora de contraste
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        
        # Intentar extraer texto con español (spa) e inglés (eng) por compatibilidad
        texto = pytesseract.image_to_string(image, lang='spa+eng')
        return [line.strip() for line in texto.split('\n') if line.strip()]
    except pytesseract.pytesseract.TesseractNotFoundError:
        st.error("⚠️ El motor Tesseract-OCR no está instalado en este sistema o no se encuentra en el PATH. Si estás en local en Windows, asegúrate de instalar Tesseract en 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'.")
        return []
    except Exception as e:
        st.error(f"Error al procesar la imagen: {e}")
        return []

def limpiar_lineas_ocr(lineas):
    lineas_limpias = []
    for linea in lineas:
        l = linea.strip()
        # Omitir si es muy corta (basura)
        if len(l) < 3:
            continue
        
        # Eliminar marcas de tiempo (ej: "12:30", "12:30 p.m.", "12:30 pm", "15:45", etc.)
        l = re.sub(r'\b\d{1,2}:\d{2}(?:\s?[ap]\.?\s?m\.?)?\b', '', l, flags=re.IGNORECASE)
        
        # Eliminar números de orden, guiones y caracteres extraños al inicio (ej. "1. ", "+ ", "- ", etc.)
        l_clean = re.sub(r'^[+\d\.\-\s]+', '', l)
        
        # Quitar emoticonos
        l_clean = re.sub(r'[\u2600-\u27BF\U0001f300-\U0001f64f\U0001f680-\U0001f6ff]', '', l_clean)
        l_clean = l_clean.strip()
        
        # Omitir palabras basura comunes de la interfaz de WhatsApp
        l_lower = l_clean.lower()
        palabras_basura = [
            "voto", "votos", "encuesta", "creador", "creó", "opciones", 
            "responder", "reenviar", "copiar", "eliminar", "info", "detalles",
            "ayer", "hoy", "pm", "am", "p.m.", "a.m."
        ]
        es_basura = False
        for wb in palabras_basura:
            if wb in l_lower:
                es_basura = True
                break
        if es_basura:
            continue
        
        if len(l_clean) >= 3:
            lineas_limpias.append(l_clean)
            
    return list(set(lineas_limpias))



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
        st.subheader("Resultados de la Encuesta Previa (WhatsApp)")
        st.markdown(
            "Sube capturas de pantalla de los votos de WhatsApp para procesarlos con OCR. Puedes subir múltiples capturas por opción.")

        col_si, col_no, col_duda = st.columns(3)
        with col_si:
            files_si = st.file_uploader("🟢 Votaron: SÍ PUEDO", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="files_si")
        with col_no:
            files_no = st.file_uploader("🔴 Votaron: NO PUEDO", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="files_no")
        with col_duda:
            files_duda = st.file_uploader("🟡 Votaron: NO ASEGURO", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="files_duda")

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            btn_procesar = st.button("🔍 Procesar Imágenes", type="primary", use_container_width=True)
        with col_btn2:
            btn_limpiar = st.button("🗑️ Limpiar Carga", use_container_width=True)

        if btn_limpiar:
            for k in ['votos_reconocidos', 'votos_desconocidos', 'votos_no_votaron', 'votos_si_ocr', 'votos_no_ocr', 'votos_duda_ocr']:
                if k in st.session_state:
                    del st.session_state[k]
            st.success("Carga limpiada correctamente.")
            st.rerun()

        if btn_procesar:
            # Procesar "SÍ PUEDO"
            nombres_si = []
            if files_si:
                for f in files_si:
                    nombres_si.extend(extraer_nombres_ocr(f))
            
            # Procesar "NO PUEDO"
            nombres_no = []
            if files_no:
                for f in files_no:
                    nombres_no.extend(extraer_nombres_ocr(f))
                    
            # Procesar "NO ASEGURO"
            nombres_duda = []
            if files_duda:
                for f in files_duda:
                    nombres_duda.extend(extraer_nombres_ocr(f))
                    
            # Limpiar y guardar en session state
            st.session_state['votos_si_ocr'] = limpiar_lineas_ocr(nombres_si)
            st.session_state['votos_no_ocr'] = limpiar_lineas_ocr(nombres_no)
            st.session_state['votos_duda_ocr'] = limpiar_lineas_ocr(nombres_duda)
            
            # Ejecutar análisis
            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("SELECT id, nombre FROM miembros WHERE estado='Activo'")
                miembros_activos = cursor.fetchall()
                
                cursor.execute("SELECT whatsapp_name, miembro_id FROM alias_whatsapp")
                aliases = cursor.fetchall()
                conexion.close()
            except Exception as e:
                st.error(f"Error de base de datos: {e}")
                miembros_activos = []
                aliases = []
                
            miembros_map = {m[1].lower(): (m[0], m[1]) for m in miembros_activos}
            alias_map = {a[0].lower(): a[1] for a in aliases}
            miembro_id_map = {m[0]: m[1] for m in miembros_activos}
            
            reconocidos = []
            desconocidos = []
            reconocidos_ids = set()
            
            votos_por_intencion = [
                ('Sí puedo', st.session_state.get('votos_si_ocr', [])),
                ('No puedo', st.session_state.get('votos_no_ocr', [])),
                ('No aseguro', st.session_state.get('votos_duda_ocr', []))
            ]
            
            for intencion, nombres in votos_por_intencion:
                for nom_wa in nombres:
                    nom_wa_l = nom_wa.lower()
                    if nom_wa_l in miembros_map:
                        m_id, m_nombre = miembros_map[nom_wa_l]
                        reconocidos.append({
                            "nombre_whatsapp": nom_wa,
                            "nombre_miembro": m_nombre,
                            "miembro_id": m_id,
                            "intencion": intencion
                        })
                        reconocidos_ids.add(m_id)
                    elif nom_wa_l in alias_map:
                        m_id = alias_map[nom_wa_l]
                        if m_id in miembro_id_map:
                            reconocidos.append({
                                "nombre_whatsapp": nom_wa,
                                "nombre_miembro": miembro_id_map[m_id],
                                "miembro_id": m_id,
                                "intencion": intencion
                            })
                            reconocidos_ids.add(m_id)
                        else:
                            desconocidos.append({
                                "nombre_whatsapp": nom_wa,
                                "intencion": intencion
                            })
                    else:
                        desconocidos.append({
                            "nombre_whatsapp": nom_wa,
                            "intencion": intencion
                        })
                        
            no_votaron = []
            for m_id, m_nombre in miembros_activos:
                if m_id not in reconocidos_ids:
                    no_votaron.append({
                        "miembro_id": m_id,
                        "nombre": m_nombre
                    })
                    
            st.session_state['votos_reconocidos'] = reconocidos
            st.session_state['votos_desconocidos'] = desconocidos
            st.session_state['votos_no_votaron'] = no_votaron
            
            st.success("🎉 Capturas procesadas correctamente. Valida los resultados abajo.")
            st.rerun()

        # UI de resolución de conflictos y guardado final
        if 'votos_reconocidos' in st.session_state:
            reconocidos = st.session_state.get('votos_reconocidos', [])
            desconocidos = st.session_state.get('votos_desconocidos', [])
            no_votaron = st.session_state.get('votos_no_votaron', [])
            
            st.write("---")
            st.subheader("⚠️ Validación y Resolución de Conflictos")
            
            if desconocidos:
                st.warning(f"Se encontraron **{len(desconocidos)}** nombres de WhatsApp no reconocidos. Debes asociarlos con un miembro activo o elegir 'Ignorar' antes de guardar:")
                
                try:
                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, nombre FROM miembros WHERE estado='Activo' ORDER BY nombre")
                    activos_db = cursor.fetchall()
                    conn.close()
                except:
                    activos_db = []
                    
                opciones_activos = ["Ignorar / No es del clan"] + [a[1] for a in activos_db]
                activos_map = {a[1]: a[0] for a in activos_db}
                
                with st.form("form_alias_resolucion"):
                    resoluciones = {}
                    for i, unk in enumerate(desconocidos):
                        st.markdown(f"Captura: **{unk['nombre_whatsapp']}** (Voto: `{unk['intencion']}`)")
                        resoluciones[i] = st.selectbox(
                            "Asociar con miembro del clan:",
                            opciones_activos,
                            key=f"alias_sel_{i}"
                        )
                        st.write("")
                        
                    btn_guardar_alias = st.form_submit_button("💾 Guardar Alias y Validar")
                    
                    if btn_guardar_alias:
                        nuevos_reconocidos = list(reconocidos)
                        nuevos_desconocidos = []
                        
                        try:
                            conn_alias = conectar_bd()
                            cursor_alias = conn_alias.cursor()
                            
                            for i, unk in enumerate(desconocidos):
                                seleccion = resoluciones[i]
                                if seleccion != "Ignorar / No es del clan":
                                    miembro_id = activos_map[seleccion]
                                    cursor_alias.execute(
                                        "INSERT OR IGNORE INTO alias_whatsapp (whatsapp_name, miembro_id) VALUES (?, ?)",
                                        (unk['nombre_whatsapp'], miembro_id)
                                    )
                                    nuevos_reconocidos.append({
                                        "nombre_whatsapp": unk['nombre_whatsapp'],
                                        "nombre_miembro": seleccion,
                                        "miembro_id": miembro_id,
                                        "intencion": unk['intencion']
                                    })
                                else:
                                    # Si es ignorar, no se agrega a reconocidos ni a desconocidos (se descarta)
                                    pass
                                    
                            conn_alias.commit()
                            conn_alias.close()
                            
                            st.session_state['votos_reconocidos'] = nuevos_reconocidos
                            st.session_state['votos_desconocidos'] = [] # Limpiado
                            
                            reconocidos_ids = {r['miembro_id'] for r in nuevos_reconocidos}
                            nuevos_no_votaron = [nv for nv in no_votaron if nv['miembro_id'] not in reconocidos_ids]
                            st.session_state['votos_no_votaron'] = nuevos_no_votaron
                            
                            st.success("✅ Alias guardados correctamente y lista actualizada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar los alias: {e}")
            else:
                st.success("✨ ¡Todos los nombres reconocidos y validados!")
                
            st.divider()
            st.subheader("💾 Guardado Final")
            st.write(f"📊 **Resumen actual:**")
            st.write(f"- Miembros reconocidos y validados: **{len(reconocidos)}**")
            st.write(f"- Miembros que no votaron: **{len(no_votaron)}**")
            
            aplicar_no_voto = st.checkbox("¿Deseas aplicar la inasistencia (No votó) a los que faltan?", value=True)
            
            guardado_deshabilitado = len(desconocidos) > 0
            if guardado_deshabilitado:
                st.warning("⚠️ Hay nombres desconocidos sin resolver. El guardado final está bloqueado.")
                
            btn_guardar_final = st.button(
                "Confirmar y Guardar Asistencia",
                disabled=guardado_deshabilitado,
                type="primary",
                use_container_width=True
            )
            
            if btn_guardar_final:
                try:
                    conn_save = conectar_bd()
                    cursor_save = conn_save.cursor()
                    
                    # Guardar reconocidos
                    for rec in reconocidos:
                        m_id = rec['miembro_id']
                        intencion_val = rec['intencion']
                        
                        cursor_save.execute("SELECT id FROM asistencia WHERE miembro_id=? AND evento_id=? AND ciclo=? AND fecha=?",
                                            (m_id, int(evento_id), ciclo, str(fecha_evento)))
                        registro = cursor_save.fetchone()
                        
                        if registro:
                            cursor_save.execute(
                                "UPDATE asistencia SET intencion=? WHERE id=?",
                                (intencion_val, registro[0])
                            )
                        else:
                            cursor_save.execute('''INSERT INTO asistencia 
                                              (miembro_id, evento_id, ciclo, fecha, estado_asistencia, intencion, asistio_realmente) 
                                              VALUES (?, ?, ?, ?, 'Procesado', ?, 0)''',
                                           (m_id, int(evento_id), ciclo, str(fecha_evento), intencion_val))
                            
                    # Guardar no votaron si se seleccionó
                    if aplicar_no_voto:
                        for nv in no_votaron:
                            m_id = nv['miembro_id']
                            cursor_save.execute("SELECT id FROM asistencia WHERE miembro_id=? AND evento_id=? AND ciclo=? AND fecha=?",
                                                (m_id, int(evento_id), ciclo, str(fecha_evento)))
                            registro = cursor_save.fetchone()
                            
                            if registro:
                                cursor_save.execute(
                                    "UPDATE asistencia SET intencion='No votó' WHERE id=?",
                                    (registro[0],)
                                )
                            else:
                                cursor_save.execute('''INSERT INTO asistencia 
                                                  (miembro_id, evento_id, ciclo, fecha, estado_asistencia, intencion, asistio_realmente) 
                                                  VALUES (?, ?, ?, ?, 'Procesado', 'No votó', 0)''',
                                               (m_id, int(evento_id), ciclo, str(fecha_evento)))
                                
                    conn_save.commit()
                    conn_save.close()
                    st.success("🎉 ¡Asistencia del evento guardada correctamente en la base de datos!")
                    
                    for k in ['votos_reconocidos', 'votos_desconocidos', 'votos_no_votaron', 'votos_si_ocr', 'votos_no_ocr', 'votos_duda_ocr']:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar asistencia final: {e}")

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
