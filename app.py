import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Autosol - Eficiencia de Conversión", layout="wide", page_icon="📈")

# --- CONEXIÓN A GOOGLE DRIVE ---
SHEET_ID = '1wNL_9Fw74WplbgtPLIBsTSDLcSbVf7KkCRV7Y2M3zvs'
SHEET_NAME = 'Hoja1' 
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(URL)
    df.columns = [c.strip() for c in df.columns]
    
    # Procesamiento de Fechas (Fecha de Creación como eje principal)
    df['Fecha creación'] = pd.to_datetime(df['Fecha creación'], errors='coerce')
    df = df.dropna(subset=['Fecha creación'])
    
    # Extraer componentes de tiempo para filtros
    df['Año Creación'] = df['Fecha creación'].dt.year
    df['Mes Creación'] = df['Fecha creación'].dt.strftime('%B')
    df['Fecha_Corta'] = df['Fecha creación'].dt.date
    
    # Columna N: Asegurar que sea numérica (Tiempo de respuesta en minutos laborables)
    df['Primer Contacto [Min]'] = pd.to_numeric(df['Primer Contacto [Min]'], errors='coerce').fillna(0)
    
    return df

try:
    df = load_data()
    vendedor_col = 'Oportunidad: Propietario de oportunidad: Nombre completo'

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("📂 Filtros por Fecha de Creación")
    
    # Filtro de Calendario por Fecha de Creación
    min_date = df['Fecha_Corta'].min()
    max_date = df['Fecha_Corta'].max()
    
    rango_fechas = st.sidebar.date_input(
        "Rango de Creación de Leads",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.sidebar.divider()
    sel_vendedor = st.sidebar.multiselect("Vendedor", options=sorted(df[vendedor_col].unique()))
    sel_origen = st.sidebar.multiselect("Origen del Lead", options=df['Origen'].unique())

    # --- LÓGICA DE FILTRADO ---
    df_f = df.copy()
    if len(rango_fechas) == 2:
        df_f = df_f[(df_f['Fecha_Corta'] >= rango_fechas[0]) & (df_f['Fecha_Corta'] <= rango_fechas[1])]
    if sel_vendedor:
        df_f = df_f[df_f[vendedor_col].isin(sel_vendedor)]
    if sel_origen:
        df_f = df_f[df_f['Origen'].isin(sel_origen)]

    # --- CUERPO DEL DASHBOARD ---
    st.title("🚀 Gestión de Leads y Tiempos de Respuesta")
    st.info("Nota: El tiempo promedio se calcula sobre minutos de concesionario abierto (Columna N).")

    # KPIs Principales
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Leads Creados", len(df_f))
    with k2:
        # Columna M: Lead Convertido
        tasa = (df_f['Lead Convertido'].sum() / len(df_f)) * 100 if len(df_f) > 0 else 0
        st.metric("Tasa de Conversión", f"{tasa:.1f}%")
    with k3:
        promedio_min = df_f['Primer Contacto [Min]'].mean()
        st.metric("Respuesta Promedio", f"{promedio_min:.1f} min")
    with k4:
        # Alerta visual si el promedio es alto
        status = "🟢" if promedio_min < 30 else "🟡" if promedio_min < 60 else "🔴"
        st.metric("Estado de Respuesta", status)

    st.divider()

    # --- GRÁFICOS DE TIEMPO Y CONVERSIÓN ---
    col_a, col_b = st.columns(2)

    with col_a:
        # Gráfico de tiempo promedio por Vendedor
        st.subheader("⏱️ Tiempo de Respuesta por Vendedor")
        df_vendedor_tpo = df_f.groupby(vendedor_col)['Primer Contacto [Min]'].mean().reset_index().sort_values('Primer Contacto [Min]')
        fig_tpo = px.bar(df_vendedor_tpo, x='Primer Contacto [Min]', y=vendedor_col, 
                         orientation='h', color='Primer Contacto [Min]',
                         color_continuous_scale='RdYlGn_r', # Rojo para los más lentos, verde para los más rápidos
                         labels={'Primer Contacto [Min]': 'Minutos Promedio'})
        st.plotly_chart(fig_tpo, use_container_width=True)

    with col_b:
        # Relación entre Fecha de Creación y Tiempo de Respuesta
        st.subheader("📅 Evolución Diaria de Respuesta")
        df_diario = df_f.groupby('Fecha_Corta')['Primer Contacto [Min]'].mean().reset_index()
        fig_evol = px.line(df_diario, x='Fecha_Corta', y='Primer Contacto [Min]', 
                           markers=True, title="Minutos hasta contacto por día de creación")
        st.plotly_chart(fig_evol, use_container_width=True)

    st.divider()
    
    # Análisis de Ranking Detallado
    st.subheader("🏆 Tabla de Desempeño")
    ranking = df_f.groupby(vendedor_col).agg({
        'Primer Contacto [Min]': 'mean',
        'Lead Convertido': 'sum',
        'Origen': 'count'
    }).rename(columns={'Origen': 'Total Leads', 'Lead Convertido': 'Ventas', 'Primer Contacto [Min]': 'Min. Promedio'})
    
    ranking['% Eficacia'] = (ranking['Ventas'] / ranking['Total Leads']) * 100
    st.dataframe(ranking.sort_values('Min. Promedio'), use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar el dashboard: {e}")
