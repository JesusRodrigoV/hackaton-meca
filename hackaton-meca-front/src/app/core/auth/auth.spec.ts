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

  it('should authenticate default admin user', () => {
    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentUser()?.roleCode).toBe('ADMIN');
  });

  it('should verify permissions correctly', () => {
    expect(service.hasPermission('usuarios.admin')).toBe(true);
  });
});
