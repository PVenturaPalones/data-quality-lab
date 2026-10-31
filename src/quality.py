"""Deterministic audit and annotation helpers for short-text CSV datasets.

The rule-based classifier is intentionally only a suggestion: it is not a
machine-learning model and every suggested label requires human review.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd

LABELS = (
    "Sin etiquetar",
    "Soporte técnico",
    "Pagos",
    "Envíos",
    "Cuenta",
    "Otros",
)
STATUSES = ("Pendiente", "Revisado", "Escalar")

# Short, transparent, editable rules; no external API is used.
KEYWORDS = {
    "Soporte técnico": ("error", "falla", "bug", "cuelga", "bloquea", "funciona", "pantalla", "lento", "reinicia"),
    "Pagos": ("pago", "cobro", "cobraron", "cobrado", "tarjeta", "factura", "reembolso", "cuota", "precio", "devolucion"),
    "Envíos": ("envio", "entrega", "pedido", "paquete", "correo", "demora", "repartidor", "seguimiento"),
    "Cuenta": ("cuenta", "contrasena", "password", "sesion", "login", "registro", "usuario", "acceso"),
}


def normalized_text(value: object) -> str:
    """Normalize for comparisons without modifying original source values."""
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.split()).casefold()


def keyword_friendly_text(value: object) -> str:
    clean = normalized_text(value)
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", clean)
        if not unicodedata.combining(ch)
    )


def suggested_label(value: object) -> str:
    """A conservative lexical hint; ambiguous messages stay unlabelled."""
    text = keyword_friendly_text(value)
    if not text:
        return "Sin etiquetar"
    scores = {
        label: sum(bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)) for term in terms)
        for label, terms in KEYWORDS.items()
    }
    maximum = max(scores.values(), default=0)
    winners = [label for label, score in scores.items() if score == maximum and maximum > 0]
    return winners[0] if len(winners) == 1 else "Sin etiquetar"


def quality_flags(frame: pd.DataFrame, text_column: str, min_length: int = 12) -> list[list[str]]:
    """Flags missing, exact-normalized duplicate and short records.

    Only the second and subsequent occurrences of a normalized text are marked
    as duplicates. Empty records are *not* marked as duplicates.
    """
    if text_column not in frame.columns:
        raise ValueError(f"No existe la columna de texto: {text_column}")
    if min_length < 1:
        raise ValueError("min_length debe ser mayor que cero")

    normalized = frame[text_column].map(normalized_text)
    duplicates = normalized.ne("") & normalized.duplicated(keep="first")
    flags: list[list[str]] = []
    for text, duplicate in zip(normalized, duplicates):
        current = []
        if not text:
            current.append("Texto vacío")
        else:
            if bool(duplicate):
                current.append("Duplicado")
            if len(text) < min_length:
                current.append("Texto corto")
        flags.append(current)
    return flags


def prepare_records(frame: pd.DataFrame, text_column: str, min_length: int = 12) -> pd.DataFrame:
    """Return an editable dataset retaining all original columns."""
    if frame.empty:
        raise ValueError("El CSV debe contener al menos una fila")
    if text_column not in frame.columns:
        raise ValueError(f"No existe la columna de texto: {text_column}")
    if any(name.startswith("dq_") for name in frame.columns):
        raise ValueError("Los nombres de columnas dq_* están reservados para la aplicación")
    result = frame.copy().reset_index(drop=True)
    flags = quality_flags(result, text_column, min_length)
    result.insert(0, "dq_id", range(1, len(result) + 1))
    result["dq_texto"] = result[text_column].fillna("").astype(str)
    result["dq_alertas"] = [" · ".join(row) if row else "Sin alertas" for row in flags]
    result["dq_sugerencia"] = result[text_column].map(suggested_label)
    result["dq_etiqueta"] = "Sin etiquetar"
    result["dq_estado"] = "Pendiente"
    result["dq_notas"] = ""
    return result


@dataclass(frozen=True)
class AuditSummary:
    total: int
    missing: int
    duplicate: int
    short: int
    with_issues: int
    reviewed: int
    escalated: int
    labelled: int


def summarize(frame: pd.DataFrame) -> AuditSummary:
    """Summarize prepared/edited records without interpreting hints as human labels."""
    required = {"dq_alertas", "dq_estado", "dq_etiqueta"}
    if not required.issubset(frame.columns):
        raise ValueError("Faltan columnas generadas por la aplicación")
    alertas = frame["dq_alertas"].fillna("")
    return AuditSummary(
        total=len(frame),
        missing=int(alertas.str.contains("Texto vacío", regex=False).sum()),
        duplicate=int(alertas.str.contains("Duplicado", regex=False).sum()),
        short=int(alertas.str.contains("Texto corto", regex=False).sum()),
        with_issues=int((alertas != "Sin alertas").sum()),
        reviewed=int((frame["dq_estado"] == "Revisado").sum()),
        escalated=int((frame["dq_estado"] == "Escalar").sum()),
        labelled=int((frame["dq_etiqueta"] != "Sin etiquetar").sum()),
    )


def csv_bytes(frame: pd.DataFrame) -> bytes:
    """Export UTF-8 with BOM for easier opening in Microsoft Excel."""
    return frame.to_csv(index=False).encode("utf-8-sig")
