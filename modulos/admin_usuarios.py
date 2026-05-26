import streamlit as st
import pandas as pd
from database import conectar_bd
from werkzeug.security import generate_password_hash


def mostrar():
    st.title("🔐 Gestión de Accesos (Solo Administrador)")
    st.markdown(
        "Desde aquí puedes otorgar o revocar accesos a los oficiales del clan.")

    try:
        conexion = conectar_bd()

        # 1. Mostrar usuarios actuales
        st.subheader("👥 Oficiales con acceso al sistema")
        df_usuarios = pd.read_sql_query(
            "SELECT id, usuario, rol FROM usuarios", conexion)
        st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
        st.divider()

        # 2. Crear nuevo usuario o resetear contraseña
        st.subheader("➕ Crear o Restablecer Oficial")
        with st.form("nuevo_usuario"):
            nuevo_user = st.text_input("Usuario (Nick del Oficial):").strip()
            nuevo_pass = st.text_input("Contraseña Temporal:", type="password")
            rol = st.selectbox("Nivel de Permisos:", ["oficial", "admin"])

            st.info("💡 Si el usuario ya existe, al guardarlo se pisoteará la contraseña vieja por esta nueva temporal y se le obligará a cambiarla al entrar.")
            submit = st.form_submit_button("💾 Guardar / Restablecer Usuario")

            if submit:
                if not nuevo_user or len(nuevo_pass) < 6:
                    st.error(
                        "⚠️ El usuario es obligatorio y la contraseña debe tener al menos 6 caracteres.")
                else:
                    hash_pass = generate_password_hash(nuevo_pass)
                    cursor = conexion.cursor()

                    # Verificamos si ya existe el usuario
                    cursor.execute(
                        "SELECT id FROM usuarios WHERE LOWER(usuario) = LOWER(?)", (nuevo_user,))
                    existe = cursor.fetchone()

                    if existe:
                        # Si existe, pisamos la contraseña y activamos debe_cambiar_pass = 1
                        cursor.execute(
                            "UPDATE usuarios SET password_hash=?, rol=?, debe_cambiar_pass=1 WHERE id=?", (hash_pass, rol, existe[0]))
                        st.success(
                            f"🔄 Contraseña vieja anulada. Se asignó la clave temporal para el oficial: {nuevo_user}.")
                    else:
                        # Si es nuevo, lo creamos con debe_cambiar_pass = 1
                        cursor.execute(
                            "INSERT INTO usuarios (usuario, password_hash, rol, debe_cambiar_pass) VALUES (?, ?, ?, 1)", (nuevo_user, hash_pass, rol))
                        st.success(
                            f"✅ Oficial {nuevo_user} creado con contraseña temporal obligatoria.")

                    conexion.commit()
                    st.rerun()

        conexion.close()
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
