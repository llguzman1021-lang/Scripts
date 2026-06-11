import streamlit as st
import json
import os

# Archivo de datos
DATA_FILE = "data.json"

# Cargar datos
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"📧 Correos": {}, "🎫 Tickets ZohoDesk": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Guardar datos
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

st.set_page_config(page_title="Gestor TIC", layout="centered")
st.title("⚡ Gestor TIC Pro")

data = load_data()

# Tabs principales
tab1, tab2 = st.tabs(["📋 Uso Rápido", "⚙️ Panel de Control"])

with tab1:
    st.subheader("Selecciona y Copia")
    categoria = st.radio("Elige la categoría:", list(data.keys()))
    
    if not data[categoria]:
        st.write("No hay scripts en esta categoría.")
    else:
        for titulo, contenido in data[categoria].items():
            with st.expander(f"📌 {titulo}"):
                st.code(contenido, language="text")

with tab2:
    st.subheader("Gestionar Scripts")
    cat_admin = st.selectbox("Categoría a editar:", list(data.keys()))
    
    # ACCIÓN: AGREGAR
    with st.expander("➕ Agregar Nuevo Script"):
        nuevo_titulo = st.text_input("Título del script:")
        nuevo_texto = st.text_area("Contenido del script:")
        if st.button("Guardar Nuevo"):
            if nuevo_titulo and nuevo_texto:
                data[cat_admin][nuevo_titulo] = nuevo_texto
                save_data(data)
                st.success("Guardado!")
                st.rerun()

    # ACCIÓN: MODIFICAR/ELIMINAR
    st.write("---")
    for titulo in list(data[cat_admin].keys()):
        col1, col2 = st.columns([3, 1])
        with col1:
            # Editamos el contenido
            nuevo_texto = st.text_area(f"Editar: {titulo}", value=data[cat_admin][titulo], key=f"edit_{titulo}")
            if nuevo_texto != data[cat_admin][titulo]:
                data[cat_admin][titulo] = nuevo_texto
                save_data(data)
        with col2:
            if st.button("❌ Eliminar", key=f"del_{titulo}"):
                del data[cat_admin][titulo]
                save_data(data)
                st.rerun()
