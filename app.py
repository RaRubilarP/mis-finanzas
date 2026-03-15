import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Finanzas Pro CLP", layout="wide")

# 2. Conexión segura a Supabase (Asegúrate de tener estos en Secrets)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Función para formatear moneda chilena (CLP)
def format_clp(valor):
    try:
        return f"$ {int(valor):,.0f}".replace(",", ".")
    except:
        return "$ 0"

# 3. Lógica de Lectura de Datos Blindada
def obtener_datos():
    try:
        # Traemos todos los datos de la tabla movimientos
        response = supabase.table("movimientos").select("*").execute()
        if response.data and len(response.data) > 0:
            df = pd.DataFrame(response.data)
            # Forzamos conversión de tipos para evitar errores en gráficos
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            return df
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")
    return pd.DataFrame()

df = obtener_datos()

st.title("💰 Control Financiero Personal")

# 4. Pestañas de Navegación
tab1, tab2 = st.tabs(["📝 Registro", "📊 Análisis"])

with tab1:
    st.subheader("Nuevo Movimiento")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_sel = st.date_input("Fecha")
            tipo_sel = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto_sel = st.number_input("Monto (CLP)", min_value=0, step=1000)
        with col2:
            cat_sel = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Cuentas", "Otros"])
            metodo_sel = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito", "Transferencia"])
            desc_sel = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar Movimiento"):
            if monto_sel > 0:
                data_insert = {
                    "fecha": str(fecha_sel),
                    "tipo": tipo_sel,
                    "categoria": cat_sel,
                    "metodo": metodo_sel,
                    "monto": int(monto_sel),
                    "descripcion": desc_sel if desc_sel else "" # Evita nulos
                }
                try:
                    supabase.table("movimientos").insert(data_insert).execute()
                    st.success(f"✅ ¡Guardado! {format_clp(monto_sel)}")
                    st.balloons()
                    st.rerun() # Refresca para actualizar el análisis automáticamente
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El monto debe ser mayor a $0")

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
        st.write("### 📅 Evolución Mensual")
        df_copy = df.copy()
        df_copy['Mes'] = df_copy['fecha'].dt.strftime('%Y-%m')
        resumen_mes = df_copy.groupby(['Mes', 'tipo'])['monto'].sum().reset_index()
        
        fig_barras = px.bar(resumen_mes, x='Mes', y='monto', color='tipo', 
                           barmode='group',
                           color_discrete_map={'Ingreso': '#00CC96', 'Gasto': '#EF553B'},
                           labels={'monto': 'Monto ($)', 'Mes': 'Mes'})
        st.plotly_chart(fig_barras, use_container_width=True)

        col_pie, col_hist = st.columns([1, 1])
        
        with col_pie:
            st.write("### 🍰 Gastos por Categoría")
            df_g = df[df['tipo'] == 'Gasto']
            if not df_g.empty:
                fig_p = px.pie(df_g, values='monto', names='categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
            
        with col_hist:
            st.write("### 📜 Historial")
            df_h = df.sort_values("fecha", ascending=False).copy()
            df_h['monto_formato'] = df_h['monto'].apply(format_clp)
            st.dataframe(df_h[["fecha", "tipo", "categoria", "monto_formato"]], use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos suficientes para el análisis. Ingresa un movimiento.")
