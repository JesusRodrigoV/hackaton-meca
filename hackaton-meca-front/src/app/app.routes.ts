import { Routes } from '@angular/router';
import { Shell } from './layout/shell/shell';
import { authGuard, guestGuard, permissionGuard } from './core/guards/auth.guard';
import { publicCssResolver } from './public/public-css';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    resolve: { publicCss: publicCssResolver },
    loadComponent: () => import('./public/landing/landing').then(m => m.Landing)
  },
  {
    path: 'landing',
    resolve: { publicCss: publicCssResolver },
    loadComponent: () => import('./public/landing/landing').then(m => m.Landing)
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login/login').then(m => m.Login)
  },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
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
        canActivate: [permissionGuard],
        data: { permissions: ['importaciones.ver'] },
        loadComponent: () => import('./features/execution/importador/importador').then(m => m.Importador)
      },
      {
        path: 'reportes',
        loadComponent: () => import('./features/reports/reports/reports').then(m => m.Reports)
      },
      {
        path: 'seguridad/usuarios',
        canActivate: [permissionGuard],
        data: { permissions: ['usuarios.admin'] },
        loadComponent: () => import('./features/security/users/users').then(m => m.Users)
      },
      {
        path: 'seguridad/roles',
        canActivate: [permissionGuard],
        data: { permissions: ['roles.admin'] },
        loadComponent: () => import('./features/security/roles/roles').then(m => m.Roles)
      },
      {
        path: 'seguridad/auditoria',
        canActivate: [permissionGuard],
        data: { permissions: ['auditoria.ver'] },
        loadComponent: () => import('./features/security/audit/audit').then(m => m.Audit)
      },
      {
        path: 'prohibido',
        loadComponent: () => import('./features/errors/forbidden/forbidden').then(m => m.Forbidden)
      },
      {
        path: '403',
        redirectTo: 'prohibido'
      },
      {
        path: '404',
        loadComponent: () => import('./features/errors/not-found/not-found').then(m => m.NotFound)
      }
    ]
  },
  {
    path: '**',
    redirectTo: '404'
  }
];
