---
name: Enseña por Bolivia - Financial Design System
description: Institutional budgeting, financial execution, and audit governance design system
mode: operate
colors:
  bright-snow: "#F8F9FA"
  space-indigo: "#1B2A49"
  mint-leaf: "#10B981"
  rosewood: "#B24C63"
  cerulean: "#0081AF"
  background: "{colors.bright-snow}"
  surface: "#FFFFFF"
  surface-hover: "#F1F5F9"
  border: "#E2E8F0"
  text-primary: "{colors.space-indigo}"
  text-secondary: "#4A5568"
  text-muted: "#718096"
  accent-primary: "{colors.cerulean}"
  accent-hover: "#00688D"
  status-positive: "{colors.mint-leaf}"
  status-warning: "#F59E0B"
  status-danger: "{colors.rosewood}"
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
Sistema de diseño institucional en **Modo Operate**, ajustado a la paleta oficial de 5 tonos para el control presupuestario y rendición de cuentas financieras.

## Colors

### Paleta Oficial de 5 Tonos
1. **Bright Snow (`#F8F9FA`)**: Color base de fondo (60%), neutro, limpio y descansado para la vista.
2. **Space Indigo (`#1B2A49`)**: Color estructural y de texto primario (30%), usado en navegación lateral, encabezados y cifras principales.
3. **Cerulean (`#0081AF`)**: Color de acción y acento primario (10%), usado en botones interactivos (CTAs), enlaces activos, pestañas seleccionadas y series de gráficos.
4. **Mint Leaf (`#10B981`)**: Color semafórico de saldo positivo, ejecución aprobada, carga exitosa de lotes e insignias de estado activo.
5. **Rosewood (`#B24C63`)**: Color semafórico de sobregiro presupuestario, advertencias críticas, eliminación o reversión de lotes y partidas en déficit.

## Typography
- **Interfaz y Textos**: `Inter` como tipografía sans-serif neutra para etiquetas, botones y formularios.
- **Cifras Numéricas y Contables**: `JetBrains Mono` con `font-variant-numeric: tabular-nums`. Todas las cifras monetarias (Bs y USD) se alinean estrictamente a la derecha para facilitar la lectura contable vertical.

## Layout
- **Sidebar (Space Indigo / Blanco)**: 260px colapsable a 72px con filtrado dinámico de subrutas según RBAC.
- **Topbar**: 64px de altura, fondo blanco con borde inferior `#E2E8F0`, selector de gestión anual y badge de jurisdicción activa (`[Alcance: Santa Cruz]`).
- **Área Central (Bright Snow)**: Fondo `#F8F9FA` con contenedor espaciado a 24px.

## Elevation & Depth
- Bordes de `1px solid #E2E8F0` con elevaciones sutiles (`0 1px 3px rgba(27, 42, 73, 0.05)`).

## Shapes
- Inputs y Botones: `rounded: 8px` (`md`).
- Badges de estado (Mint Leaf / Rosewood): `rounded: 9999px` (`full`).
- Tarjetas y Contenedores de Reportes: `rounded: 8px`.

## Components
- **Tablas de Reportes**: Sticky headers, montos alineados a la derecha, zebra striping sutil.
- **Botones de Acción**:
  - Primario: Fondo `Cerulean (#0081AF)` con texto blanco.
  - Peligro / Reversión: Fondo `Rosewood (#B24C63)` con texto blanco.
  - Éxito / Confirmación: Fondo `Mint Leaf (#10B981)` con texto blanco.
- **Zona de Ingesta Drag-and-Drop**: Borde discontinuo en `Cerulean` al arrastrar archivos Excel.

## Do's and Don'ts
- **DO**: Usar `Cerulean` para acciones interactivas y reservar `Mint Leaf` y `Rosewood` estrictamente para estados financieros y de sistema.
- **DO**: Mantener `Space Indigo` como color dominante de texto sobre fondos `Bright Snow` o blancos.
- **DON'T**: Reemplazar `Rosewood` con rojos fluorescentes ni usar degradados que degraden la sobriedad institucional.
