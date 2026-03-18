import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la hoja de Drive (Usa el ID de tu enlace)
SHEET_ID = '1wNL_9Fw74WplbgtPLIBsTSDLcSbVf7KkCRV7Y2M3zvs'
SHEET_NAME = 'Hoja1' # Cambia esto por el nombre de la pestaña en tu Drive
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

st.set_page_config(page_title="Dashboard Autosol Live", layout="wide")

@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def load_data():
    df = pd.read_csv(URL)
    # Limpieza básica basada en tus columnas 
    df['Fecha creación'] = pd.to_datetime(df['Fecha creación'], errors='coerce')
    return df

try:
    df = load_data()
    st.title("📊 Indicadores de Gestión - Autosol")

    # --- MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Leads", len(df))
    with c2:
        # Usando la columna "Lead Convertido" 
        conv_rate = (df["Lead Convertido"].sum() / len(df)) * 100
        st.metric("Tasa de Conversión", f"{conv_rate:.1f}%")
    with c3:
        # Usando la columna "Primer Contacto [Min]" 
        tpo_promedio = df["Primer Contacto [Min]"].mean()
        st.metric("Tpo. Respuesta Promedio", f"{tpo_promedio:.1f} min")

    # --- GRÁFICOS INTERACTIVOS ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Análisis por Producto de Interés 
        fig_prod = px.bar(df['Producto de Interes'].value_counts(), 
                          title="Demanda por Modelo", orientation='h')
        st.plotly_chart(fig_prod, use_container_width=True)
        
    with col_b:
        # Análisis por Origen del Lead 
        fig_origen = px.pie(df, names='Origen', title="Fuentes de Tráfico")
        st.plotly_chart(fig_origen, use_container_width=True)

except Exception as e:
    st.error(f"No se pudo conectar con el Drive. Verifica el nombre de la pestaña. Error: {e}")
