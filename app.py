import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px # Nueva para gráficos

# Configuración de página
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# Conexión a Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💰 Control Financiero Personal")

# --- LÓGICA DE DATOS ---
def obtener_datos():
    response = supabase.table("movimientos").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    return pd.DataFrame()

df = obtener_datos()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📝 Registro", "📊 Análisis"])

with tab1:
    st.subheader("Nuevo Movimiento")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = st.number_input("Monto (CLP)", min_value=0, step=500)
        with col2:
            cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Otros"])
            metodo = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito"])
            desc = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar"):
            data = {"fecha": str(fecha), "tipo": tipo, "categoria": cat, "metodo": metodo, "monto": int(monto), "descripcion": desc}
            supabase.table("movimientos").insert(data).execute()
            st.success("✅ Guardado")
            st.rerun()

with tab2:
    if not df.empty:
        st.subheader("Resumen General (CLP)")
        
        # Cálculos
        ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
        gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
        balance = ingresos - gastos

        # Métricas con formato CLP
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Ingresos", f"$ {ingresos:,.0f}".replace(",", "."))
        m2.metric("Total Gastos", f"$ {gastos:,.0f}".replace(",", "."))
        m3.metric("Balance Actual", f"$ {balance:,.0f}".replace(",", "."), delta=float(balance))

        st.divider()
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("### Gastos por Categoría")
            df_gastos = df[df['tipo'] == 'Gasto']
            fig_pie = px.pie(df_gastos, values='monto', names='categoria', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_b:
            st.write("### Historial de Movimientos")
            # Formatear la columna monto para la tabla
            df_display = df.copy()
            df_display['monto'] = df_display['monto'].apply(lambda x: f"$ {x:,.0f}".replace(",", "."))
            st.dataframe(df_display[["fecha", "tipo", "categoria", "monto", "descripcion"]].sort_values("fecha", ascending=False), use_container_width=True)
    else:
        st.info("Ingresa tu primer movimiento para ver el análisis.")
