---
name: Enseña por Bolivia - Financial Design System
description: Institutional budgeting, financial execution, and audit governance design system
mode: operate
colors:
  bright-snow: "#F8F9FA"
  space-indigo: "#2B255C"
  forest-green: "#00923D"
  tuscan-sun: "#ECC562"
  deep-space-blue: "#0D2439"
  background: "{colors.bright-snow}"
  surface: "#FFFFFF"
  surface-hover: "#F1F5F9"
  border: "#E2E8F0"
  text-primary: "{colors.deep-space-blue}"
  text-secondary: "#4A5568"
  text-muted: "#718096"
  accent-primary: "{colors.forest-green}"
  accent-hover: "#007A33"
  status-positive: "{colors.forest-green}"
  status-warning: "{colors.tuscan-sun}"
  status-danger: "#E11D48"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.2
  heading:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  data-numeric:
    fontFamily: "JetBrains Mono, Roboto Mono, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "-0.01em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent-primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-danger:
    backgroundColor: "{colors.status-danger}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
---

# Design System: Enseña por Bolivia

## Overview
Sistema de diseño institucional en **Modo Operate**, ajustado a la paleta oficial mejorada de la web pública de Enseña por Bolivia para el control presupuestario y rendición de cuentas financieras.

## Colors

### Paleta Oficial Web Pública (5 Tonos)
1. **Bright Snow (`#F8F9FA` / `hsla(210, 17%, 98%, 1)`)**: Color base de fondo (60%), neutro, limpio y descansado para la lectura prolongada.
2. **Space Indigo (`#2B255C` / `hsla(247, 43%, 25%, 1)`)**: Color primario institucional, usado en navegación lateral, encabezados principales y tarjetas ejecutivas.
3. **Forest Green (`#00923D` / `hsla(145, 100%, 29%, 1)`)**: Color de acción y acento primario (10%), usado en botones interactivos (CTAs), saldos aprobados, ejecución en norma e indicadores de éxito.
4. **Tuscan Sun (`#ECC562` / `hsla(43, 78%, 65%, 1)`)**: Color de advertencia y resalte, usado en alertas de riesgo presupuestario, subtítulos de navegación y acentos dorados institucionales.
5. **Deep Space Blue (`#0D2439` / `hsla(209, 63%, 14%, 1)`)**: Color de contraste profundo y texto principal, usado en tipografía de alto contraste, bordes estructurales y fondos oscuros.

### Variables CSS y SCSS

```scss
/* CSS HEX */
--bright-snow: #f8f9faff;
--space-indigo: #2b255cff;
--forest-green: #00923dff;
--tuscan-sun: #ecc562ff;
--deep-space-blue: #0d2439ff;

/* CSS HSL */
--bright-snow: hsla(210, 17%, 98%, 1);
--space-indigo: hsla(247, 43%, 25%, 1);
--forest-green: hsla(145, 100%, 29%, 1);
--tuscan-sun: hsla(43, 78%, 65%, 1);
--deep-space-blue: hsla(209, 63%, 14%, 1);

/* SCSS HEX */
$bright-snow: #f8f9faff;
$space-indigo: #2b255cff;
$forest-green: #00923dff;
$tuscan-sun: #ecc562ff;
$deep-space-blue: #0d2439ff;
```

## Typography
- **Interfaz y Textos**: `Inter` como tipografía sans-serif neutra para etiquetas, botones y formularios.
- **Cifras Numéricas y Contables**: `JetBrains Mono` con `font-variant-numeric: tabular-nums`. Todas las cifras monetarias (Bs y USD) se alinean estrictamente a la derecha para facilitar la lectura contable vertical.

## Layout
- **Sidebar (Space Indigo / Blanco)**: 260px fijo, sin botón de colapso, encabezado con el logo institucional oficial de `public/logos/logo-ensena-nuevo-01-311.webp` y filtrado dinámico de subrutas según RBAC.
- **Topbar**: 64px de altura, fondo blanco con borde inferior `#E2E8F0`, selector de gestión anual y badge de jurisdicción activa (`[Alcance: Santa Cruz]`).
- **Área Central (Bright Snow)**: Fondo `#F8F9FA` con contenedor espaciado a 24px.

## Elevation & Depth
- Bordes de `1px solid #E2E8F0` con elevaciones sutiles (`0 1px 3px rgba(43, 37, 92, 0.05)`).

## Shapes
- Inputs y Botones: `rounded: 8px` (`md`).
- Badges de estado (Forest Green / Tuscan Sun / Rosewood): `rounded: 9999px` (`full`).
- Tarjetas y Contenedores de Reportes: `rounded: 8px`.

## Components
- **Tablas de Reportes**: Sticky headers, montos alineados a la derecha, zebra striping sutil.
- **Botones de Acción**:
  - Primario: Fondo `Forest Green (#00923D)` con texto blanco.
  - Alerta / Advertencia: Fondo `Tuscan Sun (#ECC562)` con texto oscuro `Deep Space Blue`.
  - Peligro / Reversión: Fondo `#E11D48` con texto blanco.
- **Zona de Ingesta Drag-and-Drop**: Borde discontinuo en `Forest Green` al arrastrar archivos Excel.
