import streamlit as st
import os
import pandas as pd
from database import obtener_clanes, obtener_clan_por_id, actualizar_clan


def mostrar():
    st.title("🏰 Configuración y Personalización de Clanes")
    st.markdown("Como **SuperAdministrador**, puedes editar el nombre, la sigla, la descripción y el escudo/logo oficial de cada clan en cualquier momento.")

    if st.session_state.get('rol') != 'superadmin':
        st.error("🚫 Acceso denegado. Este módulo solo está disponible para SuperAdministradores.")
        return

    try:
        df_clanes = obtener_clanes()
    except Exception as e:
        st.error(f"Error al consultar clanes: {e}")
        return

    os.makedirs("assets", exist_ok=True)

    pestanas = st.tabs([f"🛡️ {row['nombre']}" for _, row in df_clanes.iterrows()])

    for idx, (_, clan_row) in enumerate(df_clanes.iterrows()):
        clan_id = int(clan_row['id'])
        with pestanas[idx]:
            st.subheader(f"⚙️ Configuración: {clan_row['nombre']} (ID: {clan_id})")

            col_form, col_preview = st.columns([2, 1])

            with col_form:
                with st.form(f"form_clan_{clan_id}"):
                    nuevo_nombre = st.text_input("Nombre del Clan:", value=str(clan_row['nombre'])).strip()
                    nueva_sigla = st.text_input("Sigla / Abreviatura:", value=str(clan_row['sigla'] or "")).strip()
                    nueva_desc = st.text_area("Descripción / Rango del Clan:", value=str(clan_row['descripcion'] or "")).strip()

                    archivo_logo = st.file_uploader(
                        f"Subir nuevo Logo / Escudo para {nuevo_nombre} (PNG, JPG, JPEG):",
                        type=["png", "jpg", "jpeg"],
                        key=f"uploader_logo_{clan_id}"
                    )

                    btn_guardar = st.form_submit_button("💾 Guardar Cambios de este Clan", type="primary")

                    if btn_guardar:
                        if not nuevo_nombre:
                            st.error("⚠️ El nombre del clan no puede estar vacío.")
                        else:
                            nuevo_logo_path = clan_row['logo_path']
                            if archivo_logo is not None:
                                ext = os.path.splitext(archivo_logo.name)[1].lower()
                                nuevo_logo_path = f"assets/logo_clan_{clan_id}{ext}"
                                with open(nuevo_logo_path, "wb") as f:
                                    f.write(archivo_logo.getbuffer())

                            try:
                                actualizar_clan(clan_id, nuevo_nombre, nueva_sigla, nuevo_logo_path, nueva_desc)
                                st.success(f"🎉 ¡Datos del clan '{nuevo_nombre}' actualizados correctamente!")
                                
                                # Si el clan editado es el que está en sesión, refrescar datos
                                if st.session_state.get('clan_id') == clan_id:
                                    st.session_state['clan_nombre'] = nuevo_nombre
                                    st.session_state['clan_logo'] = nuevo_logo_path
                                
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al guardar los cambios del clan: {ex}")

            with col_preview:
                st.markdown("#### 🖼️ Vista Previa del Logo")
                logo_actual = clan_row['logo_path']
                if logo_actual and os.path.exists(logo_actual):
                    st.image(logo_actual, caption=f"Logo actual de {clan_row['nombre']}", width="stretch")
                elif os.path.exists("Logo1.jpeg") and clan_id == 1:
                    st.image("Logo1.jpeg", caption="Logo predeterminado", width="stretch")
                elif os.path.exists("Diablo Inmortal.png"):
                    st.image("Diablo Inmortal.png", caption="Logo provisional", width="stretch")
                else:
                    st.info("Sin imagen de logo configurada.")
