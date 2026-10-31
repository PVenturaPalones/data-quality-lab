# Data Quality Lab 🔎

**Herramienta web de auditoría de datos y etiquetado manual de textos, desarrollada con Python y Streamlit.**

> Proyecto de portfolio orientado a tareas reales de *data annotation*, *data quality* y revisión humana de datasets. Contiene datos sintéticos y no utiliza servicios externos ni APIs de IA.

## ¿Qué hace?

- Importa un CSV en UTF-8 o utiliza 20 mensajes sintéticos de ejemplo.
- Detecta **textos vacíos**, **duplicados exactos normalizados** y **textos muy cortos**.
- Propone etiquetas mediante **reglas transparentes por palabras clave**. Son sugerencias, **no predicciones de un modelo de IA**.
- Permite **etiquetar y revisar manualmente** cada registro, añadir notas y escalar casos ambiguos.
- Muestra un resumen de calidad y el progreso del etiquetado.
- Exporta un CSV completo con trazabilidad y otro con registros revisados y etiquetados.

![Tecnologías](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-red) ![Tests](https://img.shields.io/badge/Pytest-Unit%20tests-green)

## Ejecución en Windows con VS Code

1. Instalá [Python](https://www.python.org/downloads/) (3.10 o posterior) y [VS Code](https://code.visualstudio.com/).
2. Abrí la carpeta `data-quality-lab` en VS Code.
3. Abrí una terminal en VS Code (**Terminal → New Terminal**) y ejecutá:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py
```

Si PowerShell no permite activar el entorno, utilizá directamente `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` y `.\.venv\Scripts\python.exe -m streamlit run app.py`, sin modificar las políticas del sistema.

La app normalmente aparece en `http://localhost:8501`.

En macOS/Linux, usá `python3 -m venv .venv`, `source .venv/bin/activate` y el resto de los comandos igual.

## Pruebas

```powershell
python -m pytest -q
```

Incluye pruebas de normalización, detección de errores, sugerencias conservadoras, exportación y conteo de revisión humana. En GitHub, un workflow ejecuta los tests en cada push.

## Cómo probarlo en 2 minutos

1. Abrí la app sin subir un archivo; aparece el CSV de ejemplo.
2. Verificá que se marcan filas vacías, duplicadas y cortas.
3. Cambiá *Etiqueta humana* y *Estado de revisión* en algunas filas.
4. Descargá el CSV anotado y abrilo con Excel.

## Formato de entrada

Un CSV con encabezados y al menos una columna de texto. Ejemplo:

```csv
id,mensaje
1,No puedo iniciar sesión
2,Mi pedido llegó tarde
```

Seleccioná qué columna contiene el texto. Se conservan las columnas originales. Las columnas nuevas llevan el prefijo `dq_`:

| Columna | Significado |
|---|---|
| `dq_id` | Identificador de fila dentro de la carga |
| `dq_texto` | Copia de la columna elegida |
| `dq_alertas` | Problemas detectados |
| `dq_sugerencia` | Etiqueta sugerida por reglas |
| `dq_etiqueta` | Decisión humana |
| `dq_estado` | Pendiente, Revisado o Escalar |
| `dq_notas` | Notas del revisor |

Para conocer los criterios de decisión, consultá [Guía de anotación](docs/guia_anotacion.md).

## Decisiones de diseño y límites

- **No hay IA generativa detrás:** el preetiquetado usa palabras clave. Por diseño, un mensaje ambiguo puede permanecer sin etiquetar.
- **No hay persistencia:** la app no tiene base de datos. Las ediciones se conservan en la sesión activa; **descargá el CSV antes de cerrar**.
- **No se eliminan filas automáticamente:** una alerta necesita revisión humana.
- **Duplicados exactos normalizados:** no detecta textos semánticamente equivalentes ni faltas ortográficas.
- **Límites del prototipo:** CSV UTF-8, hasta 5 MB y 5.000 filas para mantener fluida la edición.
- Para datos personales reales, evitá subir archivos sensibles a despliegues públicos sin revisar primero privacidad y acceso.

## Estructura

```text
data-quality-lab/
├── app.py                    # Interfaz de Streamlit
├── src/quality.py            # Auditoría y preetiquetado
├── sample_data/mensajes_demo.csv
├── tests/test_quality.py     # Pruebas automáticas
├── docs/guia_anotacion.md    # Protocolo de revisión humana
├── .github/workflows/tests.yml # CI al publicar en GitHub
├── .streamlit/config.toml    # Tema oscuro
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Próximas mejoras

- Etiquetado por lotes y comparación entre dos anotadores.
- Métricas de acuerdo inter-anotador.
- Reglas configurables desde la interfaz.
- Historial de cambios e importación del CSV anotado para continuar una sesión.

---
**Autor:** proyecto educativo de portfolio. La revisión humana y el análisis de errores son el enfoque principal.
