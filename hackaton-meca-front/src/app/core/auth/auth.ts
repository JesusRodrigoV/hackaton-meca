import { Injectable, signal, computed } from '@angular/core';

export type RoleCode = 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR';

export interface UserProfile {
  id: number;
  email: string;
  fullName: string;
  roleName: string;
  roleCode: RoleCode;
  scopeType: 'global' | 'region' | 'financier';
  scopeLabel: string;
  permissions: string[];
}

export const PRESET_USERS: Record<RoleCode, UserProfile> = {
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

const TOKEN_KEY = 'exb.access_token';
const IDENTIFIER_KEY = 'exb.user_identifier';

function decodeJwt(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;

    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      '='
    );
    const json = decodeURIComponent(
      atob(padded)
        .split('')
        .map((char) => `%${`00${char.charCodeAt(0).toString(16)}`.slice(-2)}`)
        .join('')
    );

    return JSON.parse(json) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function roleCodeFor(roleName: string): RoleCode {
  if (/admin|director|super/i.test(roleName)) return 'ADMIN';
  if (/financ|contab|tesor|presupuest/i.test(roleName)) return 'FINANCE';
  if (/coord|área|area|regi|proyecto/i.test(roleName)) return 'COORDINATOR';
  if (/audit|donante|consulta|lectura/i.test(roleName)) return 'AUDITOR';
  return 'AUDITOR';
}

function displayNameFor(identifier: string): string {
  const local = identifier.includes('@')
    ? identifier.split('@')[0]
    : identifier;

  const words = local
    .replace(/[._-]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (!words.length) return '';

  return words
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  readonly currentUser = signal<UserProfile>(
    this.restoreProfile() ?? PRESET_USERS['ADMIN']
  );
  readonly sessionToken = signal<string | null>(this.readToken());
  readonly currentGestion = signal<number>(2026);
  readonly availableGestiones = signal<number[]>([2026, 2025, 2024]);

  readonly isAuthenticated = computed(() => this.sessionToken() !== null);
  readonly userRole = computed(() => this.currentUser()?.roleName ?? '');
  readonly scopeBadge = computed(() => this.currentUser()?.scopeLabel ?? '');

  switchUser(roleKey: RoleCode): void {
    if (PRESET_USERS[roleKey]) {
      this.currentUser.set(PRESET_USERS[roleKey]);
    }
  }

  /**
   * Guarda la sesión real emitida por el backend y adapta el perfil operativo
   * al rol que viene en el JWT. La aplicación conserva sus permisos y alcances
   * de demostración, pero el rol mostrado deja de ser inventado.
   */
  setSession(token: string, identifier: string): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(IDENTIFIER_KEY, identifier);

    const claims = decodeJwt(token);
    const roleName =
      typeof claims?.['role'] === 'string' ? String(claims['role']) : '';
    const roleCode = roleCodeFor(roleName);
    const preset = PRESET_USERS[roleCode];
    const displayName = displayNameFor(identifier);

    this.sessionToken.set(token);
    this.currentUser.set({
      ...preset,
      email: identifier || preset.email,
      fullName: displayName || preset.fullName,
      roleName: roleName || preset.roleName
    });
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(IDENTIFIER_KEY);
    this.sessionToken.set(null);
    this.currentUser.set(PRESET_USERS['ADMIN']);
  }

  setGestion(year: number): void {
    this.currentGestion.set(year);
  }

  hasPermission(permissionCode: string): boolean {
    const user = this.currentUser();
    if (!user) return false;
    if (user.roleCode === 'ADMIN') return true;
    return user.permissions.includes(permissionCode);
  }

  private readToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  private restoreProfile(): UserProfile | null {
    const token = this.readToken();
    if (!token) return null;

    const claims = decodeJwt(token);
    if (!claims) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }

    let identifier = '';
    try {
      identifier = localStorage.getItem(IDENTIFIER_KEY) ?? '';
    } catch {
      identifier = '';
    }

    const roleName =
      typeof claims['role'] === 'string' ? String(claims['role']) : '';
    const roleCode = roleCodeFor(roleName);
    const preset = PRESET_USERS[roleCode];
    const displayName = displayNameFor(identifier);

    return {
      ...preset,
      email: identifier || preset.email,
      fullName: displayName || preset.fullName,
      roleName: roleName || preset.roleName
    };
  }
}
