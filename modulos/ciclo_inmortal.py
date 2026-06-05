import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import conectar_bd, obtener_ciclo_activo


def calcular_duracion(desde_str, hasta_str=None):
    try:
        formato = "%Y-%m-%d"
        desde = datetime.strptime(desde_str, formato).date()
        if hasta_str:
            hasta = datetime.strptime(hasta_str, formato).date()
            dias = (hasta - desde).days
            semanas = round(dias / 7, 1)
            return f"{dias} días ({semanas} semanas)"
        else:
            hoy = date.today()
            dias = (hoy - desde).days
            semanas = round(dias / 7, 1)
            return f"{semanas} semanas"
    except Exception:
        return "Error en fechas"


def mostrar():
    st.title("⏳ Administrar Ciclos Inmortales")
    st.markdown(
        "Gestiona los ciclos del servidor inmortal. Permite crear nuevos ciclos, cerrar los actuales y auditar históricos.")

    # Control estricto de permisos
    if st.session_state.get('rol') != 'admin':
        st.error("🚫 Acceso denegado. Este módulo solo está disponible para Administradores.")
        return

    ciclo_activo = obtener_ciclo_activo()

    # ==========================================
    # SECCIÓN 1: PANEL SUPERIOR (ESTADO ACTUAL)
    # ==========================================
    st.subheader("📊 Estado del Ciclo Inmortal")
    if ciclo_activo:
        c_id, c_desde, _ = ciclo_activo
        duracion = calcular_duracion(c_desde)
        st.success(f"🟢 **Ciclo {c_id} Activo**")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Fecha de Inicio", c_desde)
        col_m2.metric("Semanas Transcurridas", duracion)
    else:
        st.warning("⚠️ No existe un ciclo inmortal activo en el sistema.")

    st.divider()

    # ==========================================
    # SECCIÓN 2: OPERACIONES (ALTA Y CIERRE)
    # ==========================================
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("🆕 Crear Nuevo Ciclo Inmortal")
        with st.form("form_crear_ciclo"):
            fecha_desde = st.date_input("Fecha Desde (Inicio del Ciclo):", date.today())
            btn_crear = st.form_submit_button("🚀 Crear Ciclo Inmortal")

            if btn_crear:
                # REGLA 1 y 2: Unicidad de ciclo activo
                if ciclo_activo:
                    st.error("❌ Ya existe un ciclo inmortal activo. Debe cerrarlo antes de crear uno nuevo.")
                else:
                    fecha_desde_str = str(fecha_desde)
                    try:
                        conexion = conectar_bd()
                        cursor = conexion.cursor()

                        # REGLA 9: Validar superposición con períodos registrados
                        cursor.execute("SELECT MAX(fecha_hasta) FROM ciclos_inmortales")
                        max_hasta_res = cursor.fetchone()

                        superposicion = False
                        max_hasta_val = None
                        if max_hasta_res and max_hasta_res[0]:
                            max_hasta_val = datetime.strptime(max_hasta_res[0], "%Y-%m-%d").date()
                            if fecha_desde <= max_hasta_val:
                                superposicion = True

                        if superposicion:
                            st.error(f"❌ La fecha desde ({fecha_desde_str}) se superpone con un período ya registrado (Último ciclo finalizó el {max_hasta_val}).")
                        else:
                            cursor.execute(
                                "INSERT INTO ciclos_inmortales (fecha_desde, estado) VALUES (?, 'Activo')",
                                (fecha_desde_str,)
                            )
                            conexion.commit()
                            st.success("🎉 Ciclo inmortal creado exitosamente.")
                            st.rerun()
                        conexion.close()
                    except Exception as e:
                        st.error(f"Error al acceder a la base de datos: {e}")

    with col_der:
        st.subheader("🔒 Cerrar Ciclo Inmortal Activo")
        with st.form("form_cerrar_ciclo"):
            fecha_hasta = st.date_input("Fecha Hasta (Fin del Ciclo):", date.today())
            btn_cerrar = st.form_submit_button("🔒 Finalizar Ciclo Activo")

            if btn_cerrar:
                # REGLA 10: Validar existencia de ciclo activo
                if not ciclo_activo:
                    st.error("❌ No existe un ciclo inmortal activo en el sistema.")
                else:
                    c_id, c_desde, _ = ciclo_activo
                    c_desde_date = datetime.strptime(c_desde, "%Y-%m-%d").date()

                    # REGLA 4: Fecha Hasta >= Fecha Desde
                    if fecha_hasta < c_desde_date:
                        st.error("❌ La fecha hasta debe ser mayor o igual a la fecha desde.")
                    else:
                        try:
                            conexion = conectar_bd()
                            cursor = conexion.cursor()
                            cursor.execute(
                                "UPDATE ciclos_inmortales SET fecha_hasta = ?, estado = 'Finalizado' WHERE id = ?",
                                (str(fecha_hasta), c_id)
                            )
                            conexion.commit()
                            conexion.close()
                            st.success(f"🎉 Ciclo {c_id} cerrado y guardado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al cerrar el ciclo: {e}")

    st.divider()

    # ==========================================
    # SECCIÓN 3: LISTADO HISTÓRICO Y ELIMINACIÓN
    # ==========================================
    st.subheader("📋 Historial de Ciclos Inmortales")
    try:
        conexion = conectar_bd()
        df_ciclos = pd.read_sql_query("SELECT id, fecha_desde, fecha_hasta, estado FROM ciclos_inmortales ORDER BY id DESC", conexion)
        conexion.close()
    except Exception:
        df_ciclos = pd.DataFrame()

    if not df_ciclos.empty:
        # Calcular duraciones para mostrar en la grilla
        df_ciclos['Duración'] = df_ciclos.apply(lambda r: calcular_duracion(r['fecha_desde'], r['fecha_hasta']), axis=1)
        
        # Renombrar columnas para la grilla visual
        df_mostrar = df_ciclos.rename(columns={
            'id': 'ID Ciclo',
            'fecha_desde': 'Fecha Desde',
            'fecha_hasta': 'Fecha Hasta',
            'estado': 'Estado'
        })
        st.dataframe(df_mostrar[['ID Ciclo', 'Fecha Desde', 'Fecha Hasta', 'Estado', 'Duración']], use_container_width=True, hide_index=True)

        # Formulario para eliminar ciclo
        st.write("")
        st.markdown("##### 🗑️ Eliminar Ciclo Histórico (Acción Protegida)")
        with st.form("form_eliminar_ciclo"):
            ciclo_a_eliminar = st.selectbox("Seleccionar ciclo a eliminar:", df_ciclos['id'])
            confirmar_del = st.checkbox("Confirmar que desea eliminar permanentemente este ciclo")
            btn_eliminar = st.form_submit_button("🗑️ Eliminar Ciclo")

            if btn_eliminar:
                if not confirmar_del:
                    st.warning("⚠️ Debes activar la casilla de confirmación para eliminar.")
                else:
                    ciclo_str = f"Ciclo {ciclo_a_eliminar}"
                    try:
                        conexion = conectar_bd()
                        cursor = conexion.cursor()

                        # REGLA 7: No eliminar ciclo con información asociada
                        cursor.execute("SELECT COUNT(*) FROM asistencia WHERE ciclo = ?", (ciclo_str,))
                        cont_asist = cursor.fetchone()[0]

                        cursor.execute("SELECT COUNT(*) FROM estadisticas_guerra WHERE ciclo = ?", (ciclo_str,))
                        cont_stats = cursor.fetchone()[0]

                        if cont_asist > 0 or cont_stats > 0:
                            st.error("❌ No es posible eliminar un ciclo que posee información asociada.")
                            st.info(f"💡 Detalle de asociaciones: {cont_asist} registros de asistencia, {cont_stats} de estadísticas de guerra.")
                        else:
                            cursor.execute("DELETE FROM ciclos_inmortales WHERE id = ?", (int(ciclo_a_eliminar),))
                            conexion.commit()
                            st.success(f"🗑️ Ciclo {ciclo_a_eliminar} eliminado con éxito.")
                            st.rerun()
                        conexion.close()
                    except Exception as e:
                        st.error(f"Error de base de datos al eliminar: {e}")
    else:
        st.info("No hay ciclos inmortales registrados en el sistema.")
