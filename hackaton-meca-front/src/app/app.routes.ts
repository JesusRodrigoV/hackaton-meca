import { Routes } from '@angular/router';
import { Shell } from './layout/shell/shell';
import { publicCssResolver } from './public/public-css';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    resolve: { publicCss: publicCssResolver },
    loadComponent: () => import('./public/landing/landing').then(m => m.Landing)
  },
  {
    path: 'login',
    resolve: { publicCss: publicCssResolver },
    loadComponent: () => import('./features/auth/login/login').then(m => m.Login)
  },
  {
    path: '',
    component: Shell,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard').then(m => m.Dashboard)
      },
      {
        path: 'presupuestos/techos',
        loadComponent: () => import('./features/budgets/techos/techos').then(m => m.Techos)
      },
      {
        path: 'presupuestos/modificaciones',
        loadComponent: () => import('./features/budgets/modificaciones/modificaciones').then(m => m.Modificaciones)
      },
      {
        path: 'ejecucion/movimientos',
        loadComponent: () => import('./features/execution/movimientos/movimientos').then(m => m.Movimientos)
      },
      {
        path: 'ejecucion/importador',
        loadComponent: () => import('./features/execution/importador/importador').then(m => m.Importador)
      },
      {
        path: 'reportes',
        loadComponent: () => import('./features/reports/reports/reports').then(m => m.Reports)
      },
      {
        path: 'seguridad/usuarios',
        loadComponent: () => import('./features/security/users/users').then(m => m.Users)
      },
      {
        path: 'seguridad/roles',
        loadComponent: () => import('./features/security/roles/roles').then(m => m.Roles)
      },
      {
        path: 'seguridad/auditoria',
        loadComponent: () => import('./features/security/audit/audit').then(m => m.Audit)
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
