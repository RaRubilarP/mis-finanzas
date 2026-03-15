import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Configuración inicial
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# Conexión
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def format_clp(valor):
    return f"$ {int(valor):,.0f}".replace(",", ".")

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        res = supabase.table("movimientos").select("*").execute()
        if res.data:
            df_raw = pd.DataFrame(res.data)
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
            df_raw['monto'] = pd.to_numeric(df_raw['monto'])
            return df_raw
    except:
        pass
    return pd.DataFrame()

df = cargar_datos()

st.title("💰 Mi Panel de Finanzas")

tab_reg, tab_ana = st.tabs(["📝 Registrar", "📊 Análisis"])

with tab_reg:
    with st.form("registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_fecha = st.date_input("Fecha")
            f_tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            f_monto = st.number_input("Monto (CLP)", min_value=0, step=1000)
        with col2:
            f_cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Cuentas", "Otros"])
            f_met = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito", "Transferencia"])
            f_desc = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar"):
            if f_monto > 0:
                payload = {
                    "fecha": str(f_fecha), "tipo": f_tipo, "categoria": f_cat,
                    "metodo": f_met, "monto": int(f_monto), "descripcion": f_desc
                }
                supabase.table("movimientos").insert(payload).execute()
                st.success("¡Guardado!")
                st.cache_data.clear()
                st.rerun()

with tab_ana:
    if not df.empty:
        # Gráfico Mensual
        df_m = df.copy()
        df_m['Mes'] = df_m['fecha'].dt.strftime('%Y-%m')
        res_m = df_m.groupby(['Mes', 'tipo'])['monto'].sum().reset_index()
        fig = px.bar(res_m, x='Mes', y='monto', color='tipo', barmode='group',
                     color_discrete_map={'Ingreso': '#2ecc71', 'Gasto': '#e74c3c'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla
        df_view = df.sort_values('fecha', ascending=False).copy()
        df_view['monto'] = df_view['monto'].apply(format_clp)
        st.dataframe(df_view[['fecha', 'tipo', 'categoria', 'monto', 'descripcion']], use_container_width=True)
    else:
        st.info("Ingresa datos para ver el análisis.")
