import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Mis Finanzas", layout="centered")

st.title("💰 Control de Gastos")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos actuales
try:
    df = conn.read(ttl="0")
except Exception:
    df = pd.DataFrame(columns=["Fecha", "Tipo", "Categoría", "Método_Pago", "Monto", "Descripción"])

# --- FORMULARIO DE REGISTRO ---
with st.container():
    st.subheader("📝 Nuevo Registro")
    with st.form("formulario", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            monto = st.number_input("Monto", min_value=0, step=100)
        with col2:
            cat = st.selectbox("Categoría", ["Alimentación", "Transporte", "Vivienda", "Ocio", "Salud", "Sueldo", "Otros"])
            metodo = st.selectbox("Método", ["Efectivo", "Débito", "Tarjeta de Crédito"])
            desc = st.text_input("Descripción (opcional)")
        
        boton_guardar = st.form_submit_button("Guardar Movimiento")

        if boton_guardar:
            if monto > 0:
                nuevo_registro = pd.DataFrame([{
                    "Fecha": str(fecha),
                    "Tipo": tipo,
                    "Categoría": cat,
                    "Método_Pago": metodo,
                    "Monto": monto,
                    "Descripción": desc
                }])
                
                # Unir datos nuevos con los viejos
                df_actualizado = pd.concat([df, nuevo_registro], ignore_index=True)
                
                # ACTUALIZAR EN GOOGLE SHEETS
                conn.update(data=df_actualizado)
                st.success("✅ ¡Guardado exitosamente en la nube!")
                st.balloons()
            else:
                st.warning("Por favor, ingresa un monto mayor a 0")

# --- VISUALIZACIÓN ---
st.divider()
st.subheader("📊 Últimos Movimientos")
if not df.empty:
    # Mostrar los últimos 5 registros
    st.table(df.tail(5))
else:
    st.info("Aún no hay registros en tu Google Sheet.")
