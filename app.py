import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Control Financiero Compartido", layout="wide")

st.title("💰 Gestión de Gastos Compartida")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos existentes
df = conn.read(ttl="0") # ttl="0" asegura que siempre lea los datos más recientes

tab_registro, tab_resumen = st.tabs(["📝 Registrar", "📊 Análisis"])

with tab_registro:
    with st.form("nuevo_registro"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = st.number_input("Monto", min_value=0.0)
        with col2:
            cat = st.selectbox("Categoría", ["Alimentación", "Ocio", "Vivienda", "Transporte", "Sueldo", "Otros"])
            metodo = st.selectbox("Método", ["Tarjeta de Crédito", "Débito", "Efectivo"])
            desc = st.text_input("Descripción")
        
        if st.form_submit_button("Guardar"):
            nuevo_dato = pd.DataFrame([{
                "Fecha": str(fecha), "Tipo": tipo, "Categoría": cat,
                "Método_Pago": metodo, "Monto": monto, "Descripción": desc
            }])
            # Concatenar y actualizar Google Sheets
            actualizado = pd.concat([df, nuevo_dato], ignore_index=True)
            conn.update(data=actualizado)
            st.success("¡Datos sincronizados en la nube!")
            st.rerun()

with tab_resumen:
    if not df.empty:
        st.metric("Balance Total", f"${df[df['Tipo']=='Ingreso']['Monto'].sum() - df[df['Tipo']=='Gasto']['Monto'].sum():,.2f}")
        st.dataframe(df.tail(10))
    else:
        st.info("No hay datos aún.")

# Agregar al inicio del código anterior
password = st.sidebar.text_input("Contraseña de acceso", type="password")
if password != "12345678":
    st.warning("Por favor introduce la contraseña correcta.")
    st.stop()
