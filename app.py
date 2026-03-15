import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# 2. Conexión segura a Supabase
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error en Secrets: {e}")
        st.stop()

supabase = init_connection()

# Función para formato moneda chilena (CLP)
def format_clp(valor):
    try:
        return f"$ {int(valor):,.0f}".replace(",", ".")
    except:
        return "$ 0"

# 3. Lectura de Datos Blindada
def cargar_datos():
    try:
        # Traemos todos los datos de la tabla movimientos
        res = supabase.table("movimientos").select("*").execute()
        if res.data:
            df_raw = pd.DataFrame(res.data)
            # Forzamos conversión de tipos para evitar errores en gráficos
            df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
            df_raw['monto'] = pd.to_numeric(df_raw['monto'], errors='coerce').fillna(0)
            return df_raw
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")
    return pd.DataFrame()

df = cargar_datos()

st.title("💰 Control Financiero Definitivo (CLP)")

# 4. Pestañas de Navegación
tab_reg, tab_ana = st.tabs(["📝 Registro de Movimientos", "📊 Análisis y Reportes"])

with tab_reg:
    st.subheader("Ingresar Nuevo Dato")
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
        
        if st.form_submit_button("Guardar en Base de Datos"):
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
                    # Intento de inserción
                    supabase.table("movimientos").insert(payload).execute()
                    st.success(f"✅ ¡Éxito! Guardado: {f_cat} por {format_clp(f_monto)}")
                    st.balloons()
                    st.rerun() # Refresca para actualizar el análisis
                except Exception as e:
                    st.error(f"Error técnico de Supabase: {e}")
                    st.info("💡 Asegúrate de haber desactivado el RLS en el panel de Supabase.")
            else:
                st.warning("El monto debe ser mayor a $0")

with tab_ana:
    if not df.empty:
        # Métricas principales
        ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
        gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
        balance = ingresos - gastos

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Ingresos", format_clp(ingresos))
        col_m2.metric("Total Gastos", format_clp(gastos))
        col_m3.metric("Balance Neto", format_clp(balance), delta=float(balance))

        st.divider()
        
        # --- GRÁFICO COMPARATIVO MENSUAL ---
        st.write("### 📅 Evolución Mensual")
        df_plot = df.copy()
        df_plot['Mes'] = df_plot['fecha'].dt.strftime('%Y-%m')
        resumen_mes = df_plot.groupby(['Mes', 'tipo'])['monto'].sum().reset_index()
        
        fig_barras = px.bar(resumen_mes, x='Mes', y='monto', color='tipo', 
                           barmode='group',
                           color_discrete_map={'Ingreso': '#2ecc71', 'Gasto': '#e74c3c'},
                           labels={'monto': 'Monto ($)', 'Mes': 'Mes'})
        st.plotly_chart(fig_barras, use_container_width=True)

        col_pie, col_hist = st.columns([1, 1])
        
        with col_pie:
            st.write("### 🍰 Gastos por Categoría")
            df_g = df[df['tipo'] == 'Gasto']
            if not df_g.empty:
                fig_p = px.pie(df_g, values='monto', names='categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
            else:
                st.info("No hay gastos registrados para graficar.")
            
        with col_hist:
            st.write("### 📜 Historial")
            df_h = df.sort_values("fecha", ascending=False).copy()
            df_h['monto_clp'] = df_h['monto'].apply(format_clp)
            st.dataframe(df_h[["fecha", "tipo", "categoria", "monto_clp"]], use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos suficientes para el análisis. Ingresa tu primer movimiento.")
