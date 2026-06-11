import streamlit as st
import json
import os

# ==========================================
# CONFIGURACIÓN Y CSS INYECTADO (DISEÑO PREMIUM)
# ==========================================
st.set_page_config(page_title="Gestor TIC Pro", page_icon="⚡", layout="wide")

# Inyección de CSS para modernizar la interfaz nativa de Streamlit
st.markdown("""
    <style>
    /* Suavizar bordes y sombras para tarjetas */
    div[data-testid="stContainer"] {
        border-radius: 12px;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stContainer"]:hover {
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.05);
        border-color: #4CAF50;
    }
    /* Estilizar botones para que parezcan 'Pills' o etiquetas */
    .stButton>button {
        border-radius: 20px;
        font-weight: 600;
    }
    /* Limpiar la barra lateral */
    [data-testid="stSidebarNav"] {display: none;}
    /* Títulos más estilizados */
    h1 { font-weight: 800; letter-spacing: -1px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CAPA DE DATOS ANTIFALLOS
# ==========================================
class GestorDatos:
    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        self.datos_base = {"📧 Correos": {}, "🎫 Tickets ZohoDesk": {}, "📞 Telefonía Avaya": {}, "🌐 Redes Cisco (CCNA)": {}}

    def cargar(self):
        if not os.path.exists(self.filepath):
            self.guardar(self.datos_base)
            return self.datos_base
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict): return self.datos_base
                for cat, scripts in data.items():
                    if not isinstance(scripts, dict): data[cat] = {}
                return data
        except:
            return self.datos_base

    def guardar(self, datos):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)

gestor = GestorDatos()

if "db" not in st.session_state:
    st.session_state.db = gestor.cargar()
if "filtro_rapido" not in st.session_state:
    st.session_state.filtro_rapido = ""

def sincronizar_datos():
    gestor.guardar(st.session_state.db)

def contar_scripts():
    return sum(len(cat) for cat in st.session_state.db.values())

def set_filtro(tag):
    st.session_state.filtro_rapido = tag

# ==========================================
# MENÚ LATERAL MEJORADO
# ==========================================
with st.sidebar:
    st.markdown("### ⚡ Gestor TIC Pro")
    st.caption("Workspace Personal")
    st.markdown("---")
    modo = st.radio("Navegación", ["🚀 Panel Principal", "⚙️ Configuración"], label_visibility="collapsed")
    st.markdown("---")
    st.info(f"📂 Categorías: **{len(st.session_state.db)}**\n\n📝 Scripts: **{contar_scripts()}**")

# ==========================================
# VISTA 1: PANEL PRINCIPAL (DASHBOARD)
# ==========================================
if modo == "🚀 Panel Principal":
    st.title("Centro de Operaciones TIC")
    st.markdown("Busca, filtra y copia tus respuestas estandarizadas en un clic.")
    
    # Buscador principal
    busqueda = st.text_input("🔍 ¿Qué problema estás resolviendo hoy?", 
                             value=st.session_state.filtro_rapido, 
                             placeholder="Ej. J139, VLAN, Service Tag, Zoho...")
    
    # Filtros rápidos (Tags) - Diseño moderno con columnas
    st.caption("Filtros rápidos:")
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1,1,1,1,4])
    with col_f1: st.button("📞 Avaya", on_click=set_filtro, args=("Avaya",), use_container_width=True)
    with col_f2: st.button("🎫 Zoho", on_click=set_filtro, args=("Zoho",), use_container_width=True)
    with col_f3: st.button("🌐 Cisco", on_click=set_filtro, args=("Cisco",), use_container_width=True)
    with col_f4: st.button("❌ Limpiar", on_click=set_filtro, args=("",), use_container_width=True)

    st.markdown("---")

    # Mostrar tarjetas de resultados
    termino = busqueda.lower()
    hubo_resultados = False

    for categoria, scripts in st.session_state.db.items():
        scripts_filtrados = {
            t: txt for t, txt in scripts.items() 
            if termino in t.lower() or termino in txt.lower() or termino in categoria.lower()
        }

        if scripts_filtrados:
            hubo_resultados = True
            st.markdown(f"#### {categoria}")
            
            # Tarjetas distribuidas en una cuadrícula limpia
            cols = st.columns(2)
            for i, (titulo, texto) in enumerate(scripts_filtrados.items()):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{titulo}**")
                        st.code(texto, language="text")
                        
    if not hubo_resultados:
        st.warning("No hay resultados. Intenta buscar otro término o limpia los filtros.")

# ==========================================
# VISTA 2: CONFIGURACIÓN (UX OPTIMIZADA)
# ==========================================
elif modo == "⚙️ Configuración":
    st.title("⚙️ Configuración del Entorno")
    st.markdown("Administra tu base de conocimientos.")
    
    # Pestañas para no saturar la vista
    tab_scripts, tab_categorias = st.tabs(["📝 Gestionar Scripts", "📁 Gestionar Categorías"])
    
    with tab_scripts:
        if not st.session_state.db:
            st.warning("Crea una categoría primero.")
        else:
            cat_seleccionada = st.selectbox("📂 Selecciona la categoría a editar:", list(st.session_state.db.keys()))
            
            # Crear nuevo en una tarjeta destacada
            with st.container(border=True):
                st.markdown("##### ✨ Añadir nuevo script")
                col_n1, col_n2 = st.columns([1, 2])
                with col_n1:
                    nuevo_tit = st.text_input("Título (Ej. Reinicio IP Office)", key="n_tit")
                with col_n2:
                    nuevo_txt = st.text_area("Texto de la respuesta", height=68, key="n_txt")
                if st.button("Guardar Script", type="primary"):
                    if nuevo_tit and nuevo_txt:
                        st.session_state.db[cat_seleccionada][nuevo_tit] = nuevo_txt
                        sincronizar_datos()
                        st.success("Añadido correctamente.")
                        st.rerun()

            st.markdown("---")
            
            # Editar existentes
            for titulo, texto in st.session_state.db[cat_seleccionada].items():
                with st.expander(f"✏️ Editar: {titulo}"):
                    nuevo_texto = st.text_area("Contenido", value=texto, key=f"edit_{titulo}")
                    c1, c2, c3 = st.columns([2, 2, 4])
                    with c1:
                        if st.button("💾 Guardar", key=f"sv_{titulo}", use_container_width=True):
                            st.session_state.db[cat_seleccionada][titulo] = nuevo_texto
                            sincronizar_datos()
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Borrar", key=f"dl_{titulo}", use_container_width=True):
                            del st.session_state.db[cat_seleccionada][titulo]
                            sincronizar_datos()
                            st.rerun()

    with tab_categorias:
        with st.container(border=True):
            st.markdown("##### ➕ Crear Categoría")
            nueva_cat = st.text_input("Nombre (Usa emojis de Windows con Win + .)")
            if st.button("Crear"):
                if nueva_cat and nueva_cat not in st.session_state.db:
                    st.session_state.db[nueva_cat] = {}
                    sincronizar_datos()
                    st.rerun()

        with st.container(border=True):
            st.markdown("##### ❌ Eliminar Categoría")
            cat_a_borrar = st.selectbox("Selecciona:", [""] + list(st.session_state.db.keys()))
            if st.button("Eliminar (Peligro)"):
                if cat_a_borrar:
                    del st.session_state.db[cat_a_borrar]
                    sincronizar_datos()
                    st.rerun()
