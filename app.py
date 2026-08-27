import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash
from database import conectar_bd

# Importamos todos los módulos
from modulos import datos_resumen, alta_baja, asistencia, sanciones, estadisticas, admin_usuarios, armador_salas, ciclo_inmortal, admin_clases

st.set_page_config(page_title="ÐÛΝΞÐΛIN Dashboard",
                   page_icon="🛡️", layout="wide")

# Inyección de Estilos Tematización Diablo
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@300;400;600&display=swap');

    /* Fuente base para encabezados */
    h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
        font-family: 'Cinzel', serif !important;
    }

    /* MODO CLARO (Fondo blanco/claro) */
    @media (prefers-color-scheme: light) {
        h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
            color: #353839 !important; /* Gris carbón oscuro */
            text-shadow: none !important; /* Sin brillo para máxima legibilidad */
        }
    }

    /* MODO OSCURO (Fondo oscuro/negro) */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {
            color: #353232 !important; /* Gris claro para máxima legibilidad */
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9) !important; /* Sombra oscura para contraste */
        }
    }

    /* Párrafos, tablas, textos de widgets, labels */
    p, label, li, table, td, th, [data-testid="stWidgetLabel"] {
        font-family: 'Montserrat', sans-serif;
    }

    span, div {
        font-family: 'Montserrat', sans-serif;
    }

    /* Excepción para iconos */
    .material-icons, .st-icon, svg, [class^="st-icon-"], .st-expander-arrow, .st-expander-arrow span {
        font-family: 'Material Icons' !important;
        font-size: inherit;
    }

    /* Modificación de st.divider (<hr>) */
    hr {
        border: 0 !important;
        height: 2px !important;
        background: linear-gradient(to right, rgba(114, 28, 36, 0.1) 0%, rgba(212, 175, 55, 0.8) 50%, rgba(114, 28, 36, 0.1) 100%) !important;
        margin: 20px 0 !important;
    }

    /* Clase divisor-diablo manual */
    .divisor-diablo {
        height: 2px;
        background: linear-gradient(to right, rgba(114, 28, 36, 0.1) 0%, rgba(212, 175, 55, 0.8) 50%, rgba(114, 28, 36, 0.1) 100%);
        margin: 15px 0;
    }

    /* Clase card-diablo */
    .card-diablo {
        background-color: #121418 !important;
        border: 1px solid #721c24 !important;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(114, 28, 36, 0.4);
        padding: 15px;
        margin-bottom: 15px;
        color: #f5f5f5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
            import os
            if os.path.exists("Logo1.jpeg"):
                st.image("Logo1.jpeg", width="stretch")
            elif os.path.exists("assets/logo.png"):
                st.image("assets/logo.png", width="stretch")
            elif os.path.exists("logo.jpg"):
                st.image("logo.jpg", width="stretch")
            else:
                st.markdown(
                    "<h2 style='text-align: center; color: #d4af37;'>Nombre del Clan</h2><h4 style='text-align: center; color: #a9b0ba;'>Centro de Comando</h4>", unsafe_allow_html=True)
        except:
            st.markdown(
                "<h2 style='text-align: center; color: #d4af37;'>Nombre del Clan</h2>", unsafe_allow_html=True)

        st.markdown(
            "<h2 style='text-align: center; color: #a9b0ba;'>Acceso Restringido</h2>", unsafe_allow_html=True)

        with st.form("login_form"):
            user = st.text_input("Usuario", placeholder="Nick del jugador")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button(
                "Entrar a la Base de Datos", width="stretch")

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
                        st.error(f"Fallo de conexión a la base de datos. Detalle técnico: {e}")

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
        import os
        if os.path.exists("Logo1.jpeg"):
            st.sidebar.image("Logo1.jpeg", width="stretch")
        elif os.path.exists("assets/logo.png"):
            st.sidebar.image("assets/logo.png", width="stretch")
        elif os.path.exists("logo.jpg"):
            st.sidebar.image("logo.jpg", width="stretch")
        else:
            st.sidebar.markdown(
                "<h3 style='text-align: center; color: #d4af37;'>Nombre del Clan<br><span style='font-size: 0.8em; color: #a9b0ba;'>Centro de Comando</span></h3>", unsafe_allow_html=True)
    except:
        st.sidebar.markdown(
            "<h3 style='text-align: center; color: #d4af37;'>Nombre del Clan</h3>", unsafe_allow_html=True)

    st.sidebar.title(f"Bienvenido,\n🛡️ {st.session_state['usuario']}")

    st.sidebar.markdown("<hr class='divisor-diablo'>", unsafe_allow_html=True)
    try:
        st.sidebar.image("Diablo Inmortal.png", width="stretch")
    except FileNotFoundError:
        try:
            st.sidebar.image("Diablo Inmortal.jpg", width="stretch")
        except Exception:
            pass

    # Aquí está la lista con la coma corregida y el Armador incluido
    opciones_menu = [
        "📊 Datos y Resumen",
        "📥 Ingreso / 📤 Egreso",
        "📝 Asistencia Masiva",
        "⚖️ Sanciones y Advertencias",
        "⚔️ Estadísticas de Guerra",
        "🗺️ Armador de Salas"
    ]

    if st.session_state['rol'] == 'admin':
        st.sidebar.divider()
        opciones_menu.append("🔐 Gestión de Accesos")
        opciones_menu.append("⏳ Administrar Ciclo Inmortal")
        opciones_menu.append("⚙️ Administrar Clases")

    st.sidebar.divider()
    opciones_menu.append("🚪 Cerrar Sesión")

    menu = st.sidebar.radio("Módulos de Gestión:", opciones_menu)

    # Navegación
    if menu == "📊 Datos y Resumen":
        datos_resumen.mostrar()
    elif menu == "📥 Ingreso / 📤 Egreso":
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
    elif menu == "⚙️ Administrar Clases":
        admin_clases.mostrar()
    elif menu == "🚪 Cerrar Sesión":
        st.session_state['logeado'] = False
        st.session_state['usuario'] = ""
        st.session_state['rol'] = ""
        st.session_state['debe_cambiar'] = False
        st.rerun()
