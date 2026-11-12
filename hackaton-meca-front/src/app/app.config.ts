import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeng/themes/aura';
import { definePreset } from '@primeng/themes';
import { routes } from './app.routes';

const EnsenaPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#ecfdf3',
      100: '#d1fae1',
      200: '#a7f3c7',
      300: '#6ee7a4',
      400: '#34d380',
      500: '#00923d',
      600: '#007c33',
      700: '#006229',
      800: '#004f21',
      900: '#00411c',
      950: '#00240d'
    },
    colorScheme: {
      light: {
        surface: {
          0: '#ffffff',
          50: '#f8f9fa',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617'
        }
      }
    }
  }
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding()),
    providePrimeNG({
      theme: {
        preset: EnsenaPreset,
        options: {
          darkModeSelector: false,
          cssLayer: false
        }
      },
    }),
  ],
};
