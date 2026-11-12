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
  surface-hover: "#F8FAFC"
  border: "#E2E8F0"
  border-subtle: "#EDF2F7"
  text-primary: "{colors.deep-space-blue}"
  text-secondary: "#475569"
  text-muted: "#64748B"
  accent-primary: "{colors.forest-green}"
  accent-hover: "#007A33"
  accent-subtle: "rgba(0, 146, 61, 0.08)"
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
    fontFamily: "'JetBrains Mono', 'SF Mono', 'Roboto Mono', monospace"
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
shadows:
  xs: "0 1px 2px rgba(13, 36, 57, 0.04)"
  sm: "0 1px 3px rgba(13, 36, 57, 0.06), 0 1px 2px rgba(13, 36, 57, 0.04)"
  md: "0 4px 6px -1px rgba(13, 36, 57, 0.08), 0 2px 4px -2px rgba(13, 36, 57, 0.04)"
  lg: "0 10px 15px -3px rgba(13, 36, 57, 0.08), 0 4px 6px -4px rgba(13, 36, 57, 0.03)"
  card: "0 1px 3px rgba(13, 36, 57, 0.05), 0 1px 2px -1px rgba(13, 36, 57, 0.05)"
  card-hover: "0 8px 16px -2px rgba(13, 36, 57, 0.08), 0 4px 6px -2px rgba(13, 36, 57, 0.04)"
components:
  button-primary:
    backgroundColor: "{colors.accent-primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    hoverBackgroundColor: "{colors.accent-hover}"
  button-brand:
    backgroundColor: "{colors.space-indigo}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    borderColor: "{colors.border}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-danger:
    backgroundColor: "{colors.status-danger}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
---

# Design System: Enseña por Bolivia

## Overview
Sistema de diseño institucional en **Modo Operate**, ajustado a la paleta oficial mejorada de la web pública de Enseña por Bolivia para el control presupuestario y rendición de cuentas financieras.

## Colors

### Paleta Oficial Web Pública (5 Tonos Canónicos)
1. **Bright Snow (`#F8F9FA` / `hsla(210, 17%, 98%, 1)`)**: Color base de fondo (60%), neutro, limpio y descansado para la lectura prolongada.
2. **Space Indigo (`#2B255C` / `hsla(247, 43%, 25%, 1)`)**: Color primario institucional, usado en barra lateral de navegación, encabezados principales y tarjetas ejecutivas.
3. **Forest Green (`#00923D` / `hsla(145, 100%, 29%, 1)`)**: Color de acción y acento primario (10%), usado en botones interactivos (CTAs), saldos aprobados, ejecución en norma e indicadores de éxito.
4. **Tuscan Sun (`#ECC562` / `hsla(43, 78%, 65%, 1)`)**: Color de advertencia y resalte, usado en alertas de riesgo presupuestario, subtítulos de navegación y acentos dorados institucionales. En texto sobre fondos claros se utiliza `#855F05` para contraste WCAG AAA.
5. **Deep Space Blue (`#0D2439` / `hsla(209, 63%, 14%, 1)`)**: Color de contraste profundo y texto principal, usado en tipografía de alto contraste, bordes estructurales y fondos oscuros.

### Variables CSS y SCSS Oficiales

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

## Layout & Components
- **Sidebar**: Ancho estándar de 260px con modo compacto a 76px. Conmutador interactivo mediante el logotipo institucional (`logo-ensena-nuevo-01-311.webp` expandido / `logo-ensena-nuevo-01-148.webp` compacto). Gradiente institucional de `#2B255C` a `#1F1A43`.
- **Topbar**: 64px de altura, fondo blanco con borde inferior `#E2E8F0`, selector de gestión anual estilizado y badge de jurisdicción activa (`[Alcance: Santa Cruz]`).
- **Área Central (Bright Snow)**: Fondo `#F8F9FA` con contenedor espaciado a 24px.
- **Tarjetas y Contenedores**: Bordes de `1px solid #E2E8F0`, radio de 12px, sombras difusas tintadas `rgba(13, 36, 57, 0.05)`.
