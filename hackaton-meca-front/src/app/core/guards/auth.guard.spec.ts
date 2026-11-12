import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { authGuard, guestGuard, permissionGuard } from './auth.guard';
import { AuthService } from '../auth/auth';

describe('Auth Guards', () => {
  let authService: AuthService;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    authService = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
  });

  it('authGuard should redirect to login when user is unauthenticated', () => {
    authService.logout();
    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/dashboard' } as RouterStateSnapshot;
    const result = TestBed.runInInjectionContext(() => authGuard(route, state));
    expect(result).not.toBe(true);
  });

  it('authGuard should allow access when user is authenticated', () => {
    authService.switchUser('ADMIN');
    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/dashboard' } as RouterStateSnapshot;
    const result = TestBed.runInInjectionContext(() => authGuard(route, state));
    expect(result).toBe(true);
  });

  it('guestGuard should redirect to dashboard if already authenticated', () => {
    authService.switchUser('ADMIN');
    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/login' } as RouterStateSnapshot;
    const result = TestBed.runInInjectionContext(() => guestGuard(route, state));
    expect(result).not.toBe(true);
  });

  it('permissionGuard should allow access for ADMIN role without restrictions', () => {
    authService.switchUser('ADMIN');
    const route = {
      data: { permissions: ['usuarios.admin'] }
    } as unknown as ActivatedRouteSnapshot;
    const state = { url: '/seguridad/usuarios' } as RouterStateSnapshot;
    const result = TestBed.runInInjectionContext(() => permissionGuard(route, state));
    expect(result).toBe(true);
  });
});
