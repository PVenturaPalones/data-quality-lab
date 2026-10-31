import pandas as pd
import pytest

from src.quality import (
    csv_bytes,
    normalized_text,
    prepare_records,
    quality_flags,
    suggested_label,
    summarize,
)


def test_normalization_preserves_source_and_cleans_whitespace():
    assert normalized_text("  HOLA   mundo  ") == "hola mundo"
    assert normalized_text(None) == ""
    assert normalized_text(float("nan")) == ""


@pytest.mark.parametrize(
    "message, expected",
    [
        ("Me cobraron dos veces con la tarjeta", "Pagos"),
        ("Necesito recuperar la contraseña", "Cuenta"),
        ("Mi paquete no llega", "Envíos"),
        ("La aplicación muestra un error", "Soporte técnico"),
        ("Me cobraron y mi paquete no llegó", "Sin etiquetar"),
        ("", "Sin etiquetar"),
    ],
)
def test_conservative_suggestions(message, expected):
    assert suggested_label(message) == expected


def test_flags_only_later_nonempty_exact_duplicates():
    sample = pd.DataFrame({"mensaje": ["Hola", " hola  ", "", "  ", "Texto largo sin fallas"]})
    flags = quality_flags(sample, "mensaje", min_length=6)
    assert flags[0] == ["Texto corto"]
    assert flags[1] == ["Duplicado", "Texto corto"]
    assert flags[2] == ["Texto vacío"]
    assert flags[3] == ["Texto vacío"]
    assert flags[4] == []


def test_prepare_preserves_columns_and_summary_is_human_only():
    original = pd.DataFrame({"source_id": ["001", "002", "003"], "mensaje": ["Error de pantalla", "Error de pantalla", ""]})
    result = prepare_records(original, "mensaje")
    assert result["source_id"].tolist() == ["001", "002", "003"]
    assert result["dq_id"].tolist() == [1, 2, 3]
    assert result["dq_etiqueta"].eq("Sin etiquetar").all()
    assert result.loc[0, "dq_sugerencia"] == "Soporte técnico"
    assert summarize(result).duplicate == 1
    assert summarize(result).missing == 1
    assert summarize(result).reviewed == 0
    result.loc[0, "dq_estado"] = "Revisado"
    result.loc[0, "dq_etiqueta"] = "Soporte técnico"
    assert summarize(result).labelled == 1
    assert summarize(result).reviewed == 1
    assert csv_bytes(result).startswith(b"\xef\xbb\xbf")


def test_invalid_text_column_and_reserved_names():
    sample = pd.DataFrame({"x": ["hola"]})
    with pytest.raises(ValueError):
        prepare_records(sample, "no_existe")
    with pytest.raises(ValueError):
        prepare_records(pd.DataFrame({"dq_fake": ["hola"]}), "dq_fake")


def test_minimum_length_must_be_positive():
    with pytest.raises(ValueError):
        quality_flags(pd.DataFrame({"texto": ["hola"]}), "texto", 0)
