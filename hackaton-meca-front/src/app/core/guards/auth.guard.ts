import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth';

/**
 * Guard de autenticación: verifica si el usuario tiene una sesión activa.
 * Redirige al login preservando la URL original en caso contrario.
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });
};

/**
 * Guard de invitados: impide que usuarios ya autenticados accedan a la vista de login.
 * Redirige automáticamente al dashboard principal.
 */
export const guestGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};

/**
 * Guard de permisos RBAC y roles: valida que el usuario activo cuente con
 * los permisos granulares o roles requeridos en la metadata de la ruta.
 * Redirige a la pantalla de Acceso Denegado (403) si no cumple las condiciones.
 */
export const permissionGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url }
    });
  }

  const currentUser = authService.currentUser();
  if (!currentUser) {
    return router.createUrlTree(['/login']);
  }

  // Los administradores generales cuentan con pase irrestricto
  if (currentUser.roleCode === 'ADMIN') {
    return true;
  }

  const requiredRoles = route.data?.['roles'] as string[] | undefined;
  const requiredPermissions = route.data?.['permissions'] as string[] | undefined;

  // Validación por rol requerido
  if (requiredRoles && requiredRoles.length > 0) {
    if (requiredRoles.includes(currentUser.roleCode)) {
      return true;
    }
  }

  // Validación por permiso atómico requerido
  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasRequired = requiredPermissions.every(perm => authService.hasPermission(perm));
    if (hasRequired) {
      return true;
    }
  }

  // Si no se especificaron restricciones, se concede acceso
  if (!requiredRoles && !requiredPermissions) {
    return true;
  }

  return router.createUrlTree(['/prohibido']);
};
