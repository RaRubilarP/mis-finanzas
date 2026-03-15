import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# 2. CONEXIÓN A SUPABASE
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error en las credenciales de Secrets. Revisa SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

# Función para formato moneda chilena (CLP)
def format_clp(valor):
    try:
        return f"$ {int(valor):,.0f}".replace(",", ".")
    except:
        return "$ 0"

# 3. LECTURA DE DATOS (CON CACHÉ PARA VELOCIDAD)
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        res = supabase.table("movimientos").select("*").execute()
        if res.data:
            df_raw = pd.DataFrame(res.data)
            # Asegurar tipos de datos para evitar errores en gráficos
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
            df_raw['monto'] = pd.to_numeric(df_raw['monto'])
            return df_raw
    except:
        pass
    return pd.DataFrame()

df = cargar_datos()

st.title("💰 Control Financiero Personal (CLP)")

# 4. PESTAÑAS
tab_reg, tab_ana = st.tabs(["📝 Registro", "📊 Análisis"])

with tab_reg:
    st.subheader("Nuevo Movimiento")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_fecha = st.date_input("Fecha")
            f_tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            f_monto = st.number_input("Monto (CLP)", min_value=0, step=1000)
        with col2:
            f_cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Cuentas", "Otros"])
            f_met = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito", "Transferencia"])
            f_desc = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar Movimiento"):
            if f_monto > 0:
                payload = {
                    "fecha": str(f_fecha),
                    "tipo": f_tipo,
                    "categoria": f_cat,
                    "metodo": f_met,
                    "monto": int(f_monto),
                    "descripcion": f_desc if f_desc else "Sin descripción"
                }
                try:
                    supabase.table("movimientos").insert(payload).execute()
                    st.success(f"✅ ¡Guardado! {format_clp(f_monto)}")
                    st.balloons()
                    st.cache_data.clear() # Limpia el caché para que el análisis se actualice
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El monto debe ser mayor a 0.")

with tab_ana:
    if not df.empty:
        # MÉTRICAS
        ing = df[df['tipo'] == 'Ingreso']['monto'].sum()
        gas = df[df['tipo'] == 'Gasto']['monto'].sum()
        bal = ing - gas

        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos Totales", format_clp(ing))
        c2.metric("Gastos Totales", format_clp(gas))
        c3.metric("Balance Neto", format_clp(bal), delta=float(bal))

        st.divider()

        # GRÁFICOS
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("### 📈 Evolución Mensual")
            df_m = df.copy()
            df_m['Mes'] = df_m['fecha'].dt.strftime('%Y-%m')
            res_m = df_m.groupby(['Mes', 'tipo'])['monto'].sum().reset_index()
            fig_b = px.bar(res_m, x='Mes', y='monto', color='tipo', barmode='group',
                          color_discrete_map={'Ingreso': '#2ecc71', 'Gasto': '#e74c3c'})
            st.plotly_chart(fig_b, use_container_width=True)

        with g2:
            st.write("### 🍰 Gastos por Categoría")
            df_g = df[df['tipo'] == 'Gasto']
            if not df_g.empty:
                fig_p = px.pie(df_g, values='monto', names='categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("No hay gastos para mostrar.")

        st.divider()
        st.write("### 📋 Historial")
        df_ver = df.sort_values('fecha', ascending=False).copy()
        df_ver['monto'] = df_ver['monto'].apply(format_clp)
        st.dataframe(df_ver[['fecha', 'tipo', 'categoria', 'monto', 'metodo', 'descripcion']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos. Ingresa tu primer movimiento en la pestaña de Registro.")
