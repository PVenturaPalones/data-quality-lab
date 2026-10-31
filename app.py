"""Data Quality Lab — data auditing and manual text annotation in Streamlit."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.quality import LABELS, STATUSES, csv_bytes, prepare_records, summarize

APP_DIR = Path(__file__).resolve().parent
DEMO = APP_DIR / "sample_data" / "mensajes_demo.csv"
MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000

st.set_page_config(
    page_title="Data Quality Lab · Portfolio",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .block-container {padding-top: 2rem; max-width: 1350px;}
    [data-testid="stMetric"] {background: #141e2b; border:1px solid #263649;
        border-radius: 12px; padding: 16px;}
    [data-testid="stMetricLabel"] {color:#b7c3cf;}
    h1, h2, h3 {letter-spacing:-.03em;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Data Quality Lab")
st.caption("Auditoría de CSV · Anotación de texto · Control de calidad")
st.markdown(
    "Importá un archivo de mensajes, detectá problemas de calidad y anotá los registros "
    "manualmente. Las sugerencias automáticas son **reglas por palabras clave**, no IA."
)

with st.sidebar:
    st.header("Conjunto de datos")
    upload = st.file_uploader("Archivo CSV", type=["csv"], help="UTF-8, máximo 5 MB y 5.000 registros")
    st.caption("Sin archivo cargado se utiliza un conjunto de ejemplo con errores deliberados.")

    if upload is not None:
        raw_bytes = upload.getvalue()
        if len(raw_bytes) > MAX_BYTES:
            st.error("El archivo supera el límite de 5 MB.")
            st.stop()
    else:
        raw_bytes = DEMO.read_bytes()

    try:
        # Reading as strings preserves IDs with leading zeros and avoids accidental type inference.
        data = pd.read_csv(BytesIO(raw_bytes), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (UnicodeError, pd.errors.ParserError, ValueError, pd.errors.EmptyDataError) as exc:
        st.error("No se pudo leer el CSV. Usá UTF-8 con encabezados y comas como separador.")
        st.caption(str(exc))
        st.stop()

    if data.empty:
        st.error("El CSV está vacío.")
        st.stop()
    if len(data) > MAX_ROWS:
        st.error(f"El CSV tiene {len(data):,} filas. El máximo permitido es {MAX_ROWS:,}.")
        st.stop()
    if data.columns.duplicated().any():
        st.error("Hay encabezados de columna repetidos. Renombrá las columnas antes de continuar.")
        st.stop()
    if any(str(col).startswith("dq_") for col in data.columns):
        st.error("Los encabezados que comienzan por dq_ están reservados.")
        st.stop()

    preferred = ["mensaje", "text", "texto", "comment", "comentario", "review", "description"]
    default_idx = next((i for i, name in enumerate(data.columns) if name.lower() in preferred), 0)
    text_column = st.selectbox("Columna que contiene el texto", list(data.columns), index=default_idx)
    min_length = st.slider("Umbral de texto corto (caracteres)", 3, 50, 12)
    st.divider()
    st.caption("Procesamiento local en la sesión de Streamlit; esta app no incorpora una base de datos ni guarda los archivos de forma persistente.")
    st.caption("Proyecto educativo · Datos de ejemplo sintéticos")

try:
    prepared = prepare_records(data, text_column=text_column, min_length=min_length)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

# Editor key changes with the input, selected text column and threshold. This
# prevents edits made to one dataset from leaking into a different dataset.
import hashlib
editor_token = hashlib.sha256(raw_bytes + text_column.encode() + str(min_length).encode()).hexdigest()[:16]

st.subheader("1. Auditoría inicial")
initial = summarize(prepared)
metrics = st.columns(5)
metrics[0].metric("Registros", f"{initial.total:,}")
metrics[1].metric("Vacíos", initial.missing)
metrics[2].metric("Duplicados", initial.duplicate)
metrics[3].metric("Muy cortos", initial.short)
metrics[4].metric("Con alertas", initial.with_issues)

with st.expander("¿Cómo se detectan las alertas?", expanded=False):
    st.markdown(
        "- **Texto vacío:** valor vacío o solo espacios.\n"
        "- **Duplicado:** repetición exacta del texto normalizado, a partir de la segunda aparición.\n"
        "- **Texto corto:** menos caracteres que el umbral configurado.\n\n"
        "Estas reglas no detectan errores semánticos, sesgos ni duplicados aproximados."
    )

st.subheader("2. Etiquetado y revisión")
st.caption(
    "Modificá *Etiqueta*, *Estado* y *Notas*. Los datos originales, alertas y sugerencias están bloqueados. "
    "Una sugerencia no cuenta como etiqueta confirmada."
)
shown_columns = ["dq_id", "dq_texto", "dq_alertas", "dq_sugerencia", "dq_etiqueta", "dq_estado", "dq_notas"]
reviewed = st.data_editor(
    prepared,
    key=f"review_editor_{editor_token}",
    column_order=shown_columns,
    column_config={
        "dq_id": st.column_config.NumberColumn("#", width="small"),
        "dq_texto": st.column_config.TextColumn("Texto original", width="large"),
        "dq_alertas": st.column_config.TextColumn("Alertas", width="medium"),
        "dq_sugerencia": st.column_config.TextColumn("Sugerencia (reglas)", width="medium"),
        "dq_etiqueta": st.column_config.SelectboxColumn("Etiqueta humana", options=list(LABELS), required=True, width="medium"),
        "dq_estado": st.column_config.SelectboxColumn("Estado de revisión", options=list(STATUSES), required=True, width="medium"),
        "dq_notas": st.column_config.TextColumn("Notas del revisor", width="large", max_chars=400),
    },
    disabled=[col for col in prepared.columns if col not in {"dq_etiqueta", "dq_estado", "dq_notas"}],
    hide_index=True,
    num_rows="fixed",
    height=440,
    width="stretch",
)

# A human can mark a message "Revisado" without selecting a label; report the
# inconsistency instead of silently changing or counting their decision.
invalid = reviewed[(reviewed["dq_estado"] == "Revisado") & (reviewed["dq_etiqueta"] == "Sin etiquetar")]
if not invalid.empty:
    st.warning(f"Hay {len(invalid)} registros marcados como «Revisado» pero sin etiqueta humana. Completalos antes de exportar la versión validada.")

st.subheader("3. Resumen y exportación")
summary = summarize(reviewed)
left, mid, right = st.columns(3)
left.metric("Revisados", summary.reviewed)
mid.metric("Escalados", summary.escalated)
right.metric("Etiquetas asignadas", summary.labelled)

chart = reviewed["dq_etiqueta"].value_counts().rename_axis("Etiqueta").reset_index(name="Registros")
st.bar_chart(chart.set_index("Etiqueta"), horizontal=True, height=250)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "Descargar CSV con auditoría y anotaciones",
        data=csv_bytes(reviewed),
        file_name="data_quality_anotado.csv",
        mime="text/csv",
        type="primary",
        width="stretch",
    )
with col2:
    valid = reviewed[(reviewed["dq_estado"] == "Revisado") & (reviewed["dq_etiqueta"] != "Sin etiquetar")]
    st.download_button(
        "Descargar solo registros validados",
        data=csv_bytes(valid),
        file_name="data_quality_validado.csv",
        mime="text/csv",
        disabled=valid.empty,
        width="stretch",
    )

st.caption(
    "Las columnas dq_* se añaden al archivo original para conservar la trazabilidad. "
    "No se modifica el CSV que cargaste."
)
