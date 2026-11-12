import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import conectar_bd, obtener_ciclo_activo


@st.cache_data(ttl=60)
def obtener_historial_ciclos(clan_id=None):
    if clan_id is None:
        try:
            clan_id = st.session_state.get('clan_id', 1)
        except Exception:
            clan_id = 1
    conexion = conectar_bd()
    df_ciclos = pd.read_sql_query(
        "SELECT id, COALESCE(numero_ciclo, id) AS numero_ciclo, fecha_desde, fecha_hasta, estado FROM ciclos_inmortales WHERE COALESCE(clan_id, 1) = ? ORDER BY COALESCE(numero_ciclo, id) DESC",
        conexion,
        params=(int(clan_id),)
    )
    conexion.close()
    return df_ciclos


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
    clan_id = int(st.session_state.get('clan_id', 1))
    clan_nombre = st.session_state.get('clan_nombre', 'Clan')

    st.title(f"⏳ Administrar Ciclos Inmortales — {clan_nombre}")
    st.markdown(
        f"Gestiona los ciclos inmortales independientes de **{clan_nombre}**. Permite crear nuevos ciclos, cerrar el actual y auditar su histórico propio."
    )

    # Control estricto de permisos
    if st.session_state.get('rol') not in ('admin', 'superadmin'):
        st.error("🚫 Acceso denegado. Este módulo solo está disponible para Administradores.")
        return

    ciclo_activo = obtener_ciclo_activo(clan_id)

    # ==========================================
    # SECCIÓN 1: PANEL SUPERIOR (ESTADO ACTUAL)
    # ==========================================
    st.subheader(f"📊 Estado del Ciclo Inmortal ({clan_nombre})")
    if ciclo_activo:
        c_num, c_desde, _ = ciclo_activo
        duracion = calcular_duracion(c_desde)
        st.success(f"🟢 **Ciclo {c_num} Activo en {clan_nombre}**")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Fecha de Inicio", c_desde)
        col_m2.metric("Semanas Transcurridas", duracion)
    else:
        st.warning(f"⚠️ No existe un ciclo inmortal activo para **{clan_nombre}**.")

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
                # REGLA 1 y 2: Unicidad de ciclo activo por clan
                if ciclo_activo:
                    st.error(f"❌ Ya existe un ciclo inmortal activo en {clan_nombre}. Debe cerrarlo antes de crear uno nuevo.")
                else:
                    fecha_desde_str = str(fecha_desde)
                    try:
                        conexion = conectar_bd()
                        cursor = conexion.cursor()

                        # REGLA 9: Validar superposición con períodos registrados en este clan
                        cursor.execute(
                            "SELECT MAX(fecha_hasta) FROM ciclos_inmortales WHERE COALESCE(clan_id, 1) = ?",
                            (clan_id,)
                        )
                        max_hasta_res = cursor.fetchone()

                        superposicion = False
                        max_hasta_val = None
                        if max_hasta_res and max_hasta_res[0]:
                            max_hasta_val = datetime.strptime(max_hasta_res[0], "%Y-%m-%d").date()
                            if fecha_desde <= max_hasta_val:
                                superposicion = True

                        if superposicion:
                            st.error(f"❌ La fecha desde ({fecha_desde_str}) se superpone con un período ya registrado en {clan_nombre} (Último ciclo finalizó el {max_hasta_val}).")
                            conexion.close()
                        else:
                            # Calcular número de ciclo secuencial propio para este clan (1, 2, 3...)
                            cursor.execute(
                                "SELECT COALESCE(MAX(COALESCE(numero_ciclo, id)), 0) + 1 FROM ciclos_inmortales WHERE COALESCE(clan_id, 1) = ?",
                                (clan_id,)
                            )
                            nuevo_num = int(cursor.fetchone()[0])

                            cursor.execute(
                                "INSERT INTO ciclos_inmortales (fecha_desde, estado, clan_id, numero_ciclo) VALUES (?, 'Activo', ?, ?)",
                                (fecha_desde_str, clan_id, nuevo_num)
                            )
                            conexion.commit()
                            conexion.close()
                            st.cache_data.clear()
                            st.success(f"🎉 Ciclo {nuevo_num} de {clan_nombre} creado exitosamente.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al acceder a la base de datos: {e}")

    with col_der:
        st.subheader("🔒 Cerrar Ciclo Inmortal Activo")
        with st.form("form_cerrar_ciclo"):
            fecha_hasta = st.date_input("Fecha Hasta (Fin del Ciclo):", date.today())
            btn_cerrar = st.form_submit_button("🔒 Finalizar Ciclo Activo")

            if btn_cerrar:
                if not ciclo_activo:
                    st.error(f"❌ No existe un ciclo inmortal activo en {clan_nombre}.")
                else:
                    c_num, c_desde, _ = ciclo_activo
                    c_desde_date = datetime.strptime(c_desde, "%Y-%m-%d").date()

                    if fecha_hasta < c_desde_date:
                        st.error("❌ La fecha hasta debe ser mayor o igual a la fecha desde.")
                    else:
                        try:
                            conexion = conectar_bd()
                            cursor = conexion.cursor()
                            cursor.execute(
                                "UPDATE ciclos_inmortales SET fecha_hasta = ?, estado = 'Finalizado' WHERE estado = 'Activo' AND COALESCE(clan_id, 1) = ?",
                                (str(fecha_hasta), clan_id)
                            )
                            conexion.commit()
                            conexion.close()
                            st.cache_data.clear()
                            st.success(f"🎉 Ciclo {c_num} de {clan_nombre} cerrado y guardado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al cerrar el ciclo: {e}")

    st.divider()

    # ==========================================
    # SECCIÓN 3: LISTADO HISTÓRICO Y ELIMINACIÓN
    # ==========================================
    st.subheader(f"📋 Historial de Ciclos Inmortales — {clan_nombre}")
    try:
        df_ciclos = obtener_historial_ciclos(clan_id)
    except Exception:
        df_ciclos = pd.DataFrame()

    if not df_ciclos.empty:
        df_ciclos['Duración'] = df_ciclos.apply(lambda r: calcular_duracion(r['fecha_desde'], r['fecha_hasta']), axis=1)
        
        df_mostrar = df_ciclos.rename(columns={
            'numero_ciclo': 'ID Ciclo',
            'fecha_desde': 'Fecha Desde',
            'fecha_hasta': 'Fecha Hasta',
            'estado': 'Estado'
        })
        st.dataframe(df_mostrar[['ID Ciclo', 'Fecha Desde', 'Fecha Hasta', 'Estado', 'Duración']], use_container_width=True, hide_index=True)

        # Formulario para eliminar ciclo
        st.write("")
        st.markdown("##### 🗑️ Eliminar Ciclo Histórico (Acción Protegida)")
        with st.form("form_eliminar_ciclo"):
            ciclo_a_eliminar = st.selectbox("Seleccionar ciclo a eliminar:", df_ciclos['numero_ciclo'])
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

                        # REGLA 7: No eliminar ciclo con información asociada en este clan
                        cursor.execute(
                            "SELECT COUNT(*) FROM asistencia WHERE ciclo = ? AND COALESCE(clan_id, 1) = ?",
                            (ciclo_str, clan_id)
                        )
                        cont_asist = cursor.fetchone()[0]

                        cursor.execute(
                            "SELECT COUNT(*) FROM estadisticas_guerra WHERE ciclo = ? AND COALESCE(clan_id, 1) = ?",
                            (ciclo_str, clan_id)
                        )
                        cont_stats = cursor.fetchone()[0]

                        if cont_asist > 0 or cont_stats > 0:
                            st.error("❌ No es posible eliminar un ciclo que posee información asociada.")
                            st.info(f"💡 Detalle de asociaciones en {clan_nombre}: {cont_asist} registros de asistencia, {cont_stats} de estadísticas de guerra.")
                            conexion.close()
                        else:
                            cursor.execute(
                                "DELETE FROM ciclos_inmortales WHERE COALESCE(clan_id, 1) = ? AND COALESCE(numero_ciclo, id) = ?",
                                (clan_id, int(ciclo_a_eliminar))
                            )
                            conexion.commit()
                            conexion.close()
                            st.cache_data.clear()
                            st.success(f"🗑️ Ciclo {ciclo_a_eliminar} de {clan_nombre} eliminado con éxito.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error de base de datos al eliminar: {e}")
    else:
        st.info(f"No hay ciclos inmortales registrados para {clan_nombre}.")
