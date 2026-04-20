import streamlit as st
import sqlite3
import pandas as pd

# ------------------- LOGIN -------------------
USUARIO = "admin"
CLAVE = "1234"

if "login" not in st.session_state:
    st.session_state.login = False

def login():
    st.title("🔐 Iniciar sesión")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if user == USUARIO and password == CLAVE:
            st.session_state.login = True
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

if not st.session_state.login:
    login()
    st.stop()

# ------------------- APP PRINCIPAL -------------------
st.set_page_config(page_title="Sistema de Nómina", page_icon="💼", layout="wide")

conn = sqlite3.connect("nomina.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado TEXT,
    fecha TEXT,
    horas REAL,
    pago_hora REAL,
    total REAL
)
""")
conn.commit()

st.title("💼 Sistema de Nómina")

# ------------------- FORMULARIO -------------------
with st.form("form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        empleado = st.text_input("Empleado")

    with col2:
        horas = st.number_input("Horas", min_value=0.0)

    with col3:
        pago_hora = st.number_input("Pago por hora", min_value=0.0)

    fecha = st.date_input("Fecha")

    if st.form_submit_button("Registrar"):
        total = horas * pago_hora
        cursor.execute("""
        INSERT INTO registros (empleado, fecha, horas, pago_hora, total)
        VALUES (?, ?, ?, ?, ?)
        """, (empleado, str(fecha), horas, pago_hora, total))
        conn.commit()
        st.success("Guardado")

# ------------------- FILTRO POR FECHA -------------------
st.subheader("📅 Filtrar registros")

col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("Desde")
with col2:
    fecha_fin = st.date_input("Hasta")

query = "SELECT * FROM registros WHERE 1=1"

if fecha_inicio:
    query += f" AND fecha >= '{fecha_inicio}'"
if fecha_fin:
    query += f" AND fecha <= '{fecha_fin}'"

df = pd.read_sql(query, conn)

# ------------------- MOSTRAR DATOS -------------------
st.subheader("📊 Registros")

if not df.empty:
    st.dataframe(df, use_container_width=True)

    total_pagado = df["total"].sum()
    st.metric("💰 Total filtrado", f"${total_pagado:.2f}")

    nombre_archivo = st.text_input("ingrese un nombre para descargar el archivo")
    nota = st.text("(nota: debe darle a la tecla enter despues de colocar el nombre al archivo)")
    if not nombre_archivo.strip():
        nombre_archivo = "nomina"

    st.subheader("✏️ Editar registros")

    csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8')

# ---------------------------------------- Guardar cambios -----------------------------------
    for i, row in df.iterrows():
        with st.expander(f"{row['empleado']} - ${row['total']:.2f}"):

            col1, col2, col3 = st.columns(3)

            with col1:
                nuevo_nombre = st.text_input("Empleado", row["empleado"], key=f"n{row['id']}")
        
            with col2:
                nuevas_horas = st.number_input("Horas", value=row["horas"], key=f"h{row['id']}")
        
            with col3:
                nuevo_pago = st.number_input("Pago/hora", value=row["pago_hora"], key=f"p{row['id']}")

            if st.button("💾 Guardar cambios", key=f"u{row['id']}"):
                nuevo_total = nuevas_horas * nuevo_pago

                cursor.execute("""
                UPDATE registros 
                SET empleado=?, horas=?, pago_hora=?, total=?
                WHERE id=?
                """, (nuevo_nombre, nuevas_horas, nuevo_pago, nuevo_total, row["id"]))

                conn.commit()
                st.success("Registro actualizado")
                st.rerun()    

# ---------------------------------------- Boton de descarga -----------------------------------------------
    st.download_button(
    "⬇️ Descargar Nómina",
    csv,
    f"{nombre_archivo}.csv",
    "text/csv",
    key="descargar_nomina"
)
else:
    st.info("No hay registros en ese rango")

# ------------------- BORRAR TODO -------------------
st.subheader("Eliminar nominas")

confirmar = st.checkbox("Confirmar eliminación total")

if confirmar:
    if st.button("🧨 Borrar todo"):
        cursor.execute("DELETE FROM registros")
        conn.commit()
        st.error("Todos los datos eliminados")
        st.rerun()
