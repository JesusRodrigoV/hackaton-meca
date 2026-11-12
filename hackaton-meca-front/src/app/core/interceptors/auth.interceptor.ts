import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../auth/auth';

/**
 * Interceptor HTTP para peticiones al backend FastAPI:
 * 1. Adjunta automáticamente el token Bearer JWT si existe.
 * 2. Inyecta la cabecera de gestión fiscal actual ('X-Gestion').
 * 3. Inyecta el rol y alcance activo para facilitar el filtrado contextual ('X-Scope-Type', 'X-Role-Code').
 * 4. Captura errores 401 (sesión expirada) y 403 (permiso denegado) redirigiendo a las vistas correspondientes.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const currentUser = authService.currentUser();
  const currentGestion = authService.currentGestion();
  const token = authService.token();

  let headersConfig: Record<string, string> = {
    'X-Gestion': currentGestion.toString()
  };

  if (token) {
    headersConfig['Authorization'] = `Bearer ${token}`;
  }

  if (currentUser) {
    headersConfig['X-Role-Code'] = currentUser.roleCode;
    headersConfig['X-Scope-Type'] = currentUser.scopeType;
  }

  const clonedReq = req.clone({
    setHeaders: headersConfig
  });

  return next(clonedReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        authService.logout();
        router.navigate(['/login'], {
          queryParams: { sessionExpired: 'true' }
        });
      } else if (error.status === 403) {
        router.navigate(['/prohibido']);
      }
      return throwError(() => error);
    })
  );
};
