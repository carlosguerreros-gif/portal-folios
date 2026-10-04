import streamlit as st
import re

st.set_page_config(page_title="Folios RedSalud", layout="centered")

# --- ESTILO PARA QUITAR ESPACIO SUPERIOR Y CENTRAR TÍTULO ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- ESTADOS ---
if "caja_folios" not in st.session_state:
    st.session_state["caja_folios"] = ""
if "resultado" not in st.session_state:
    st.session_state["resultado"] = None

def limpiar_caja():
    st.session_state["caja_folios"] = ""
    st.session_state["resultado"] = None

# --- TÍTULO CENTRADO Y CHICO ---
st.markdown("<h3 style='text-align: center; margin-bottom: 2px; font-size: 26px;'>Actualización Estados de Bonos</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 14px; margin-top:0;'>De 'No Conciliado' a 'Ingresado Ok'</p>", unsafe_allow_html=True)

def limpiar_caja():
    st.session_state["caja_folios"] = ""

st.markdown("<h3 style='margin-bottom:0px;'>Actualización Estados de Bonos</h3>", unsafe_allow_html=True)
st.caption("De 'No Conciliado' a 'Ingresado Ok'")

MODO_PRUEBA = True
client = None
bigquery = None

if "gcp_service_account" in st.secrets:
    try:
        from google.oauth2 import service_account
        from google.cloud import bigquery as bq
        bigquery = bq
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = bq.Client(credentials=creds, project=creds.project_id)
        MODO_PRUEBA = False
    except Exception as e:
        st.error(f"Error leyendo el Secret: {e}")

if MODO_PRUEBA:
    st.warning("⚠️ Estoy en modo prueba, falta pegar el JSON en Secrets > Misterios")

folios_text = st.text_area(
    "Ingrese los folios de los bonos que cambiarán de estado",
    placeholder="Ej: 12345678\n87654321\n234...",
    height=220,
    key="caja_folios"
)

# --- BOTONES ALINEADOS IZQ Y DER ---
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    btn_actualizar = st.button("Actualizar Estados", type="primary", use_container_width=True)
with c3:
    btn_limpiar = st.button("Limpiar", use_container_width=True, on_click=limpiar_caja)

if btn_actualizar:
    texto_actual = st.session_state["caja_folios"]
    if not texto_actual.strip():
        st.warning("Debes ingresar al menos un folio")
        st.stop()

    folios_raw = re.split(r'[\s,;]+', texto_actual.strip())
    folios_unicos = sorted(list(set([f for f in folios_raw if f])))

    st.divider()
    st.subheader("Resultado")

    if MODO_PRUEBA:
        st.success(f"✅ MODO PRUEBA: Se actualizarían {len(folios_unicos)} bonos")
        st.code(", ".join(folios_unicos))
    else:
        try:
            tabla = "prod-bi-selfservice-cmd.tu_dataset.tu_tabla_bonos"
            query = f"UPDATE `{tabla}` SET estado = 'Ingresado Ok' WHERE folio IN UNNEST(@folios) AND estado = 'No Conciliado'"
            job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ArrayQueryParameter("folios", "STRING", folios_unicos)])
            job = client.query(query, job_config=job_config)
            job.result()
            st.success(f"✅ Se actualizaron {job.num_dml_affected_rows} bonos")
        except Exception as e:
            st.error(f"❌ Error en BigQuery: {e}")
