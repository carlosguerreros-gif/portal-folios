import streamlit as st

st.set_page_config(page_title="Folios RedSalud", layout="centered")

st.title("Actualización Estados de Bonos")
st.caption("De 'No Conciliado' a 'Ingresado Ok'")

# --- CONEXIÓN BIGQUERY ---
MODO_PRUEBA = True
client = None

if "gcp_service_account" in st.secrets:
    try:
        from google.oauth2 import service_account
        from google.cloud import bigquery
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = bigquery.Client(credentials=creds, project=creds.project_id)
        MODO_PRUEBA = False
    except Exception as e:
        st.error(f"Error leyendo el Secret del JSON: {e}")
        client = None
        MODO_PRUEBA = True

if MODO_PRUEBA:
    st.warning("⚠️ Estoy en modo prueba, falta pegar el JSON en Secrets > Misterios", icon="⚠️")

# --- INPUT ---
folios_text = st.text_area(
    "Ingrese los folios de los bonos que cambiarán de estado",
    placeholder="Ej: 12345678\n87654321\n234...",
    height=200
)

c1, c2 = st.columns([2,1])
with c1:
    btn_actualizar = st.button("Actualizar Estados", type="primary", use_container_width=True)
with c2:
    btn_limpiar = st.button("Limpiar", use_container_width=True)

if btn_limpiar:
    st.rerun()

# --- LÓGICA AL ACTUALIZAR ---
if btn_actualizar:
    if not folios_text.strip():
        st.warning("Debes ingresar al menos un folio")
        st.stop()

    # Limpia: acepta comas, espacios, saltos de línea
    import re
    folios_raw = re.split(r'[\s,;]+', folios_text.strip())
    folios_unicos = sorted(list(set([f for f in folios_raw if f])))

    st.divider()
    st.subheader("Resultado")

    if MODO_PRUEBA:
        st.success(f"✅ MODO PRUEBA: Se actualizarían {len(folios_unicos)} bonos únicos")
        st.code(", ".join(folios_unicos), language="text")
        st.info("Cuando pegues el JSON real en Manage app > Settings > Secrets, este mismo botón hará el UPDATE en BigQuery.")
    else:
        # --- MODO REAL ---
        try:
            # CAMBIA AQUÍ TU TABLA REAL
            # Ejemplo: prod-bi-selfservice-cmd.tu_dataset.tu_tabla
            tabla = "prod-bi-selfservice-cmd.folios.bonos" 
            
            # Construimos la query segura
            query = f"""
            UPDATE `{tabla}`
            SET estado = 'Ingresado Ok'
            WHERE folio IN UNNEST(@folios)
            AND estado = 'No Conciliado'
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("folios", "STRING", folios_unicos)
                ]
            )
            
            job = client.query(query, job_config=job_config)
            job.result() # espera resultado

            st.success(f"✅ Se actualizaron {job.num_dml_affected_rows} bonos en BigQuery")
            st.caption(f"Folios procesados: {', '.join(folios_unicos[:20])}{'...' if len(folios_unicos)>20 else ''}")

        except Exception as e:
            st.error(f"❌ Error en BigQuery: {e}")
