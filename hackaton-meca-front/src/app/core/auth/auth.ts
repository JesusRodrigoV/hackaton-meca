import { Injectable, signal, computed } from '@angular/core';

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

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Estado reactivo de usuario y autenticación
  readonly currentUser = signal<UserProfile | null>(PRESET_USERS['ADMIN']);
  readonly token = signal<string | null>('jwt-demo-token-exb-2026');

  // Gestión fiscal activa y gestiones disponibles
  readonly currentGestion = signal<number>(2026);
  readonly availableGestiones = signal<number[]>([2026, 2025, 2024]);

  // Propiedades calculadas (Computed Signals)
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly userRole = computed(() => this.currentUser()?.roleName ?? '');
  readonly scopeBadge = computed(() => this.currentUser()?.scopeLabel ?? '');

  /**
   * Conmuta el perfil activo entre los roles prestablecidos (ideal para pruebas y auditoría).
   */
  switchUser(roleKey: 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR'): void {
    if (PRESET_USERS[roleKey]) {
      this.currentUser.set(PRESET_USERS[roleKey]);
      this.token.set(`jwt-token-${roleKey.toLowerCase()}-exb`);
    }
  }

  /**
   * Simula o realiza el login con credenciales.
   */
  login(email: string, _password: string): boolean {
    const foundUser = Object.values(PRESET_USERS).find(u => u.email.toLowerCase() === email.toLowerCase());
    if (foundUser) {
      this.currentUser.set(foundUser);
      this.token.set(`jwt-token-${foundUser.roleCode.toLowerCase()}-exb`);
      return true;
    }
    // Usuario por defecto si no coincide exactamente
    this.currentUser.set(PRESET_USERS['ADMIN']);
    this.token.set('jwt-demo-token-exb-2026');
    return true;
  }

  /**
   * Cierra la sesión activa.
   */
  logout(): void {
    this.currentUser.set(null);
    this.token.set(null);
  }

  /**
   * Cambia la gestión fiscal activa del sistema.
   */
  setGestion(year: number): void {
    this.currentGestion.set(year);
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
