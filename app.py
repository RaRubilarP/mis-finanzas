import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Finanzas Pro", layout="centered")

# Conexión a Supabase usando tus Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💰 Control de Gastos Pro")

# --- FORMULARIO DE INGRESO ---
with st.form("form_gastos", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha")
        tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
        monto = st.number_input("Monto", min_value=0, step=100)
    with col2:
        cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Otros"])
        metodo = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito"])
        desc = st.text_input("Descripción")
    
    if st.form_submit_button("Guardar Movimiento"):
        if monto > 0:
            data = {
                "fecha": str(fecha),
                "tipo": tipo,
                "categoria": cat,
                "metodo": metodo,
                "monto": int(monto),
                "descripcion": desc
            }
            try:
                supabase.table("movimientos").insert(data).execute()
                st.success("✅ ¡Guardado en Supabase!")
                st.balloons()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- TABLA DE VISUALIZACIÓN ---
st.divider()
st.subheader("📊 Últimos Movimientos")
try:
    response = supabase.table("movimientos").select("*").order("fecha", desc=True).limit(10).execute()
    if response.data:
        df = pd.DataFrame(response.data)
        st.dataframe(df[["fecha", "tipo", "categoria", "monto", "descripcion"]], use_container_width=True)
    else:
        st.info("Aún no hay datos.")
except Exception as e:
    st.error("Error al cargar historial.")
