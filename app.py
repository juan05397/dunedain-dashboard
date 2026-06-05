import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash
from database import conectar_bd

# Importamos todos los módulos
from modulos import datos_resumen, alta_baja, asistencia, sanciones, estadisticas, admin_usuarios, armador_salas, ciclo_inmortal

st.set_page_config(page_title="ÐÛΝΞÐΛIN Dashboard",
                   page_icon="🛡️", layout="wide")

# Inicializamos el control de sesiones en la memoria del navegador
if 'logeado' not in st.session_state:
    st.session_state['logeado'] = False
    st.session_state['usuario'] = ""
    st.session_state['rol'] = ""
    st.session_state['debe_cambiar'] = False

# ==========================================
# PANTALLA DE LOGIN RESTRINGIDO
# ==========================================


def pantalla_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("")
        st.write("")
        try:
            st.image("logo.jpg", use_container_width=True)
        except:
            pass

        st.markdown(
            "<h2 style='text-align: center; color: #a9b0ba;'>Acceso Restringido</h2>", unsafe_allow_html=True)

        with st.form("login_form"):
            user = st.text_input("Usuario", placeholder="Nick del jugador")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Entrar a la Base de Datos", use_container_width=True)

            if submit:
                if not user or not password:
                    st.error("⚠️ Debes ingresar ambos datos.")
                else:
                    try:
                        conexion = conectar_bd()
                        cursor = conexion.cursor()
                        # Traemos también el estado de la columna debe_cambiar_pass
                        cursor.execute(
                            "SELECT password_hash, rol, debe_cambiar_pass FROM usuarios WHERE LOWER(usuario) = LOWER(?)", (user,))
                        resultado = cursor.fetchone()
                        conexion.close()

                        if resultado and check_password_hash(resultado[0], password):
                            st.session_state['logeado'] = True
                            st.session_state['usuario'] = user
                            st.session_state['rol'] = resultado[1]
                            st.session_state['debe_cambiar'] = True if resultado[2] == 1 else False
                            st.rerun()
                        else:
                            st.error(
                                "❌ Credenciales incorrectas o acceso denegado.")
                    except Exception as e:
                        st.error("Fallo de conexión a la base de datos.")

# ==========================================
# PANTALLA OBLIGATORIA DE CAMBIO DE CONTRASEÑA
# ==========================================


def pantalla_cambio_obligatorio():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("")
        st.warning("🔒 **CAMBIO DE CONTRASEÑA OBLIGATORIO**\n\nEstás usando una contraseña temporal provista por el administrador. Por seguridad, debes definir una clave nueva y secreta antes de continuar.")

        with st.form("form_cambio_obligatorio"):
            nueva_pass = st.text_input("Nueva Contraseña:", type="password")
            confirmar_pass = st.text_input(
                "Confirmar Nueva Contraseña:", type="password")
            btn_cambiar = st.form_submit_button(
                "🔄 Actualizar Contraseña y Entrar")

            if btn_cambiar:
                if len(nueva_pass) < 6:
                    st.error(
                        "⚠️ La nueva contraseña debe tener al menos 6 caracteres.")
                elif nueva_pass != confirmar_pass:
                    st.error("❌ Las contraseñas ingresadas no coinciden.")
                else:
                    try:
                        conexion = conectar_bd()
                        cursor = conexion.cursor()
                        nuevo_hash = generate_password_hash(nueva_pass)
                        cursor.execute("UPDATE usuarios SET password_hash = ?, debe_cambiar_pass = 0 WHERE LOWER(usuario) = LOWER(?)", (
                            nuevo_hash, st.session_state['usuario']))
                        conexion.commit()
                        conexion.close()

                        st.session_state['debe_cambiar'] = False
                        st.success(
                            "🎉 ¡Contraseña actualizada con éxito! Accediendo al sistema...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar la nueva contraseña: {e}")


# ==========================================
# ENRUTADOR PRINCIPAL
# ==========================================
if not st.session_state['logeado']:
    pantalla_login()
elif st.session_state['debe_cambiar']:
    pantalla_cambio_obligatorio()
else:
    # Sidebar dinámico
    try:
        st.sidebar.image("logo.jpg", use_container_width=True)
    except:
        pass

    st.sidebar.title(f"Bienvenido,\n🛡️ {st.session_state['usuario']}")

    # Aquí está la lista con la coma corregida y el Armador incluido
    opciones_menu = [
        "📊 Datos y Resumen",
        "🚪 Alta / Baja de Miembros",
        "📝 Asistencia Masiva",
        "⚖️ Sanciones y Advertencias",
        "⚔️ Estadísticas de Guerra",
        "🗺️ Armador de Salas"
    ]

    if st.session_state['rol'] == 'admin':
        st.sidebar.divider()
        opciones_menu.append("🔐 Gestión de Accesos")
        opciones_menu.append("⏳ Administrar Ciclo Inmortal")

    st.sidebar.divider()
    opciones_menu.append("🚪 Cerrar Sesión")

    menu = st.sidebar.radio("Módulos de Gestión:", opciones_menu)

    # Navegación
    if menu == "📊 Datos y Resumen":
        datos_resumen.mostrar()
    elif menu == "🚪 Alta / Baja de Miembros":
        alta_baja.mostrar()
    elif menu == "📝 Asistencia Masiva":
        asistencia.mostrar()
    elif menu == "⚖️ Sanciones y Advertencias":
        sanciones.mostrar()
    elif menu == "⚔️ Estadísticas de Guerra":
        estadisticas.mostrar()
    elif menu == "🗺️ Armador de Salas":
        armador_salas.mostrar()
    elif menu == "🔐 Gestión de Accesos":
        admin_usuarios.mostrar()
    elif menu == "⏳ Administrar Ciclo Inmortal":
        ciclo_inmortal.mostrar()
    elif menu == "🚪 Cerrar Sesión":
        st.session_state['logeado'] = False
        st.session_state['usuario'] = ""
        st.session_state['rol'] = ""
        st.session_state['debe_cambiar'] = False
        st.rerun()
