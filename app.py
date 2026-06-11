import streamlit as st

# Configuración de diseño limpio
st.set_page_config(page_title="Gestor TIC", page_icon="⚡", layout="centered")

# Estilos CSS para un look moderno
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Gestor de Respuestas TIC")
st.subheader("Selecciona el tipo de respuesta que necesitas")

# Estructura de datos (Solo Correos y Tickets)
datos = {
    "📧 Correos": {
        "Solicitud de información": "Estimado usuario, para procesar su requerimiento necesitamos que nos comparta el Service Tag del equipo y la ubicación exacta de la oficina.",
        "Seguimiento pendiente": "Le escribo para darle seguimiento a su caso. Quedamos a la espera de su confirmación para proceder con la visita técnica.",
    },
    "🎫 Tickets ZohoDesk": {
        "BIOS - Service Tag": "Se ha resuelto el problema de BIOS mediante la configuración manual del Service Tag faltante en la placa base. Equipo operativo.",
        "Migración SIP (J139)": "Se ha completado la migración de la extensión H323 a protocolo SIP. Se han verificado las pruebas de voz y el registro en el servidor.",
        "Cierre estándar": "Incidente resuelto satisfactoriamente. Procedo a cerrar el ticket. Si persiste algún inconveniente, por favor reabrir este mismo ticket.",
    }
}

# Creación de pestañas (Tabs)
tab1, tab2 = st.tabs(["📧 Correos", "🎫 Tickets ZohoDesk"])

# Función para mostrar los bloques
def mostrar_contenido(categoria):
    for titulo, texto in datos[categoria].items():
        with st.expander(f"📌 {titulo}"):
            st.code(texto, language="text")

with tab1:
    mostrar_contenido("📧 Correos")

with tab2:
    mostrar_contenido("🎫 Tickets ZohoDesk")

# Pie de página minimalista
st.markdown("---")
st.caption("Central de productividad TIC - Acceso rápido")
