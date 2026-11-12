import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { API_CONFIG } from '../config/api.config';

export interface UserProfile {
  id: number;
  email: string;
  fullName: string;
  roleName: string;
  roleCode: 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR';
  scopeType: 'global' | 'region' | 'financier';
  scopeLabel: string;
  permissions: string[];
}

export const PRESET_USERS: Record<string, UserProfile> = {
  ADMIN: {
    id: 1,
    email: 'admin@ensenaporbolivia.org',
    fullName: 'Ana Morales (Director General)',
    roleName: 'Administrador General',
    roleCode: 'ADMIN',
    scopeType: 'global',
    scopeLabel: 'Nivel Nacional (Consolidado)',
    permissions: [
      'dashboard.ver', 'reportes.ver', 'reportes.exportar', 'reportes.programar',
      'importaciones.ver', 'importaciones.crear', 'importaciones.confirmar', 'importaciones.revertir',
      'presupuestos.ver', 'presupuestos.editar', 'modificaciones.solicitar', 'modificaciones.aprobar',
      'catalogos.editar', 'gestiones.cerrar', 'usuarios.admin', 'roles.admin', 'auditoria.ver'
    ]
  },
  FINANCE: {
    id: 2,
    email: 'finanzas@ensenaporbolivia.org',
    fullName: 'Carlos Rojas (Técnico Finanzas)',
    roleName: 'Contador / Finanzas',
    roleCode: 'FINANCE',
    scopeType: 'global',
    scopeLabel: 'Operativo Contable Nacional',
    permissions: [
      'dashboard.ver', 'reportes.ver', 'reportes.exportar',
      'importaciones.ver', 'importaciones.crear', 'importaciones.confirmar', 'importaciones.revertir',
      'presupuestos.ver', 'presupuestos.editar', 'modificaciones.solicitar', 'catalogos.editar'
    ]
  },
  COORDINATOR: {
    id: 3,
    email: 'coord.scz@ensenaporbolivia.org',
    fullName: 'Mariana Paz (Coord. Santa Cruz)',
    roleName: 'Coordinador de Área',
    roleCode: 'COORDINATOR',
    scopeType: 'region',
    scopeLabel: 'Región: Santa Cruz (SC)',
    permissions: [
      'dashboard.ver', 'reportes.ver', 'reportes.exportar',
      'presupuestos.ver', 'modificaciones.solicitar'
    ]
  },
  AUDITOR: {
    id: 4,
    email: 'auditor.catalyst@fundacion.org',
    fullName: 'Roberto Silva (Auditor CATALYST)',
    roleName: 'Auditor Externo Donante',
    roleCode: 'AUDITOR',
    scopeType: 'financier',
    scopeLabel: 'Financiador: CATALYST 18',
    permissions: [
      'dashboard.ver', 'reportes.ver', 'reportes.exportar',
      'importaciones.ver', 'presupuestos.ver', 'auditoria.ver'
    ]
  }
};

function getStoredUser(): UserProfile | null {
  if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
    const raw = localStorage.getItem('meca_user');
    if (raw) {
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    }
  }
  return null;
}

function getStoredToken(): string | null {
  if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
    return localStorage.getItem('meca_token');
  }
  return null;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient, { optional: true });

  // Estado reactivo de usuario y autenticación con persistencia en localStorage
  readonly currentUser = signal<UserProfile | null>(getStoredUser());
  readonly token = signal<string | null>(getStoredToken());
  readonly isApiAuthenticated = signal<boolean>(false);
  readonly isTotpEnabled = signal<boolean>(false);

  // Gestión fiscal activa y gestiones disponibles (sincronizadas desde el catálogo real de la BD)
  readonly currentGestion = signal<number>(2026);
  readonly availableGestiones = signal<number[]>([2026]);

  // Propiedades calculadas (Computed Signals)
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly userRole = computed(() => this.currentUser()?.roleName ?? 'Invitado');
  readonly scopeBadge = computed(() => this.currentUser()?.scopeLabel ?? 'Sin alcance');

  constructor() {
    if (this.token()) {
      this.cargarGestiones();
    }
  }

  /**
   * Conmuta el perfil activo entre los roles prestablecidos (ideal para pruebas y auditoría).
   */
  switchUser(roleKey: 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR'): void {
    if (PRESET_USERS[roleKey]) {
      const user = PRESET_USERS[roleKey];
      const token = `jwt-token-${roleKey.toLowerCase()}-exb`;
      this.currentUser.set(user);
      this.token.set(token);
      this.isApiAuthenticated.set(false);
      this.persistSession(user, token);
    }
  }

  /**
   * Autentica con el backend FastAPI o mediante preset institucional.
   */
  async login(email: string, password: string): Promise<{ success: boolean; requires2Fa?: boolean; sessionToken?: string; error?: string }> {
    if (this.http) {
      try {
        const resp = await firstValueFrom(
          this.http.post<any>(
            API_CONFIG.endpoints.auth.login,
            { email, password }
          )
        );

        if (resp?.session_token) {
          // Requiere segundo factor de autenticación (2FA)
          return { success: false, requires2Fa: true, sessionToken: resp.session_token };
        }

        if (resp?.access_token) {
          const ok = await this.establishSession(resp.access_token);
          return { success: ok };
        }
      } catch (err: any) {
        if (err?.status === 401) {
          return { success: false, error: 'Credenciales incorrectas' };
        }
      }
    }

    const foundUser = Object.values(PRESET_USERS).find(u => u.email.toLowerCase() === email.toLowerCase());
    if (foundUser) {
      const token = `jwt-token-${foundUser.roleCode.toLowerCase()}-exb`;
      this.currentUser.set(foundUser);
      this.token.set(token);
      this.persistSession(foundUser, token);
      return { success: true };
    }

    return { success: false, error: 'Credenciales inválidas' };
  }

  /**
   * Valida el código TOTP de 6 dígitos tras el paso 1 de login
   */
  async verifyLogin2Fa(sessionToken: string, code: string): Promise<boolean> {
    if (!this.http) return false;
    try {
      const resp = await firstValueFrom(
        this.http.post<any>(API_CONFIG.endpoints.auth.twoFactorVerifyLogin, {
          session_token: sessionToken,
          code: code.trim()
        })
      );
      if (resp?.access_token) {
        return await this.establishSession(resp.access_token);
      }
      return false;
    } catch {
      return false;
    }
  }

  private async establishSession(accessToken: string): Promise<boolean> {
    this.token.set(accessToken);
    this.isApiAuthenticated.set(true);

    try {
      const profile = await firstValueFrom(
        this.http!.get<{
          id: number;
          email: string;
          full_name?: string;
          first_name?: string;
          last_name?: string;
          roles?: Array<{ name: string; code: string }>;
          permissions?: string[];
        }>(API_CONFIG.endpoints.auth.me, {
          headers: { Authorization: `Bearer ${accessToken}` }
        })
      );

      if (profile) {
        const rawRoleName = profile.roles?.[0]?.name ?? 'Administrador General';
        let roleCode: 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR' = 'ADMIN';
        let scopeType: 'global' | 'region' | 'financier' = 'global';
        let scopeLabel = 'Nivel Nacional (Consolidado)';

        if (rawRoleName.toLowerCase().includes('finanz')) {
          roleCode = 'FINANCE';
          scopeLabel = 'Operativo Contable Nacional';
        } else if (rawRoleName.toLowerCase().includes('coord') || profile.email.includes('scz') || profile.email.includes('santacruz')) {
          roleCode = 'COORDINATOR';
          scopeType = 'region';
          scopeLabel = 'Región: Santa Cruz (SC)';
        } else if (rawRoleName.toLowerCase().includes('audit') || profile.email.includes('catalyst')) {
          roleCode = 'AUDITOR';
          scopeType = 'financier';
          scopeLabel = 'Financiador: CATALYST 18';
        }

        const fullName = profile.full_name || `${profile.first_name ?? ''} ${profile.last_name ?? ''}`.trim() || profile.email;

        const user: UserProfile = {
          id: profile.id,
          email: profile.email,
          fullName,
          roleName: rawRoleName,
          roleCode,
          scopeType,
          scopeLabel,
          permissions: profile.permissions && profile.permissions.length > 0
            ? profile.permissions
            : (PRESET_USERS[roleCode]?.permissions ?? PRESET_USERS['ADMIN'].permissions)
        };
        this.currentUser.set(user);
        this.persistSession(user, accessToken);
        // Comprobar estado 2FA y cargar gestiones reales del sistema
        this.check2FaStatus();
        this.cargarGestiones();
        return true;
      }
    } catch {
      // Perfil no disponible
    }
    return true;
  }

  // ==========================================================================
  // GESTIÓN DE AUTENTICACIÓN EN DOS PASOS (2FA)
  // ==========================================================================

  async check2FaStatus(): Promise<boolean> {
    if (!this.http) return false;
    try {
      const resp = await firstValueFrom(
        this.http.get<{ is_enabled: boolean; enabled_at: string | null }>(
          API_CONFIG.endpoints.auth.twoFactorStatus
        )
      );
      this.isTotpEnabled.set(resp.is_enabled);
      return resp.is_enabled;
    } catch {
      return false;
    }
  }

  async setup2Fa(): Promise<{ secret: string; otpauth_uri: string } | null> {
    if (!this.http) return null;
    try {
      return await firstValueFrom(
        this.http.post<{ secret: string; otpauth_uri: string }>(
          API_CONFIG.endpoints.auth.twoFactorSetup,
          {}
        )
      );
    } catch {
      return null;
    }
  }

  async enable2Fa(code: string): Promise<{ success: boolean; backupCodes?: string[]; error?: string }> {
    if (!this.http) return { success: false, error: 'No conectado' };
    try {
      const resp = await firstValueFrom(
        this.http.post<{ backup_codes?: string[] }>(
          API_CONFIG.endpoints.auth.twoFactorEnable,
          { totp_code: code.trim() }
        )
      );
      this.isTotpEnabled.set(true);
      return { success: true, backupCodes: resp.backup_codes || [] };
    } catch (err: any) {
      const detail = err?.error?.detail || 'Código de verificación incorrecto o expirado';
      return { success: false, error: detail };
    }
  }

  async disable2Fa(password: string, code: string): Promise<{ success: boolean; error?: string }> {
    if (!this.http) return { success: false, error: 'No conectado' };
    try {
      await firstValueFrom(
        this.http.post<{ message: string }>(
          API_CONFIG.endpoints.auth.twoFactorDisable,
          { password, totp_code: code.trim() }
        )
      );
      this.isTotpEnabled.set(false);
      return { success: true };
    } catch (err: any) {
      const detail = err?.error?.detail || 'Contraseña o código 2FA inválidos';
      return { success: false, error: detail };
    }
  }

  /**
   * Cierra la sesión activa en el frontend y en el backend si está conectado.
   */
  async logout(): Promise<void> {
    const curToken = this.token();
    if (this.http && curToken && this.isApiAuthenticated()) {
      try {
        await firstValueFrom(
          this.http.post(API_CONFIG.endpoints.auth.logout, {}, {
            headers: { Authorization: `Bearer ${curToken}` }
          })
        );
      } catch {
        // Fallo silenciado en desconexión
      }
    }
    this.currentUser.set(null);
    this.token.set(null);
    this.isApiAuthenticated.set(false);
    this.clearSession();
  }

  private persistSession(user: UserProfile, token: string): void {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('meca_user', JSON.stringify(user));
        localStorage.setItem('meca_token', token);
      } catch {
        // Ignorar si el almacenamiento local está restringido
      }
    }
  }

  private clearSession(): void {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      try {
        localStorage.removeItem('meca_user');
        localStorage.removeItem('meca_token');
      } catch {
        // Ignorar
      }
    }
  }

  /**
   * Carga las gestiones fiscales reales desde la base de datos a través de catálogos.
   */
  async cargarGestiones(): Promise<void> {
    if (!this.http) return;
    try {
      const resp = await firstValueFrom(
        this.http.get<Array<{ id: number; year: number; is_closed: boolean; description?: string }>>(
          API_CONFIG.endpoints.catalogos.gestiones
        )
      );
      if (resp && resp.length > 0) {
        const years = resp.map(g => Number(g.year)).filter(y => !isNaN(y) && y > 0).sort((a, b) => b - a);
        if (years.length > 0) {
          this.availableGestiones.set(years);
          if (!years.includes(this.currentGestion())) {
            this.currentGestion.set(years[0]);
          }
        }
      }
    } catch {
      // Si la API no está disponible, se conserva la gestión 2026 configurada por defecto
    }
  }

  /**
   * Cambia la gestión fiscal activa del sistema.
   */
  setGestion(year: number | string): void {
    const parsed = Number(year);
    if (!isNaN(parsed) && parsed > 0) {
      this.currentGestion.set(parsed);
    }
  }

  /**
   * Verifica si el usuario actual posee un permiso específico (o pase de administrador).
   */
  hasPermission(permissionCode: string): boolean {
    const user = this.currentUser();
    if (!user) return false;
    if (user.roleCode === 'ADMIN') return true;
    return user.permissions.includes(permissionCode);
  }
}
