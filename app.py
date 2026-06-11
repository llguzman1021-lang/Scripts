import streamlit as st
import json
import os

# ==========================================
# CAPA DE DATOS (Lógica de Persistencia)
# ==========================================
class GestorDatos:
    """
    Esta clase maneja la conexión con los datos.
    Actualmente usa un JSON local, pero su estructura está lista 
    para ser reemplazada por una conexión a Google Sheets o SQLite.
    """
    def __init__(self, filepath="data.json"):
        self.filepath = filepath
        # Datos por defecto si el archivo no existe
        self.datos_base = {
            "📧 Correos": {
                "Solicitud de información": "Estimado usuario, para procesar su requerimiento necesitamos que nos comparta el Service Tag del equipo y la ubicación exacta de la oficina."
            },
            "🎫 Tickets ZohoDesk": {
                "Cierre estándar": "Incidente resuelto satisfactoriamente. Procedo a cerrar el ticket. Si persiste algún inconveniente, por favor reabrir este mismo ticket."
            }
        }

    def cargar(self):
        # Manejo de excepciones: Si el archivo no existe o está corrupto
        if not os.path.exists(self.filepath):
            self.guardar(self.datos_base)
            return self.datos_base
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Error crítico: El archivo data.json está corrupto. Cargando respaldo temporal.")
            return self.datos_base

    def guardar(self, datos):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)


# ==========================================
# INICIALIZACIÓN Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Gestor TIC Pro", page_icon="⚡", layout="centered")

# Inicializamos el gestor de datos
gestor = GestorDatos()

# Usamos session_state para mantener la app rápida y no leer el disco constantemente
if "db" not in st.session_state:
    st.session_state.db = gestor.cargar()

def sincronizar_datos():
    """Guarda el estado actual de la memoria en el archivo JSON."""
    gestor.guardar(st.session_state.db)

# ==========================================
# INTERFAZ DE USUARIO (UX/UI)
# ==========================================
st.title("⚡ Gestor TIC Pro")
st.caption("Central de estandarización de soporte | Arquitectura Modular")

# Separación clara de entornos
tab_operacion, tab_admin = st.tabs(["🚀 Modo Operación", "⚙️ Panel de Administración"])


# ------------------------------------------
# VISTA DE OPERACIÓN (Solo lectura y copiado)
# ------------------------------------------
with tab_operacion:
    col1, col2 = st.columns([3, 1])
    with col1:
        busqueda = st.text_input("🔍 Buscar respuesta rápida (ej. BIOS, SIP, Ticket)...").lower()
    
    st.markdown("---")

    datos_actuales = st.session_state.db
    hubo_resultados = False

    for categoria, scripts in datos_actuales.items():
        # Lógica de filtrado
        scripts_filtrados = {
            titulo: texto for titulo, texto in scripts.items() 
            if busqueda in titulo.lower() or busqueda in texto.lower()
        }

        if scripts_filtrados:
            hubo_resultados = True
            st.subheader(categoria)
            for titulo, texto in scripts_filtrados.items():
                with st.expander(f"📌 {titulo}"):
                    st.code(texto, language="text")
                    
    if not hubo_resultados:
        st.info("No se encontraron resultados para tu búsqueda.")


# ------------------------------------------
# VISTA DE ADMINISTRACIÓN (CRUD Completo)
# ------------------------------------------
with tab_admin:
    st.info("⚠️ Los cambios realizados aquí alterarán la base de datos de respuestas.")
    
    # 1. GESTIÓN DE CATEGORÍAS
    with st.expander("📁 Gestionar Categorías (Crear / Eliminar)", expanded=False):
        col_cat1, col_cat2 = st.columns(2)
        
        with col_cat1:
            nueva_cat = st.text_input("Nombre de la nueva categoría:")
            if st.button("➕ Añadir Categoría", use_container_width=True):
                if nueva_cat and nueva_cat not in st.session_state.db:
                    st.session_state.db[nueva_cat] = {}
                    sincronizar_datos()
                    st.success(f"Categoría '{nueva_cat}' creada.")
                    st.rerun()
                elif nueva_cat:
                    st.warning("La categoría ya existe.")
                    
        with col_cat2:
            cat_a_borrar = st.selectbox("Categoría a eliminar:", list(st.session_state.db.keys()))
            if st.button("❌ Eliminar Categoría", use_container_width=True):
                if cat_a_borrar:
                    del st.session_state.db[cat_a_borrar]
                    sincronizar_datos()
                    st.success(f"Categoría eliminada.")
                    st.rerun()

    st.markdown("---")

    # 2. GESTIÓN DE SCRIPTS (Añadir / Editar / Eliminar)
    if not st.session_state.db:
        st.warning("No hay categorías disponibles. Crea una primero.")
    else:
        cat_seleccionada = st.selectbox("Selecciona la categoría para gestionar sus scripts:", list(st.session_state.db.keys()))
        
        # Formulario para NUEVO script
        st.markdown("#### ➕ Añadir Nuevo Script")
        with st.form("form_nuevo_script", clear_on_submit=True):
            nuevo_tit = st.text_input("Título descriptivo:")
            nuevo_txt = st.text_area("Contenido del script:")
            btn_guardar = st.form_submit_button("Guardar Script")
            
            if btn_guardar:
                if nuevo_tit and nuevo_txt:
                    st.session_state.db[cat_seleccionada][nuevo_tit] = nuevo_txt
                    sincronizar_datos()
                    st.success("Script guardado correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor, llena ambos campos.")

        # Listado de scripts existentes para EDICIÓN / ELIMINACIÓN
        st.markdown(f"#### ✏️ Editar scripts en: {cat_seleccionada}")
        scripts_cat = st.session_state.db[cat_seleccionada]
        
        if not scripts_cat:
            st.caption("No hay scripts en esta categoría.")
        
        for titulo_actual, texto_actual in scripts_cat.items():
            with st.expander(f"⚙️ {titulo_actual}"):
                nuevo_texto_edit = st.text_area("Contenido:", value=texto_actual, key=f"txt_{cat_seleccionada}_{titulo_actual}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    # Actualizar
                    if st.button("💾 Actualizar", key=f"upd_{cat_seleccionada}_{titulo_actual}", use_container_width=True):
                        st.session_state.db[cat_seleccionada][titulo_actual] = nuevo_texto_edit
                        sincronizar_datos()
                        st.success("Actualizado")
                with col_btn2:
                    # Eliminar
                    if st.button("🗑️ Eliminar", key=f"del_{cat_seleccionada}_{titulo_actual}", use_container_width=True):
                        del st.session_state.db[cat_seleccionada][titulo_actual]
                        sincronizar_datos()
                        st.rerun()
