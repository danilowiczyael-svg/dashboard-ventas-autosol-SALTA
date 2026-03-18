import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Autosol Live", layout="wide", page_icon="📊")

# --- CONEXIÓN A GOOGLE DRIVE ---
SHEET_ID = '1wNL_9Fw74WplbgtPLIBsTSDLcSbVf7KkCRV7Y2M3zvs'
SHEET_NAME = 'Hoja1' 
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(URL)
    df.columns = [c.strip() for c in df.columns]
    
    # Procesamiento de Fechas
    df['Fecha creación'] = pd.to_datetime(df['Fecha creación'], errors='coerce')
    df = df.dropna(subset=['Fecha creación']) # Eliminar filas sin fecha
    
    # Crear columnas para filtros de tiempo
    df['Año'] = df['Fecha creación'].dt.year
    df['Mes'] = df['Fecha creación'].dt.month_name()
    df['Día'] = df['Fecha creación'].dt.day
    return df

try:
    df = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🎯 Filtros de Control")

    # 1. Filtro de Rango de Fechas (Calendario)
    min_date = df['Fecha creación'].min().date()
    max_date = df['Fecha creación'].max().date()
    
    date_range = st.sidebar.date_input(
        "Seleccionar Rango de Fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # 2. Filtros de Año y Mes (Multiselect)
    selected_year = st.sidebar.multiselect("Año", options=sorted(df['Año'].unique(), reverse=True))
    selected_month = st.sidebar.multiselect("Mes", options=df['Mes'].unique())

    # 3. Filtro de Vendedor
    vendedor_col = 'Oportunidad: Propietario de oportunidad: Nombre completo'
    selected_vendedor = st.sidebar.multiselect("Vendedor", options=sorted(df[vendedor_col].unique()))

    # --- LÓGICA DE FILTRADO ---
    df_selection = df.copy()

    # Filtrar por calendario
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_selection = df_selection[
            (df_selection['Fecha creación'].dt.date >= start_date) & 
            (df_selection['Fecha creación'].dt.date <= end_date)
        ]

    # Filtrar por selecciones específicas
    if selected_year:
        df_selection = df_selection[df_selection['Año'].isin(selected_year)]
    if selected_month:
        df_selection = df_selection[df_selection['Mes'].isin(selected_month)]
    if selected_vendedor:
        df_selection = df_selection[df_selection[vendedor_col].isin(selected_vendedor)]

    # --- DASHBOARD PRINCIPAL ---
    st.title("🚗 Dashboard de Gestión Comercial Autosol")
    st.markdown(f"Mostrando datos desde **{date_range[0]}** hasta **{date_range[1]}**")

    # Métricas clave
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Leads", len(df_selection))
    with m2:
        tasa = (df_selection['Lead Convertido'].sum() / len(df_selection)) * 100 if len(df_selection) > 0 else 0
        st.metric("Conversión", f"{tasa:.1f}%")
    with m3:
        tpo_resp = df_selection['Primer Contacto [Min]'].mean()
        st.metric("Tpo. Respuesta", f"{tpo_resp:.1f} min")
    with m4:
        st.metric("Vendedores Activos", df_selection[vendedor_col].nunique())

    st.divider()

    # Visualizaciones
    c1, c2 = st.columns(2)
    
    with c1:
        # Evolución temporal de leads
        df_evolucion = df_selection.groupby(df_selection['Fecha creación'].dt.date).size().reset_index(name='Leads')
        fig_linea = px.line(df_evolucion, x='Fecha creación', y='Leads', title="Evolución Diaria de Leads", markers=True)
        st.plotly_chart(fig_linea, use_container_width=True)
        
    with c2:
        # Ranking de Vendedores
        ranking = df_selection.groupby(vendedor_col).size().reset_index(name='Cantidad').sort_values(by='Cantidad', ascending=False)
        fig_vendedores = px.bar(ranking, x='Cantidad', y=vendedor_col, orientation='h', title="Leads por Vendedor", color='Cantidad')
        st.plotly_chart(fig_vendedores, use_container_width=True)

    # Tabla detallada
    if st.checkbox("Ver registros detallados"):
        st.dataframe(df_selection[['Fecha creación', vendedor_col, 'Origen', 'Producto de Interes', 'Oportunidad: Etapa']])

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
