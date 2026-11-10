import os
import streamlit as st
from werkzeug.security import check_password_hash, generate_password_hash
from database import conectar_bd, obtener_clanes, obtener_clan_por_id

# Importamos todos los módulos
from modulos import (
    datos_resumen,
    alta_baja,
    asistencia,
    sanciones,
    estadisticas,
    admin_usuarios,
    armador_salas,
    ciclo_inmortal,
    admin_clases,
    admin_clanes
)

st.set_page_config(
    page_title="Gestión de Clanes - Diablo Immortal",
    page_icon="🛡️",
    layout="wide"
)

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
    st.session_state['clan_id'] = 1
    st.session_state['clan_nombre'] = "ÐÛΝΞÐΛIN"
    st.session_state['clan_logo'] = "Logo1.jpeg"

# ==========================================
# PANTALLA DE LOGIN RESTRINGIDO
# ==========================================


def pantalla_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("")
        st.write("")
        try:
            if os.path.exists("Logo1.jpeg"):
                st.image("Logo1.jpeg", width="stretch")
            elif os.path.exists("assets/logo.png"):
                st.image("assets/logo.png", width="stretch")
            elif os.path.exists("logo.jpg"):
                st.image("logo.jpg", width="stretch")
            else:
                st.markdown(
                    "<h2 style='text-align: center; color: #d4af37;'>Portal de Clanes</h2><h4 style='text-align: center; color: #a9b0ba;'>Centro de Comando</h4>", unsafe_allow_html=True)
        except Exception:
            st.markdown(
                "<h2 style='text-align: center; color: #d4af37;'>Portal de Clanes</h2>", unsafe_allow_html=True)

        st.markdown(
            "<h2 style='text-align: center; color: #a9b0ba;'>Acceso Restringido</h2>", unsafe_allow_html=True)

        with st.form("login_form"):
            user = st.text_input("Usuario", placeholder="Nick del oficial o administrador")
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
                        cursor.execute(
                            "SELECT password_hash, rol, debe_cambiar_pass, clan_id FROM usuarios WHERE LOWER(usuario) = LOWER(?)", (user,))
                        resultado = cursor.fetchone()
                        conexion.close()

                        if resultado and check_password_hash(resultado[0], password):
                            st.session_state['logeado'] = True
                            st.session_state['usuario'] = user
                            st.session_state['rol'] = resultado[1]
                            st.session_state['debe_cambiar'] = True if resultado[2] == 1 else False
                            
                            user_clan_id = resultado[3] if len(resultado) > 3 and resultado[3] is not None else 1
                            st.session_state['clan_id'] = user_clan_id

                            # Cargar datos del clan asignado
                            info_clan = obtener_clan_por_id(user_clan_id)
                            if info_clan:
                                st.session_state['clan_nombre'] = info_clan['nombre']
                                st.session_state['clan_logo'] = info_clan['logo_path']
                            else:
                                st.session_state['clan_nombre'] = "ÐÛΝΞÐΛIN"
                                st.session_state['clan_logo'] = "Logo1.jpeg"

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
                        st.cache_data.clear()

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
    rol_usuario = st.session_state.get('rol', 'oficial')
    es_superadmin = (rol_usuario == 'superadmin')
    es_admin_o_superior = rol_usuario in ('admin', 'superadmin')

    # Resolver información del clan activo
    clan_actual_id = st.session_state.get('clan_id', 1)
    info_clan_actual = obtener_clan_por_id(clan_actual_id)
    if info_clan_actual:
        nombre_clan_actual = info_clan_actual['nombre']
        logo_clan_actual = info_clan_actual['logo_path']
    else:
        nombre_clan_actual = st.session_state.get('clan_nombre', 'Clan')
        logo_clan_actual = "Logo1.jpeg"

    # Logo dinámico del clan activo en Sidebar
    if logo_clan_actual and os.path.exists(logo_clan_actual):
        st.sidebar.image(logo_clan_actual, width="stretch")
    elif os.path.exists("Logo1.jpeg"):
        st.sidebar.image("Logo1.jpeg", width="stretch")
    elif os.path.exists("Diablo Inmortal.png"):
        st.sidebar.image("Diablo Inmortal.png", width="stretch")

    st.sidebar.markdown(
        f"<h3 style='text-align: center; color: #d4af37;'>{nombre_clan_actual}<br><span style='font-size: 0.75em; color: #a9b0ba;'>Centro de Comando</span></h3>",
        unsafe_allow_html=True
    )

    # SELECTOR DE CLANES (Exclusivo para SuperAdmin)
    if es_superadmin:
        try:
            df_clanes = obtener_clanes()
            dict_clanes = {int(r['id']): str(r['nombre']) for _, r in df_clanes.iterrows()}
            
            if clan_actual_id not in dict_clanes and dict_clanes:
                clan_actual_id = list(dict_clanes.keys())[0]
                st.session_state['clan_id'] = clan_actual_id

            st.sidebar.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            st.sidebar.markdown("**🌐 Alternar Clan Activo:**")
            
            idx_seleccionado = list(dict_clanes.keys()).index(clan_actual_id) if clan_actual_id in dict_clanes else 0
            nuevo_clan_id = st.sidebar.selectbox(
                "Clan activo en pantalla:",
                options=list(dict_clanes.keys()),
                format_func=lambda cid: f"⚔️ {dict_clanes[cid]}",
                index=idx_seleccionado,
                key="selector_superadmin_clan",
                label_visibility="collapsed"
            )

            if nuevo_clan_id != clan_actual_id:
                st.session_state['clan_id'] = nuevo_clan_id
                info_nuevo = obtener_clan_por_id(nuevo_clan_id)
                if info_nuevo:
                    st.session_state['clan_nombre'] = info_nuevo['nombre']
                    st.session_state['clan_logo'] = info_nuevo['logo_path']
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error al listar clanes: {e}")
    else:
        # Los oficiales y administradores estándar solo ven su clan fijo
        st.sidebar.markdown(
            f"<div style='text-align: center; font-size: 0.85em; color: #d4af37; border: 1px solid #721c24; border-radius: 4px; padding: 4px; margin-bottom: 8px;'>🛡️ Clan Asignado: <b>{nombre_clan_actual}</b></div>",
            unsafe_allow_html=True
        )

    st.sidebar.title(f"Bienvenido,\n🛡️ {st.session_state['usuario']}")
    st.sidebar.markdown("<hr class='divisor-diablo'>", unsafe_allow_html=True)

    try:
        if os.path.exists("Diablo Inmortal.png"):
            st.sidebar.image("Diablo Inmortal.png", width="stretch")
        elif os.path.exists("Diablo Inmortal.jpg"):
            st.sidebar.image("Diablo Inmortal.jpg", width="stretch")
    except Exception:
        pass

    # Menú de navegación
    opciones_menu = [
        "📊 Datos y Resumen",
        "📥 Ingreso / 📤 Egreso",
        "📝 Asistencia Masiva",
        "⚖️ Sanciones y Advertencias",
        "⚔️ Estadísticas de Guerra",
        "🗺️ Armador de Salas"
    ]

    if es_admin_o_superior:
        st.sidebar.divider()
        opciones_menu.append("🔐 Gestión de Accesos")
        opciones_menu.append("⏳ Administrar Ciclo Inmortal")
        opciones_menu.append("⚙️ Administrar Clases")

    if es_superadmin:
        opciones_menu.append("🏰 Configuración de Clanes")

    st.sidebar.divider()
    opciones_menu.append("🚪 Cerrar Sesión")

    menu = st.sidebar.radio("Módulos de Gestión:", opciones_menu)

    # Navegación a módulos
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
    elif menu == "🏰 Configuración de Clanes":
        admin_clanes.mostrar()
    elif menu == "🚪 Cerrar Sesión":
        st.session_state['logeado'] = False
        st.session_state['usuario'] = ""
        st.session_state['rol'] = ""
        st.session_state['debe_cambiar'] = False
        st.session_state['clan_id'] = 1
        st.session_state['clan_nombre'] = "ÐÛΝΞÐΛIN"
        st.session_state['clan_logo'] = "Logo1.jpeg"
        st.cache_data.clear()
        st.rerun()
