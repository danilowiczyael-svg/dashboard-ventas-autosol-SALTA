import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Autosol Live", layout="wide", page_icon="📈")

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
    
    # Columnas auxiliares para filtros
    df['Año'] = df['Fecha creación'].dt.year
    df['Mes'] = df['Fecha creación'].dt.strftime('%B') # Nombre del mes
    df['Día_Semana'] = df['Fecha creación'].dt.day_name()
    return df

try:
    df = load_data()
    vendedor_col = 'Oportunidad: Propietario de oportunidad: Nombre completo'

    # --- BARRA LATERAL: FILTROS AVANZADOS ---
    st.sidebar.header("🎛️ Panel de Filtros")
    
    # Filtro de Tiempo: Rango de Calendario
    min_date = df['Fecha creación'].min().date()
    max_date = df['Fecha creación'].max().date()
    date_range = st.sidebar.date_input("Rango de Fechas", [min_date, max_date])

    # Filtros de Categoría
    st.sidebar.subheader("Segmentación")
    sel_ano = st.sidebar.multiselect("Año", options=sorted(df['Año'].unique(), reverse=True))
    sel_mes = st.sidebar.multiselect("Mes", options=df['Mes'].unique())
    sel_vendedor = st.sidebar.multiselect("Vendedor", options=sorted(df[vendedor_col].unique()))
    sel_origen = st.sidebar.multiselect("Origen", options=df['Origen'].unique())

    # --- APLICAR FILTROS ---
    df_f = df.copy()
    
    if len(date_range) == 2:
        df_f = df_f[(df_f['Fecha creación'].dt.date >= date_range[0]) & (df_f['Fecha creación'].dt.date <= date_range[1])]
    if sel_ano:
        df_f = df_f[df_f['Año'].isin(sel_ano)]
    if sel_mes:
        df_f = df_f[df_f['Mes'].isin(sel_mes)]
    if sel_vendedor:
        df_f = df_f[df_f[vendedor_col].isin(sel_vendedor)]
    if sel_origen:
        df_f = df_f[df_f['Origen'].isin(sel_origen)]

    # --- CUERPO DEL DASHBOARD ---
    st.title("📊 Control Comercial Autosol")
    st.markdown(f"**Periodo:** {date_range[0]} al {date_range[1]} | **Leads filtrados:** {len(df_f)}")

    # KPIs Principales
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Leads", len(df_f))
    with kpi2:
        conv = (df_f['Lead Convertido'].sum() / len(df_f)) * 100 if len(df_f) > 0 else 0
        st.metric("Tasa de Cierre", f"{conv:.1f}%")
    with kpi3:
        tpo = df_f['Primer Contacto [Min]'].mean()
        st.metric("Tpo. Respuesta", f"{tpo:.1f} min")
    with kpi4:
        st.metric("Leads Ganados", int(df_f['Lead Convertido'].sum()))

    st.divider()

    # --- RANKING DE EFICIENCIA POR VENDEDOR ---
    st.subheader("🏆 Ranking de Eficiencia por Vendedor")
    
    # Agrupar datos por vendedor
    ranking = df_f.groupby(vendedor_col).agg({
        'Lead Convertido': 'sum',
        'Primer Contacto [Min]': 'mean',
        'Origen': 'count'
    }).rename(columns={'Origen': 'Total Leads', 'Lead Convertido': 'Cierres', 'Primer Contacto [Min]': 'Prom. Respuesta'}).reset_index()

    ranking['% Eficacia'] = (ranking['Cierres'] / ranking['Total Leads']) * 100

    col_rank1, col_rank2 = st.columns([2, 1])
    
    with col_rank1:
        # Gráfico comparativo: Cierres vs Eficacia
        fig_rank = px.bar(ranking.sort_values('% Eficacia', ascending=False), 
                          x=vendedor_col, y='% Eficacia', 
                          color='Prom. Respuesta',
                          title="Eficacia (%) y Rapidez de Respuesta (Color)",
                          labels={'% Eficacia': 'Tasa de Cierre (%)', 'Prom. Respuesta': 'Minutos'})
        st.plotly_chart(fig_rank, use_container_width=True)

    with col_rank2:
        st.write("Detalle de Performance")
        st.dataframe(ranking[[vendedor_col, 'Total Leads', 'Cierres', '% Eficacia']].sort_values('Cierres', ascending=False), hide_index=True)

    st.divider()

    # --- TENDENCIAS ---
    c_inf1, c_inf2 = st.columns(2)
    
    with c_inf1:
        # Distribución por Origen
        fig_pie = px.sunburst(df_f, path=['Origen', 'Producto de Interes'], title="Origen y Producto de Interés")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c_inf2:
        # Evolución de carga de trabajo
        df_time = df_f.groupby(df_f['Fecha creación'].dt.date).size().reset_index(name='Cantidad')
        fig_line = px.area(df_time, x='Fecha creación', y='Cantidad', title="Volumen de Ingreso de Leads")
        st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error("Error al cargar datos. Revisa la conexión con Google Drive.")
    st.info(f"Detalle técnico: {e}")
