import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from database import conectar_bd


def mostrar():
    st.title("🚪 Gestión de Ingresos y Salidas del Clan")

    # 1. Control de Permisos Dinámico
    es_admin = st.session_state.get('rol') == 'admin'

    nombres_pestanas = ["🆕 Alta Individual",
                        "❌ Baja Individual", "🔍 Buscar y Modificar"]
    if es_admin:
        nombres_pestanas.extend(["📥 Alta Masiva (CSV)", "💥 Baja Masiva"])

    pestanas = st.tabs(nombres_pestanas)

    tab_alta = pestanas[0]
    tab_baja = pestanas[1]
    tab_modificar = pestanas[2]

    if es_admin:
        tab_alta_masiva = pestanas[3]
        tab_baja_masiva = pestanas[4]

    # ==========================================
    # PESTAÑA 1: ALTA INDIVIDUAL
    # ==========================================
    with tab_alta:
        st.subheader("Formulario de Registro Obligatorio")
        nombre_nuevo = st.text_input("Nombre del Personaje (Nick):").strip()

        if nombre_nuevo:
            veto_definitivo, advertencia_parcial, motivo_previo, miembro_bd = False, False, "", None
            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute(
                    "SELECT id, estado FROM miembros WHERE LOWER(nombre) = LOWER(?)", (nombre_nuevo,))
                miembro_bd = cursor.fetchone()
                cursor.execute('''SELECT t.nombre, s.motivo FROM sanciones s 
                                JOIN tipos_sancion t ON s.tipo_sancion_id = t.id
                                JOIN miembros m ON s.miembro_id = m.id
                                WHERE LOWER(m.nombre) = LOWER(?) ORDER BY s.id DESC LIMIT 1''', (nombre_nuevo,))
                sancion = cursor.fetchone()
                conexion.close()

                if sancion:
                    if sancion[0] == 'Definitiva':
                        veto_definitivo, motivo_previo = True, sancion[
                            1] if sancion[1] else "No especificado."
                    elif sancion[0] == 'Parcial':
                        advertencia_parcial, motivo_previo = True, sancion[
                            1] if sancion[1] else "No especificado."
            except Exception:
                st.error("Error al consultar antecedentes.")

            if miembro_bd and miembro_bd[1] == 'Activo':
                st.info(
                    f"ℹ️ El jugador **{nombre_nuevo}** ya es un miembro **ACTIVO**.")
            elif veto_definitivo:
                st.error(
                    f"🚫 **REGISTRO BLOQUEADO:** Vetado definitivamente. Motivo: {motivo_previo}")
            else:
                desea_baja_inmediata = False
                if advertencia_parcial:
                    st.warning(
                        f"⚠️ **ALERTA DE REINCIDENCIA:** Tiene una advertencia parcial previa. Motivo: {motivo_previo}")
                    desea_baja_inmediata = st.checkbox(
                        "🚨 ¿Desea aplicar el veto definitivo en lugar de admitirlo?")
                    if desea_baja_inmediata:
                        motivo_baja = st.text_area(
                            "Motivo de la expulsión:", value=f"Acumulación de advertencias. Falta previa: {motivo_previo}")
                        if st.button("❌ Confirmar Expulsión"):
                            try:
                                conexion_write = conectar_bd()
                                cursor_write = conexion_write.cursor()
                                usuario_actual = st.session_state.get('usuario', 'Desconocido')
                                if miembro_bd:
                                    cursor_write.execute("UPDATE miembros SET estado='Expulsado', fecha_baja=?, motivo_baja=?, baja_realizada_por=? WHERE id=?", (
                                        str(date.today()), motivo_baja, usuario_actual, miembro_bd[0]))
                                    cursor_write.execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 2, ?, ?)", (
                                        miembro_bd[0], motivo_baja, str(date.today())))
                                else:
                                    cursor_write.execute(
                                        "INSERT INTO miembros (nombre, estado, clase, resonancia, ic, fecha_baja, motivo_baja, baja_realizada_por) VALUES (?, 'Expulsado', 'Desconocida', 0, 0, ?, ?, ?)", (
                                            nombre_nuevo, str(date.today()), motivo_baja, usuario_actual))
                                    nuevo_id = cursor_write.lastrowid
                                    cursor_write.execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 2, ?, ?)", (
                                        nuevo_id, motivo_baja, str(date.today())))
                                conexion_write.commit()
                                conexion_write.close()
                                st.success(
                                    "🚫 ¡Jugador vetado definitivamente!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                if not desea_baja_inmediata:
                    with st.form("form_alta_normal"):
                        clase_nueva = st.selectbox("Clase:", ["Nigromante", "Guerrero Divino", "Cazador de Demonios",
                                                   "Bárbaro", "Monje", "Arcanista", "Druida", "Tempestario", "Caballero Sangriento"])
                        col_a, col_b = st.columns(2)
                        with col_a:
                            reso_nueva = st.number_input(
                                "Resonancia:", min_value=0, step=50)
                            telefono_nuevo = st.text_input(
                                "Teléfono de Contacto:").strip()
                        with col_b:
                            ic_nuevo = st.number_input(
                                "Índice de Combate (IC):", min_value=0, step=10)
                            fecha_ingreso = st.date_input(
                                "Fecha de Ingreso:", date.today())

                        check_wa = st.checkbox("¿Está en WhatsApp?")
                        check_disc = st.checkbox("¿Está en Discord?")
                        btn_alta = st.form_submit_button("💾 Guardar Miembro")

                        if btn_alta:
                            if not telefono_nuevo or reso_nueva <= 0 or ic_nuevo <= 0:
                                st.error(
                                    "⚠️ Teléfono, Resonancia e IC son campos obligatorios y mayores a cero.")
                            else:
                                try:
                                    conexion_write = conectar_bd()
                                    cursor_write = conexion_write.cursor()
                                    usuario_actual = st.session_state.get('usuario', 'Desconocido')
                                    if miembro_bd:
                                        cursor_write.execute("UPDATE miembros SET clase=?, resonancia=?, ic=?, telefono=?, usa_discord=?, usa_whatsapp=?, fecha_ingreso=?, estado='Activo', fecha_baja=NULL, alta_realizada_por=? WHERE id=?", (
                                            clase_nueva, reso_nueva, ic_nuevo, telefono_nuevo, check_disc, check_wa, str(fecha_ingreso), usuario_actual, miembro_bd[0]))
                                    else:
                                        cursor_write.execute("INSERT INTO miembros (nombre, clase, resonancia, ic, telefono, usa_discord, usa_whatsapp, fecha_ingreso, estado, alta_realizada_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Activo', ?)", (
                                            nombre_nuevo, clase_nueva, reso_nueva, ic_nuevo, telefono_nuevo, check_disc, check_wa, str(fecha_ingreso), usuario_actual))
                                    conexion_write.commit()
                                    conexion_write.close()
                                    st.success(
                                        f"✅ ¡{nombre_nuevo} dado de alta con éxito!")
                                except Exception as e:
                                    st.error(f"Error al guardar: {e}")

    # ==========================================
    # PESTAÑA 2: BAJA INDIVIDUAL
    # ==========================================
    with tab_baja:
        st.subheader("Formulario de Salida del Clan")
        try:
            conexion = conectar_bd()
            df_activos = pd.read_sql_query(
                "SELECT id, nombre FROM miembros WHERE estado='Activo' ORDER BY nombre", conexion)
            conexion.close()
        except:
            df_activos = pd.DataFrame()

        if not df_activos.empty:
            with st.form("form_baja"):
                miembro_baja = st.selectbox(
                    "Seleccionar Miembro:", df_activos['nombre'])
                fecha_baja = st.date_input("Fecha de Baja:", date.today())
                motivo_baja = st.text_area("Motivo de la baja:").strip()
                es_veto = st.checkbox("🚨 Agregar a Vetados (Definitiva)")
                if st.form_submit_button("❌ Procesar Baja"):
                    if not motivo_baja:
                        st.error("⚠️ Obligatorio especificar motivo.")
                    else:
                        try:
                            conexion_write = conectar_bd()
                            cursor_write = conexion_write.cursor()
                            miembro_id = df_activos[df_activos['nombre']
                                                    == miembro_baja]['id'].values[0]
                            nuevo_estado = 'Expulsado' if es_veto else 'Inactivo'
                            usuario_actual = st.session_state.get('usuario', 'Desconocido')
                            cursor_write.execute("UPDATE miembros SET estado=?, fecha_baja=?, motivo_baja=?, baja_realizada_por=? WHERE id=?", (
                                nuevo_estado, str(fecha_baja), motivo_baja, usuario_actual, int(miembro_id)))
                            if es_veto:
                                cursor_write.execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 2, ?, ?)", (int(
                                    miembro_id), motivo_baja, str(fecha_baja)))
                            conexion_write.commit()
                            conexion_write.close()
                            st.success(f"❌ {miembro_baja} dado de baja.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # ==========================================
    # PESTAÑA 3: BUSCAR Y MODIFICAR
    # ==========================================
    with tab_modificar:
        st.subheader("🔍 Buscar y Modificar Miembro")
        st.markdown(
            "Busca a un jugador para actualizar sus estadísticas. **Esta acción no altera sus fechas de ingreso o baja históricas.**")

        filtro_estado = st.radio("Filtro de búsqueda:", [
                                 "Activos", "Inactivos/Expulsados", "Todos"], horizontal=True)

        try:
            conexion = conectar_bd()
            if filtro_estado == "Activos":
                query = "SELECT * FROM miembros WHERE estado='Activo' ORDER BY nombre"
            elif filtro_estado == "Inactivos/Expulsados":
                query = "SELECT * FROM miembros WHERE estado IN ('Inactivo', 'Expulsado') ORDER BY nombre"
            else:
                query = "SELECT * FROM miembros ORDER BY nombre"

            df_busqueda = pd.read_sql_query(query, conexion)
            conexion.close()
        except Exception:
            df_busqueda = pd.DataFrame()

        if not df_busqueda.empty:
            jugador_sel = st.selectbox(
                "Selecciona el jugador a modificar:", df_busqueda['nombre'])
            jugador_data = df_busqueda[df_busqueda['nombre']
                                       == jugador_sel].iloc[0]

            color_estado = "green" if jugador_data['estado'] == 'Activo' else "red"
            st.markdown(
                f"Modificando a: **{jugador_sel}** | Estado actual: <span style='color:{color_estado}; font-weight:bold'>{jugador_data['estado']}</span>", unsafe_allow_html=True)

            with st.form("form_modificar"):
                clases_permitidas = ["Nigromante", "Guerrero Divino", "Cazador de Demonios", "Bárbaro",
                                     "Monje", "Arcanista", "Druida", "Tempestario", "Caballero Sangriento", "Desconocida"]
                clase_actual = jugador_data['clase']
                idx_clase = clases_permitidas.index(
                    clase_actual) if clase_actual in clases_permitidas else 0

                clase_mod = st.selectbox(
                    "Clase:", clases_permitidas, index=idx_clase)

                col_a, col_b = st.columns(2)
                with col_a:
                    reso_mod = st.number_input(
                        "Resonancia:", min_value=0, step=50, value=int(jugador_data['resonancia']))
                    telefono_mod = st.text_input("Teléfono de Contacto:", value=str(
                        jugador_data['telefono'] if pd.notna(jugador_data['telefono']) else "")).strip()
                with col_b:
                    ic_mod = st.number_input(
                        "Índice de Combate (IC):", min_value=0, step=10, value=int(jugador_data['ic']))

                check_wa_mod = st.checkbox(
                    "¿Está en WhatsApp?", value=bool(jugador_data['usa_whatsapp']))
                check_disc_mod = st.checkbox(
                    "¿Está en Discord?", value=bool(jugador_data['usa_discord']))

                if st.form_submit_button("💾 Guardar Cambios"):
                    if not telefono_mod or reso_mod <= 0 or ic_mod <= 0:
                        st.error(
                            "⚠️ Teléfono, Resonancia e IC son campos obligatorios y mayores a cero.")
                    else:
                        try:
                            conexion_write = conectar_bd()
                            cursor_write = conexion_write.cursor()
                            cursor_write.execute('''
                                UPDATE miembros 
                                SET clase=?, resonancia=?, ic=?, telefono=?, usa_discord=?, usa_whatsapp=? 
                                WHERE id=?
                            ''', (clase_mod, reso_mod, ic_mod, telefono_mod, check_disc_mod, check_wa_mod, int(jugador_data['id'])))
                            conexion_write.commit()
                            conexion_write.close()
                            st.success(
                                f"✅ ¡Datos de **{jugador_sel}** actualizados sin afectar su antigüedad!")
                        except Exception as e:
                            st.error(f"Error al modificar: {e}")
        else:
            st.info("No se encontraron jugadores bajo el filtro seleccionado.")

    # ==========================================
    # PESTAÑAS ADMINISTRADOR
    # ==========================================
    if es_admin:
        with tab_alta_masiva:
            st.subheader("📥 Carga y Actualización Masiva")
            st.markdown(
                "Sube un archivo `.csv` o `.xlsx` estructurado para actualizar o registrar múltiples miembros del clan.")
            
            # --- Generador Dinámico de Plantilla Excel ---
            import io
            df_plantilla = pd.DataFrame(columns=['Nombre', 'Clase', 'Resonancia', 'IC', 'Telefono', 'WhatsApp', 'Discord'])
            # Fila de ejemplo
            df_plantilla.loc[0] = ['EjemploNombre', 'Nigromante', 1000, 15000, '+123456789', 'Si', 'Si']
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_plantilla.to_excel(writer, index=False, sheet_name='Plantilla Roster')
            buffer.seek(0)
            
            st.download_button(
                label="📥 Descargar Plantilla Excel (.xlsx)",
                data=buffer,
                file_name="plantilla_miembros_dunedain.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga una plantilla de ejemplo estructurada para rellenar tus datos masivamente"
            )
            
            st.info("💡 **Regla de actualización masiva:**\n"
                    "- Si el jugador **ya existe y está activo**, se actualizarán su Clase, Resonancia, IC, Teléfono, WhatsApp y Discord con los nuevos datos.\n"
                    "- Si el jugador **ya existía pero estaba inactivo/expulsado**, se reactivará (estado 'Activo') y se actualizarán sus estadísticas (excepto si tiene veto definitivo).\n"
                    "- Si el jugador es **nuevo**, se creará desde cero en estado 'Activo' con toda su información provista.")

            archivo_masivo = st.file_uploader(
                "Subir archivo de roster (.csv o .xlsx):", type=['csv', 'xlsx'])

            if archivo_masivo:
                if st.button("🚀 Procesar Carga Masiva", type="primary"):
                    try:
                        df_masivo = pd.read_csv(archivo_masivo) if archivo_masivo.name.endswith(
                            '.csv') else pd.read_excel(archivo_masivo)
                        df_masivo.columns = [str(c).strip()
                                             for c in df_masivo.columns]

                        if 'Nombre' not in df_masivo.columns:
                            st.error(
                                "❌ El archivo debe contener obligatoriamente una columna llamada 'Nombre'.")
                        else:
                            conexion = conectar_bd()
                            cursor = conexion.cursor()
                            hoy = str(date.today())
                            usuario_actual = st.session_state.get('usuario', 'Desconocido')

                            # Listas para reporte visual
                            lista_nuevos = []
                            lista_actualizados = []
                            lista_reingresos = []
                            lista_bloqueados = []

                            for _, fila in df_masivo.iterrows():
                                nom = str(fila['Nombre']).strip()
                                if not nom or nom.lower() == 'nan':
                                    continue

                                # Funciones auxiliares robustas de parseo
                                def limpiar_string(val, default=""):
                                    if pd.isna(val) or str(val).strip().lower() == 'nan':
                                        return default
                                    return str(val).strip()

                                def limpiar_int(val, default=0):
                                    try:
                                        if pd.isna(val):
                                            return default
                                        return int(float(val))
                                    except:
                                        return default

                                cla = limpiar_string(fila.get('Clase'), 'Desconocida')
                                res = limpiar_int(fila.get('Resonancia'), 0)
                                ic = limpiar_int(fila.get('IC'), 0)
                                tel = limpiar_string(fila.get('Telefono'), '')
                                if tel.endswith('.0'):
                                    tel = tel[:-2]  # Corregir floats tipo "12345.0"
                                
                                wa_str = limpiar_string(fila.get('WhatsApp'), 'No').lower()
                                disc_str = limpiar_string(fila.get('Discord'), 'No').lower()
                                
                                wa = 1 if wa_str in ['si', 'sí', 'yes', 'true', '1'] else 0
                                disc = 1 if disc_str in ['si', 'sí', 'yes', 'true', '1'] else 0

                                # Consultar existencia en base de datos
                                cursor.execute(
                                    "SELECT id, estado FROM miembros WHERE LOWER(nombre) = LOWER(?)", (nom,))
                                bd_data = cursor.fetchone()

                                if bd_data:
                                    id_jugador, estado_actual = bd_data[0], bd_data[1]
                                    
                                    # Verificar veto definitivo antes de cualquier acción
                                    cursor.execute(
                                        "SELECT 1 FROM sanciones s JOIN tipos_sancion t ON s.tipo_sancion_id = t.id WHERE s.miembro_id=? AND t.nombre='Definitiva'", (id_jugador,))
                                    if cursor.fetchone():
                                        lista_bloqueados.append(nom)
                                    else:
                                        if estado_actual != 'Activo':
                                            # Reactivar y actualizar estadísticas completas
                                            cursor.execute('''
                                                UPDATE miembros 
                                                SET estado='Activo', fecha_ingreso=?, fecha_baja=NULL, clase=?, resonancia=?, ic=?, telefono=?, usa_discord=?, usa_whatsapp=?, alta_realizada_por=? 
                                                WHERE id=?
                                            ''', (hoy, cla, res, ic, tel, disc, wa, usuario_actual, id_jugador))
                                            lista_reingresos.append(nom)
                                        else:
                                            # Actualizar estadísticas manteniendo la antigüedad
                                            cursor.execute('''
                                                UPDATE miembros 
                                                SET clase=?, resonancia=?, ic=?, telefono=?, usa_discord=?, usa_whatsapp=? 
                                                WHERE id=?
                                            ''', (cla, res, ic, tel, disc, wa, id_jugador))
                                            lista_actualizados.append(nom)
                                else:
                                    # Insertar miembro completamente nuevo
                                    cursor.execute('''
                                        INSERT INTO miembros 
                                        (nombre, clase, resonancia, ic, telefono, usa_discord, usa_whatsapp, fecha_ingreso, estado, alta_realizada_por) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Activo', ?)
                                    ''', (nom, cla, res, ic, tel, disc, wa, hoy, usuario_actual))
                                    lista_nuevos.append(nom)

                            conexion.commit()
                            conexion.close()

                            st.success(f"🎉 ¡Procesamiento masivo finalizado exitosamente!")

                            if lista_nuevos:
                                st.warning(f"🆕 **{len(lista_nuevos)} Nuevos Miembros Registrados:**")
                                st.markdown(", ".join(lista_nuevos))

                            if lista_actualizados:
                                st.info(f"🔄 **{len(lista_actualizados)} Miembros Activos Actualizados:**")
                                st.markdown(", ".join(lista_actualizados))

                            if lista_reingresos:
                                st.success(f"✨ **{len(lista_reingresos)} Reingresos Exitosos (Ex-miembros reactivados):**")
                                st.markdown(", ".join(lista_reingresos))

                            if lista_bloqueados:
                                st.error(f"🚫 **Se ignoraron por poseer Veto Definitivo:** {', '.join(lista_bloqueados)}")

                            if not lista_nuevos and not lista_actualizados and not lista_reingresos and not lista_bloqueados:
                                st.info("Todos los jugadores del archivo ya se encontraban activos e idénticos en el sistema.")

                    except Exception as e:
                        st.error(f"Error al procesar el archivo: {e}")

        with tab_baja_masiva:
            st.subheader("💥 Limpieza General de Miembros")
            st.error(
                "⚠️ **ESTA ACCIÓN ES IRREVERSIBLE:** Dará de baja a TODOS los miembros activos del clan, cambiándolos a estado 'Inactivo'.")
            
            motivo_masivo = st.text_area("Motivo de la baja masiva (Ej: Fin de ciclo, limpieza de temporada, etc.):").strip()
            st.markdown("¿Desea continuar con la baja masiva?")

            col_si, col_no = st.columns(2)

            with col_si:
                if st.button("✔️ Sí, dar de baja a todos", type="primary", use_container_width=True):
                    if not motivo_masivo:
                        st.error("❌ El motivo de la baja masiva es obligatorio.")
                    else:
                        try:
                            conexion = conectar_bd()
                            cursor = conexion.cursor()
                            hoy = str(date.today())
                            usuario_actual = st.session_state.get('usuario', 'Desconocido')

                            cursor.execute(
                                "UPDATE miembros SET estado='Inactivo', fecha_baja=?, motivo_baja=?, baja_realizada_por=? WHERE estado='Activo'", 
                                (hoy, motivo_masivo, usuario_actual)
                            )
                            afectados = cursor.rowcount
                            conexion.commit()
                            conexion.close()

                            st.success(
                                f"✅ Baja masiva ejecutada. {afectados} miembros pasaron a estado Inactivo.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error crítico en base de datos: {e}")

            with col_no:
                if st.button("❌ No, cancelar acción", use_container_width=True):
                    st.info(
                        "Acción abortada por seguridad. No se alteró ningún registro.")
