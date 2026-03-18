import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Autosol - Tiempo de Respuesta", layout="wide", page_icon="⏱️")

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
    df = df.dropna(subset=['Fecha creación'])
    
    # Columnas de Tiempo y Calendario
    df['Año'] = df['Fecha creación'].dt.year
    df['Mes'] = df['Fecha creación'].dt.strftime('%B')
    # Aseguramos que 'Primer Contacto [Min]' sea numérico
    df['Primer Contacto [Min]'] = pd.to_numeric(df['Primer Contacto [Min]'], errors='coerce').fillna(0)
    
    return df

try:
    df = load_data()
    vendedor_col = 'Oportunidad: Propietario de oportunidad: Nombre completo'

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Filtros de Gestión")
    
    # Filtro por Rango de Fechas
    min_d, max_d = df['Fecha creación'].min().date(), df['Fecha creación'].max().date()
    rango = st.sidebar.date_input("Periodo de Análisis", [min_d, max_d])

    # Filtros por categorías
    anos = st.sidebar.multiselect("Año", sorted(df['Año'].unique(), reverse=True))
    meses = st.sidebar.multiselect("Mes", df['Mes'].unique())
    vendedores = st.sidebar.multiselect("Vendedor", sorted(df[vendedor_col].unique()))

    # --- APLICACIÓN DE FILTROS ---
    df_f = df.copy()
    if len(rango) == 2:
        df_f = df_f[(df_f['Fecha creación'].dt.date >= rango[0]) & (df_f['Fecha creación'].dt.date <= rango[1])]
    if anos: df_f = df_f[df_f['Año'].isin(anos)]
    if meses: df_f = df_f[df_f['Mes'].isin(meses)]
    if vendedores: df_f = df_f[df_f[vendedor_col].isin(vendedores)]

    # --- DASHBOARD ---
    st.title("⏱️ Monitor de Tiempos y Conversión - Autosol")
    
    # KPIs Superiores
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Leads", len(df_f))
    with k2:
        # Columna M: Lead Convertido
        tasa = (df_f['Lead Convertido'].sum() / len(df_f)) * 100 if len(df_f) > 0 else 0
        st.metric("Tasa de Cierre", f"{tasa:.1f}%")
    with k3:
        # Columna N: Primer Contacto [Min]
        tpo_promedio = df_f['Primer Contacto [Min]'].mean()
        st.metric("Respuesta Promedio", f"{tpo_promedio:.1f} min")
    with k4:
        mejor_tpo = df_f.groupby(vendedor_col)['Primer Contacto [Min]'].mean().min()
        st.metric("Récord Rapidez", f"{mejor_tpo:.1f} min")

    st.divider()

    # --- ANÁLISIS POR VENDEDOR ---
    st.subheader("🏆 Performance de Vendedores")
    
    # Tabla de métricas por vendedor
    metricas_vendedor = df_f.groupby(vendedor_col).agg({
        'Lead Convertido': 'sum',
        'Primer Contacto [Min]': 'mean',
        'Origen': 'count'
    }).rename(columns={'Origen': 'Leads', 'Lead Convertido': 'Ventas', 'Primer Contacto [Min]': 'Min. Respuesta'}).reset_index()

    metricas_vendedor['% Eficacia'] = (metricas_vendedor['Ventas'] / metricas_vendedor['Leads']) * 100

    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Gráfico: Tiempo de Respuesta vs Ventas
        fig = px.scatter(metricas_vendedor, 
                         x="Min. Respuesta", 
                         y="% Eficacia", 
                         size="Leads", 
                         color=vendedor_col,
                         hover_name=vendedor_col,
                         title="Relación: Rapidez de Respuesta vs. % de Cierre",
                         labels={"Min. Respuesta": "Minutos en responder", "% Eficacia": "% de Ventas Ganadas"})
        # Línea de referencia de tiempo ideal (ejemplo 15 min)
        fig.add_vline(x=15, line_dash="dash", line_color="green", annotation_text="Meta 15 min")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.write("### Top Rapidez (Menos es mejor)")
        st.dataframe(metricas_vendedor[[vendedor_col, 'Min. Respuesta', 'Ventas']].sort_values('Min. Respuesta'), hide_index=True)

    st.divider()

    # --- DISTRIBUCIÓN TEMPORAL Y ORIGEN ---
    c3, c4 = st.columns(2)
    
    with c3:
        # ¿Qué días entran más leads?
        fig_dias = px.histogram(df_f, x='Día_Semana', color='Origen', title="Volumen de Leads por Día y Origen",
                                category_orders={"Día_Semana": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]})
        st.plotly_chart(fig_dias, use_container_width=True)
        
    with c4:
        # Evolución de tiempos por mes
        fig_evol = px.line(df_f.groupby('Mes')['Primer Contacto [Min]'].mean().reset_index(), 
                           x='Mes', y='Primer Contacto [Min]', title="Evolución del Tiempo de Respuesta Mensual")
        st.plotly_chart(fig_evol, use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar los datos: {e}")
