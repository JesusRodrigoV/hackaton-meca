# Diseño: Pulido visual de Reportes

## Intención
Hacer que la sección de reportes financieros sea más clara y profesional para dirección y finanzas, sin cambiar sus cálculos, fuentes de datos ni acciones de exportación.

## Alcance
- Mantener los siete reportes y su contenido actual.
- Dar más jerarquía a la cabecera, contexto de gestión y acciones de exportación/impresión.
- Replantear el selector de reportes para mostrar código, nombre y selección activa con buen uso en móvil.
- Agrupar y ordenar visualmente los filtros existentes.
- Refinar tarjetas y tablas: contraste, densidad, alineación numérica, encabezados y estados vacíos.
- Añadir transiciones de entrada discretas al cambiar de reporte, hover/focus visibles y respetar `prefers-reduced-motion`.
- Mantener la paleta institucional existente.

## Enfoques considerados
1. **Reporte editorial (elegido como supuesto):** mejora jerarquía, navegación, filtros y tablas aprovechando el layout y los datos existentes; es el mejor equilibrio entre pulido y bajo riesgo.
2. **Analítica centrada en gráficas:** requiere agregar visualizaciones o cambiar datos por reporte; amplía el alcance funcional.
3. **Ajuste CSS ligero:** conserva casi toda la presentación y limita el resultado a retoques; no alcanza el nivel de pulido solicitado.

## Restricciones y no objetivos
No cambiar endpoints, cálculos, forma de exportar, autenticación ni los datos financieros. No añadir dependencias ni animaciones que bloqueen navegación, lectura o accesibilidad.

## Implementación prevista
Modificar principalmente `reports.html` y `reports.scss`; ajustar `reports.ts` solo si hace falta para metadatos visuales existentes. Revisar el build de Angular; no se añade ni ejecuta una suite de pruebas para este cambio visual.
