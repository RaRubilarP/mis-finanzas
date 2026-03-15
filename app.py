import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# Conexión a Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💰 Control Financiero Personal")

# --- LÓGICA DE DATOS ---
def obtener_datos():
    try:
        response = supabase.table("movimientos").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
    except:
        pass
    return pd.DataFrame()

df = obtener_datos()

# Función para formatear moneda chilena
def format_clp(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📝 Registro", "📊 Análisis"])

with tab1:
    st.subheader("Nuevo Movimiento")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = st.number_input("Monto (CLP)", min_value=0, step=1000)
        with col2:
            cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Cuentas", "Otros"])
            metodo = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito", "Transferencia"])
            desc = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar Movimiento"):
            if monto > 0:
                data = {"fecha": str(fecha), "tipo": tipo, "categoria": cat, "metodo": metodo, "monto": int(monto), "descripcion": desc}
                supabase.table("movimientos").insert(data).execute()
                st.success("✅ Guardado exitosamente")
                st.rerun()

with tab2:
    if not df.empty:
        # Métricas principales
        ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
        gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
        balance = ingresos - gastos

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Ingresos", format_clp(ingresos))
        m2.metric("Total Gastos", format_clp(gastos))
        m3.metric("Balance Total", format_clp(balance), delta=float(balance))

        st.divider()
        
        # --- GRÁFICO COMPARATIVO MENSUAL ---
        st.write("### 📅 Comparativa Mensual")
        # Agrupar por mes y tipo
        df_mensual = df.copy()
        df_mensual['Mes'] = df_mensual['fecha'].dt.strftime('%Y-%m')
        resumen_mes = df_mensual.groupby(['Mes', 'tipo'])['monto'].sum().reset_index()
        
        fig_barras = px.bar(resumen_mes, x='Mes', y='monto', color='tipo', 
                           barmode='group', labels={'monto': 'Monto (CLP)', 'tipo': 'Tipo'},
                           color_discrete_map={'Ingreso': '#00CC96', 'Gasto': '#EF553B'})
        st.plotly_chart(fig_barras, use_container_width=True)

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.write("### 🍰 Gastos por Categoría")
            df_gastos = df[df['tipo'] == 'Gasto']
            if not df_gastos.empty:
                fig_pie = px.pie(df_gastos, values='monto', names='categoria', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay gastos registrados para mostrar el gráfico.")
            
        with col_right:
            st.write("### 📜 Historial")
            df_historial = df.sort_values("fecha", ascending=False).copy()
            df_historial['monto'] = df_historial['monto'].apply(format_clp)
            st.dataframe(df_historial[["fecha", "tipo", "categoria", "monto", "descripcion"]], use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay datos. Registra tu primer movimiento para ver los gráficos.")
