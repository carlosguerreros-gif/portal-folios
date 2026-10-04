import streamlit as st
import re
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(page_title="Actualización Bonos", layout="centered")

st.title("Actualización Estados de Bonos")
st.write("De 'No Conciliado' a 'Ingresado Ok'")

# --- 1. CONEXIÓN PERMANENTE (reemplaza a auth.authenticate_user de Colab) ---
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(project="prod-bi-selfservice-cmd", credentials=credentials)

# --- 2. FUNCIÓN QUE YA TENÍAS EN COLAB (sin cambios) ---
def procesar_bonos(bonos_texto):
    lista_bonos = re.findall(r'[a-zA-Z0-9_-]+', str(bonos_texto))
    if not lista_bonos:
        return "⚠️ No se detectaron bonos válidos. Por favor, ingréselos nuevamente."
    
    lista_bonos_unicos = list(dict.fromkeys(lista_bonos))
    bonos_sql_format = ", ".join([f"'{bono}'" for bono in lista_bonos_unicos])

    query1 = f"""
    UPDATE `prod-bi-selfservice-cmd.EQUIPO_FINANZAS_CMD.imed_his_diario_centros`
    SET estado_cruce = 'Ingresado Ok'
    WHERE nro_bono_suc IN ({bonos_sql_format})
    """

    try:
        query_job = client.query(query1)
        query_job.result()
        filas_afectadas = query_job.num_dml_affected_rows
        mensaje_db = f"✅ Actualización en BigQuery ejecutada exitosamente ({filas_afectadas} registros actualizados)."
    except Exception as e:
        mensaje_db = f"❌ Error en BigQuery: {e}"

    cantidad = len(lista_bonos_unicos)
    bonos_formateados = ", ".join(lista_bonos_unicos)
    return f"{mensaje_db}\n\nSe actualizaron {cantidad} bonos únicos:\n{bonos_formateados}"

# --- 3. INTERFAZ (reemplaza a gr.Interface) ---
bonos_texto = st.text_area(
    "Ingrese los folios de los bonos que cambiarán de estado",
    height=200,
    placeholder="Pegue aquí los bonos (ej: B123, 456-A, C_789) separados por comas, espacios o saltos de línea..."
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Actualizar Estados", type="primary"):
        if bonos_texto:
            resultado = procesar_bonos(bonos_texto)
            st.text_area("Resultado", value=resultado, height=200)
        else:
            st.warning("Pegue bonos primero")
with col2:
    if st.button("Limpiar"):
        st.rerun()
