import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from database import conectar_bd


def mostrar():
    st.title("⚖️ Registro Central de Sanciones")
    try:
        conexion = conectar_bd()
        df_sanciones = pd.read_sql_query(
            '''SELECT m.nombre AS 'Jugador', t.nombre AS 'Tipo de Sanción', s.motivo AS 'Motivo', s.fecha AS 'Fecha Registro' FROM sanciones s JOIN miembros m ON s.miembro_id = m.id JOIN tipos_sancion t ON s.tipo_sancion_id = t.id ORDER BY s.id DESC''', conexion)
        df_activos = pd.read_sql_query(
            "SELECT id, nombre FROM miembros WHERE estado='Activo' ORDER BY nombre", conexion)
        conexion.close()
    except Exception:
        df_sanciones, df_activos = pd.DataFrame(), pd.DataFrame()

    st.subheader("Lista Negra y Alertas Vigentes")
    if not df_sanciones.empty:
        st.dataframe(df_sanciones, use_container_width=True, hide_index=True)
    else:
        st.info("El historial está limpio.")

    st.divider()
    st.subheader("➕ Registrar Nueva Advertencia a Activo")
    if not df_activos.empty:
        miembro_adv = st.selectbox(
            "Seleccionar Jugador:", df_activos['nombre'])
        miembro_id = int(
            df_activos[df_activos['nombre'] == miembro_adv]['id'].values[0])

        alerta_previa = None
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT s.motivo, s.fecha FROM sanciones s JOIN tipos_sancion t ON s.tipo_sancion_id = t.id WHERE s.miembro_id = ? AND t.nombre = 'Parcial' ORDER BY s.id DESC LIMIT 1", (miembro_id,))
            alerta_previa = cursor.fetchone()
            conexion.close()
        except Exception:
            pass

        if alerta_previa:
            st.warning(
                f"⚠️ **REINCIDENCIA:** {miembro_adv} ya tiene advertencia. Fecha: {alerta_previa[1]}. Motivo: {alerta_previa[0]}")
            if st.checkbox("🚨 Aplicar Veto Definitivo y Dar de Baja"):
                motivo_expulsion = st.text_area("Motivo de expulsión:")
                if st.button("❌ Confirmar Expulsión", type="primary"):
                    if motivo_expulsion:
                        conexion_write = conectar_bd()
                        cursor_write = conexion_write.cursor()
                        cursor_write.execute("UPDATE miembros SET estado='Expulsado', fecha_baja=? WHERE id=?", (str(
                            date.today()), miembro_id))
                        cursor_write.execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 2, ?, ?)", (
                            miembro_id, motivo_expulsion, str(date.today())))
                        conexion_write.commit()
                        conexion_write.close()
                        st.success("🚫 Expulsado.")
                    else:
                        st.error("Ingresa motivo.")
            else:
                motivo_adv_nuevo = st.text_input("Nueva advertencia:")
                if st.button("⚠️ Acumular Advertencia"):
                    if motivo_adv_nuevo:
                        conexion_write = conectar_bd()
                        conexion_write.cursor().execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 1, ?, ?)",
                                                        (miembro_id, motivo_adv_nuevo, str(date.today())))
                        conexion_write.commit()
                        st.success("⚠️ Advertencia sumada.")
        else:
            with st.form("form_sancion_manual"):
                motivo_adv = st.text_input("Razón:")
                if st.form_submit_button("⚠️ Registrar Advertencia") and motivo_adv:
                    conexion_write = conectar_bd()
                    conexion_write.cursor().execute("INSERT INTO sanciones (miembro_id, tipo_sancion_id, motivo, fecha) VALUES (?, 1, ?, ?)",
                                                    (miembro_id, motivo_adv, str(date.today())))
                    conexion_write.commit()
                    st.success("⚠️ Registrado.")
