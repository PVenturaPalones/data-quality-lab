# Guía de anotación y control de calidad

Esta guía define un proceso reproducible para revisar mensajes de soporte.

## Categorías

- **Soporte técnico:** fallos de aplicación, errores, lentitud o problemas técnicos.
- **Pagos:** cobros, facturación, tarjetas, reembolsos y precios.
- **Envíos:** entrega, paquetes, seguimiento, transportistas y pedidos.
- **Cuenta:** inicio de sesión, contraseñas, registro y recuperación de acceso.
- **Otros:** mensajes comprensibles que no pertenecen a las categorías anteriores.
- **Sin etiquetar:** aún no se tomó una decisión o el caso es ambiguo.

## Protocolo de revisión humana

1. Leé el texto original. No asumas que la etiqueta sugerida es correcta.
2. Consultá las alertas. Texto corto puede ser válido; duplicado no significa necesariamente error de negocio.
3. Identificá la intención principal y elegí una etiqueta.
4. Si el texto incluye dos intenciones sin una principal clara, usá **Escalar** y agregá una nota.
5. Marcá **Revisado** solo cuando hayas asignado una etiqueta humana válida.
6. Exportá solo los validados si necesitás un subconjunto listo para entrenamiento o análisis.

## Ejemplos

| Mensaje | Etiqueta | Motivo |
|---|---|---|
| «No puedo iniciar sesión» | Cuenta | Problema de acceso |
| «No llegó el paquete» | Envíos | Estado de entrega |
| «Me cobraron dos veces» | Pagos | Cobro duplicado |
| «Me cobraron y además falla el acceso» | Sin etiquetar + Escalar | Dos intenciones |
| «Gracias por la atención» | Otros | No es una incidencia |

## Métricas de calidad

La aplicación informa el **número de** registros vacíos, duplicados normalizados, muy cortos, revisados y escalados. No pretende medir precisión del modelo ni calidad global del dataset con un único porcentaje. Para medir consistencia humana, sería necesario contar con dos anotadores independientes y calcular acuerdo (por ejemplo, Cohen's kappa).

## Tratamiento de datos

Usá el ejemplo sintético para el portfolio. No subas mensajes reales con nombres, teléfonos o información personal a un hosting público sin autorización y controles apropiados.
