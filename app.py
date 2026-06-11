import streamlit as st
import json
import os

# ==========================================
# CAPA DE DATOS (Con Sanitización Antierrores)
# ==========================================
class GestorDatos:
    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        self.datos_base = {
            "📧 Correos": {
                "Solicitud de información": "Estimado usuario, para procesar su requerimiento necesitamos que nos comparta el Service Tag del equipo y la ubicación exacta de la oficina."
            },
            "🎫 Tickets ZohoDesk": {
                "Cierre estándar": "Incidente resuelto satisfactoriamente. Procedo a cerrar el ticket. Si persiste algún inconveniente, por favor reabrir este mismo ticket."
            },
            "📞 Telefonía Avaya": {
                "Migración J139": "Se ha completado la migración de la extensión a protocolo SIP (J139) exitosamente. Pruebas de entrada y salida realizadas."
            }
        }

    def cargar(self):
        if not os.path.exists(self.filepath):
            self.guardar(self.datos_base)
            return self.datos_base
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # SANITIZACIÓN: Evita el AttributeError asegurando que cada categoría sea un diccionario
                if not isinstance(data, dict):
                    return self.datos_base
                for categoria, scripts in data.items():
                    if not isinstance(scripts, dict):
                        data[categoria] = {} 
                return data
        except (json.JSONDecodeError, Exception):
            return self.datos_base

    def guardar(self, datos):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)


# ==========================================
# INICIALIZACIÓN
# ==========================================
# Usamos layout "wide" para aprovechar la pantalla como un verdadero dashboard
st.set_page_config(page_title="Gestor TIC Pro", page_icon="⚡", layout="wide")

gestor = GestorDatos()

if "db" not in st.session_state:
    st.session_state.db = gestor.cargar()

def sincronizar_datos():
    gestor.guardar(st.session_state.db)

def contar_scripts():
    total = 0
    for cat in st.session_state.db.values():
        total += len(cat)
    return total

# ==========================================
# NAVEGACIÓN LATERAL (UI Intuitiva)
# ==========================================
st.sidebar.title("⚡ Gestor TIC Pro")
st.sidebar.markdown("---")
modo = st.sidebar.radio("Navegación principal:", ["🔍 Buscar y Copiar", "⚙️ Panel de Administración"])
st.sidebar.markdown("---")

# Métricas rápidas en el sidebar
st.sidebar.metric("Categorías Totales", len(st.session_state.db))
st.sidebar.metric("Scripts Totales", contar_scripts())


# ==========================================
# VISTA 1: BUSCAR Y COPIAR (Uso diario)
# ==========================================
if modo == "🔍 Buscar y Copiar":
    st.title("🔍 Centro de Respuestas")
    st.markdown("Encuentra y copia rápidamente tus respuestas estandarizadas.")
    
    # Barra de búsqueda destacada
    busqueda = st.text_input("Escribe una palabra clave (ej. BIOS, Avaya, Ticket)...", placeholder="Buscar...").lower()
    st.markdown("---")

    hubo_resultados = False

    # Mostramos los datos usando tarjetas nativas (Containers)
    for categoria, scripts in st.session_state.db.items():
        # Filtramos los scripts que coincidan con la búsqueda
        scripts_filtrados = {
            titulo: texto for titulo, texto in scripts.items() 
            if busqueda in titulo.lower() or busqueda in texto.lower()
        }

        if scripts_filtrados:
            hubo_resultados = True
            st.subheader(f"📂 {categoria}")
            
            # Usamos columnas para organizar mejor visualmente si hay muchos scripts
            cols = st.columns(2)
            for i, (titulo, texto) in enumerate(scripts_filtrados.items()):
                # Distribuimos las tarjetas en dos columnas
                with cols[i % 2]:
                    # Usamos un contenedor con borde para que parezca una "tarjeta" profesional
                    with st.container(border=True):
                        st.markdown(f"**{titulo}**")
                        st.code(texto, language="text")
                        
    if not hubo_resultados:
        st.warning("No se encontraron coincidencias para tu búsqueda. Intenta con otra palabra.")


# ==========================================
# VISTA 2: PANEL DE ADMINISTRACIÓN (CRUD)
# ==========================================
elif modo == "⚙️ Panel de Administración":
    st.title("⚙️ Panel de Control")
    st.markdown("Añade, edita o elimina categorías y respuestas.")
    
    # --- SECCIÓN A: CATEGORÍAS ---
    with st.container(border=True):
        st.subheader("📁 Gestión de Categorías")
        col1, col2 = st.columns(2)
        
        with col1:
            nueva_cat = st.text_input("Nueva Categoría:")
            if st.button("➕ Crear Categoría", type="primary"):
                if nueva_cat and nueva_cat not in st.session_state.db:
                    st.session_state.db[nueva_cat] = {}
                    sincronizar_datos()
                    st.success("Categoría creada.")
                    st.rerun()
                    
        with col2:
            cat_a_borrar = st.selectbox("Categoría a eliminar:", [""] + list(st.session_state.db.keys()))
            if st.button("❌ Eliminar Categoría") and cat_a_borrar:
                del st.session_state.db[cat_a_borrar]
                sincronizar_datos()
                st.success("Categoría eliminada.")
                st.rerun()

    # --- SECCIÓN B: SCRIPTS ---
    if st.session_state.db:
        st.markdown("### 📝 Gestión de Scripts")
        
        # Filtro de categoría activa
        cat_seleccionada = st.selectbox("Selecciona en qué categoría trabajar:", list(st.session_state.db.keys()))
        
        # Área para añadir nuevo script
        with st.expander(f"➕ Añadir nuevo script en '{cat_seleccionada}'", expanded=False):
            with st.form("form_nuevo", clear_on_submit=True):
                nuevo_tit = st.text_input("Nombre / Título:")
                nuevo_txt = st.text_area("Contenido / Respuesta:")
                if st.form_submit_button("Guardar Script"):
                    if nuevo_tit and nuevo_txt:
                        st.session_state.db[cat_seleccionada][nuevo_tit] = nuevo_txt
                        sincronizar_datos()
                        st.success("Script añadido.")
                        st.rerun()
                    else:
                        st.error("Rellena todos los campos.")

        # Área para editar/eliminar scripts existentes
        scripts_actuales = st.session_state.db[cat_seleccionada]
        
        if not scripts_actuales:
            st.info("No hay scripts en esta categoría.")
        else:
            for titulo, texto in scripts_actuales.items():
                with st.container(border=True):
                    col_edit1, col_edit2 = st.columns([4, 1])
                    
                    with col_edit1:
                        nuevo_texto = st.text_area(f"Editar: {titulo}", value=texto, key=f"txt_{cat_seleccionada}_{titulo}")
                        if st.button("💾 Guardar cambios", key=f"upd_{cat_seleccionada}_{titulo}"):
                            st.session_state.db[cat_seleccionada][titulo] = nuevo_texto
                            sincronizar_datos()
                            st.success("Actualizado")
                            
                    with col_edit2:
                        st.markdown("<br><br>", unsafe_allow_html=True) # Espaciado
                        if st.button("🗑️ Eliminar", key=f"del_{cat_seleccionada}_{titulo}"):
                            del st.session_state.db[cat_seleccionada][titulo]
                            sincronizar_datos()
                            st.rerun()
