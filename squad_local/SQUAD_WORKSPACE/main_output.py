import streamlit as st

def test_streamlit_app():
    # Configuración inicial del Streamlit
    st.title("Prueba de Aplicación Streamlit")
    
    # Verificación de la configuración
    assert st.title() == "Prueba de Aplicación Streamlit"
