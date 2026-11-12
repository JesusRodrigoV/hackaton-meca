import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth';

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start unauthenticated when no stored session exists', () => {
    service.logout();
    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentUser()).toBeNull();
  });

  it('should authenticate admin user when switching user or logging in', () => {
    service.switchUser('ADMIN');
    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentUser()?.roleCode).toBe('ADMIN');
  });

  it('should verify permissions correctly', () => {
    service.switchUser('ADMIN');
    expect(service.hasPermission('usuarios.admin')).toBe(true);
  });
});
