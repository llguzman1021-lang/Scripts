import streamlit as st

# Configuración visual
st.set_page_config(page_title="Central TIC Luis", page_icon="🚀", layout="wide")

# Estilo personalizado para que se vea más moderno
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stCodeBlock { border: 1px solid #d1d8e0; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Central de Comandos y Respuestas TIC")
st.info("Selecciona una categoría y haz clic en el icono de copiar del cuadro de texto.")

# --- DICCIONARIO DE SCRIPTS Y RESPUESTAS ---
# Aquí puedes ir agregando todo lo que necesites a futuro
scripts = {
    "📞 Telefonía Avaya": {
        "Migración H323 a SIP": "Se ha completado la migración de la extensión de protocolo H323 a SIP (Modelo J139) exitosamente. Pruebas de entrada y salida realizadas.",
        "Reinicio de Extensión": "Se ha procedido con el reinicio físico y lógico de la extensión. El registro con el servidor Avaya IP Office es correcto.",
        "Falla de registro": "Error de registro detectado. Se verifica VLAN de voz y estado de puerto en switch. Se reasigna contraseña de usuario en Manager."
    },
    "🌐 Redes Cisco (CCNA)": {
        "Configuración Básica": "enable\nconfigure terminal\nhostname [NOMBRE_SWITCH]\nenable secret class\nline con 0\npassword cisco\nlogin\nexit",
        "Verificar Interfaces": "show ip interface brief",
        "Guardar Configuración": "copy running-config startup-config"
    },
    "🎫 Soporte Zoho Desk": {
        "Respuesta Inicial": "Estimado usuario, hemos recibido su solicitud. Un técnico del equipo TIC ha sido asignado y se pondrá en contacto a la brevedad.",
        "Cierre por BIOS": "Caso cerrado: Se configuró el Service Tag en BIOS tras cambio de placa base. El equipo inicia correctamente.",
        "Solicitud de Datos": "Para continuar con su solicitud, por favor envíenos el Service Tag del equipo y su ubicación física (Oficina/Piso)."
    }
}

# --- INTERFAZ LATERAL (Sidebar) ---
st.sidebar.header("Menú de Navegación")
categoria = st.sidebar.selectbox("Elegir Categoría", list(scripts.keys()))

# --- CUERPO PRINCIPAL ---
st.header(f"Sección: {categoria}")

for nombre, contenido in scripts[categoria].items():
    with st.expander(f"📌 {nombre}", expanded=True):
        # Usamos st.code porque Streamlit añade automáticamente un botón de "COPIAR"
        st.code(contenido, language="text")
