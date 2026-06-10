import streamlit as st
import sqlite3
import pandas as pd
from database import conectar_bd

def formatear_nombre_clase(nombre):
    palabras = nombre.strip().split()
    palabras_formateadas = []
    for i, p in enumerate(palabras):
        if i > 0 and p.lower() in ["de", "del"]:
            palabras_formateadas.append(p.lower())
        else:
            palabras_formateadas.append(p.capitalize())
    return " ".join(palabras_formateadas)

def mostrar():
    st.title("⚙️ Administración de Clases")
    st.markdown("Crea, modifica y visualiza las clases oficiales del sistema.")
    
    # 1. Obtener listado de clases actuales
    try:
        conn = conectar_bd()
        df_clases = pd.read_sql_query("SELECT id, nombre FROM clases ORDER BY id", conn)
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar las clases: {e}")
        df_clases = pd.DataFrame(columns=["id", "nombre"])

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Clases Registradas")
        if not df_clases.empty:
            df_clases_visual = df_clases.copy()
            df_clases_visual.insert(0, "#", range(1, len(df_clases_visual) + 1))
            st.dataframe(
                df_clases_visual,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": None,
                    "#": st.column_config.NumberColumn("#", width="small"),
                    "nombre": "Nombre de la Clase"
                }
            )
        else:
            st.info("No hay clases registradas.")
            
    with col2:
        # Formulario para agregar una nueva clase
        st.subheader("🆕 Agregar Nueva Clase")
        with st.form("form_nueva_clase"):
            nueva_clase = st.text_input("Nombre de la clase a crear:").strip()
            submit_crear = st.form_submit_button("💾 Guardar Clase")
            
            if submit_crear:
                if not nueva_clase:
                    st.error("⚠️ El nombre de la clase no puede estar vacío.")
                else:
                    clase_formateada = formatear_nombre_clase(nueva_clase)
                    try:
                        conn_w = conectar_bd()
                        cursor_w = conn_w.cursor()
                        # Buscar duplicados case-insensitive
                        cursor_w.execute("SELECT id FROM clases WHERE LOWER(nombre) = LOWER(?)", (clase_formateada,))
                        if cursor_w.fetchone():
                            st.error(f"⚠️ La clase '{clase_formateada}' ya está registrada.")
                            conn_w.close()
                        else:
                            cursor_w.execute("INSERT INTO clases (nombre) VALUES (?)", (clase_formateada,))
                            conn_w.commit()
                            conn_w.close()
                            st.success(f"✅ ¡Clase '{clase_formateada}' creada con éxito!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar la clase: {e}")

        st.write("")
        st.divider()
        st.write("")

        # Formulario para modificar una clase existente
        st.subheader("✏️ Modificar Clase Existente")
        if not df_clases.empty:
            opciones_clases = df_clases["nombre"].tolist()
            with st.form("form_modificar_clase"):
                clase_a_editar = st.selectbox("Seleccione la clase a modificar:", opciones_clases)
                nuevo_nombre_clase = st.text_input("Nuevo nombre para la clase:").strip()
                submit_modificar = st.form_submit_button("🔄 Actualizar Clase")
                
                if submit_modificar:
                    if not nuevo_nombre_clase:
                        st.error("⚠️ El nuevo nombre no puede estar vacío.")
                    else:
                        clase_formateada_mod = formatear_nombre_clase(nuevo_nombre_clase)
                        row_editar = df_clases[df_clases["nombre"] == clase_a_editar].iloc[0]
                        clase_id = int(row_editar["id"])
                        
                        try:
                            conn_w = conectar_bd()
                            cursor_w = conn_w.cursor()
                            # Buscar duplicados case-insensitive en OTRAS clases
                            cursor_w.execute("SELECT id FROM clases WHERE LOWER(nombre) = LOWER(?) AND id <> ?", (clase_formateada_mod, clase_id))
                            if cursor_w.fetchone():
                                st.error(f"⚠️ La clase '{clase_formateada_mod}' ya está registrada con otro ID.")
                                conn_w.close()
                            else:
                                cursor_w.execute("UPDATE clases SET nombre = ? WHERE id = ?", (clase_formateada_mod, clase_id))
                                conn_w.commit()
                                conn_w.close()
                                st.success(f"✅ ¡Clase actualizada a '{clase_formateada_mod}' exitosamente!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar la clase: {e}")
        else:
            st.info("No hay clases disponibles para modificar.")
