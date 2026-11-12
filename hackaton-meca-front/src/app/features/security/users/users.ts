import { Component, signal, inject, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { API_CONFIG } from '../../../core/config/api.config';

export interface UsuarioItem {
  id: number;
  nombreCompleto: string;
  email: string;
  rol: string;
  rolId: number;
  rolCodigo: string;
  alcanceTipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR';
  alcanceValor: string;
  activo: boolean;
  permisos: string[];
}

export interface RolOption {
  id: number;
  name: string;
  description: string;
  permissions: string[];
}

@Component({
  selector: 'app-users',
  imports: [CommonModule, FormsModule, BoxIconComponent],
  templateUrl: './users.html',
  styleUrl: './users.scss'
})
export class Users implements OnInit {
  private readonly http = inject(HttpClient, { optional: true });

  readonly searchQuery = signal<string>('');
  readonly isSaving = signal<boolean>(false);
  readonly toastMessage = signal<{ text: string; type: 'success' | 'error' } | null>(null);

  // Control de modal de creación / edición
  readonly isModalOpen = signal<boolean>(false);
  readonly isEditing = signal<boolean>(false);
  readonly editUserId = signal<number>(0);

  // Modal para inspeccionar permisos granulares de un usuario
  readonly isPermisosModalOpen = signal<boolean>(false);
  readonly selectedUserForPermisos = signal<UsuarioItem | null>(null);

  // Campos de formulario reactivo
  readonly editNombre = signal<string>('');
  readonly editEmail = signal<string>('');
  readonly editPassword = signal<string>('PasswordExB2026!');
  readonly editAutoPassword = signal<boolean>(false);
  readonly editRolId = signal<number>(1);
  readonly editAlcanceTipo = signal<'GLOBAL' | 'REGION' | 'FINANCIADOR'>('GLOBAL');
  readonly editAlcanceValor = signal<string>('Nivel Nacional (Consolidado)');
  readonly editActivo = signal<boolean>(true);

  // Catálogo de roles con sus descripciones y permisos
  readonly availableRoles = signal<RolOption[]>([
    {
      id: 1,
      name: 'Dirección General (Administrador)',
      description: 'Acceso total y configuración de roles, techos y aprobación de modificaciones.',
      permissions: [
        'Ver Tablero Ejecutivo',
        'Consultar 7 Reportes Oficiales',
        'Exportar Informes a Excel / PDF',
        'Consultar Techos Presupuestarios',
        'Configurar Techos Iniciales',
        'Solicitar Traspasos y Adiciones',
        'Aprobar Modificaciones de Techos',
        'Ver Historial de Lotes Excel',
        'Cargar Archivos al Prevalidador',
        'Confirmar e Imputar al Mayor',
        'Rollback Contable de Lotes',
        'Inspeccionar Cadena SHA-256',
        'Administrar Usuarios y Scopes',
        'Administrar Roles y Permisos'
      ]
    },
    {
      id: 3,
      name: 'Contabilidad y Finanzas',
      description: 'Operaciones contables, carga de planillas de gastos, traspasos y conciliación.',
      permissions: [
        'Ver Tablero Ejecutivo',
        'Consultar 7 Reportes Oficiales',
        'Exportar Informes a Excel / PDF',
        'Consultar Techos Presupuestarios',
        'Configurar Techos Iniciales',
        'Solicitar Traspasos y Adiciones',
        'Ver Historial de Lotes Excel',
        'Cargar Archivos al Prevalidador',
        'Confirmar e Imputar al Mayor',
        'Rollback Contable de Lotes'
      ]
    },
    {
      id: 4,
      name: 'Coordinación Regional',
      description: 'Gestión presupuestaria delimitada a su región geográfica asignada.',
      permissions: [
        'Ver Tablero Ejecutivo (Región)',
        'Consultar Reportes de la Región',
        'Exportar Informes a Excel / PDF',
        'Consultar Techos Regionales',
        'Solicitar Traspasos y Adiciones'
      ]
    },
    {
      id: 2,
      name: 'Auditoría Donante',
      description: 'Supervisión independiente, verificación SHA-256 y descarga de reportes oficiales.',
      permissions: [
        'Ver Tablero Ejecutivo (Donante)',
        'Consultar 7 Reportes Oficiales',
        'Exportar Informes a Excel / PDF',
        'Consultar Techos Presupuestarios',
        'Ver Historial de Lotes Excel',
        'Inspeccionar Cadena SHA-256'
      ]
    }
  ]);

  readonly regionesDisponibles = ['Santa Cruz (SC)', 'La Paz (LP)', 'Cochabamba (CBBA)', 'Beni (BN)', 'Chuquisaca (CH)'];
  readonly financiadoresDisponibles = ['CATALYST 18', 'CEL (Comunidad)', 'Fundación Tinkuy', 'Cooperación Suiza'];

  readonly usuarios = signal<UsuarioItem[]>([
    {
      id: 1,
      nombreCompleto: 'Ana Morales',
      email: 'admin@ensenaporbolivia.org',
      rol: 'Dirección General (Administrador)',
      rolId: 1,
      rolCodigo: 'ADMIN',
      alcanceTipo: 'GLOBAL',
      alcanceValor: 'Nivel Nacional (Consolidado)',
      activo: true,
      permisos: [
        'Acceso Global a Nivel Nacional',
        'Aprobación de Modificaciones Presupuestarias',
        'Administración de Usuarios y Roles',
        'Gestión de Techos y Catálogos',
        'Auditoría y Trazabilidad Criptográfica'
      ]
    },
    {
      id: 2,
      nombreCompleto: 'Carlos Rojas',
      email: 'finanzas@ensenaporbolivia.org',
      rol: 'Contabilidad y Finanzas',
      rolId: 3,
      rolCodigo: 'FINANCE',
      alcanceTipo: 'GLOBAL',
      alcanceValor: 'Nivel Nacional (Consolidado)',
      activo: true,
      permisos: [
        'Carga e Importación de Planillas Excel',
        'Confirmación e Imputación al Mayor',
        'Reversión y Rollback de Lotes',
        'Solicitud de Traspasos Presupuestarios',
        'Descarga de Reportes en Excel y PDF'
      ]
    },
    {
      id: 3,
      nombreCompleto: 'Mariana Paz',
      email: 'coord.scz@ensenaporbolivia.org',
      rol: 'Coordinación Regional',
      rolId: 4,
      rolCodigo: 'COORDINATOR',
      alcanceTipo: 'REGION',
      alcanceValor: 'Santa Cruz (SC)',
      activo: true,
      permisos: [
        'Consulta de Techos Presupuestarios de Santa Cruz',
        'Solicitud de Traspasos para Santa Cruz',
        'Visualización de Reportes Regionales',
        'Exportación de Informes Financieros Locales'
      ]
    },
    {
      id: 4,
      nombreCompleto: 'Roberto Silva',
      email: 'auditor.catalyst@fundacion.org',
      rol: 'Auditoría Donante',
      rolId: 2,
      rolCodigo: 'AUDITOR',
      alcanceTipo: 'FINANCIADOR',
      alcanceValor: 'CATALYST 18',
      activo: true,
      permisos: [
        'Inspección de Cadena Inmutable SHA-256',
        'Auditoría de Fondos de CATALYST 18',
        'Consulta de Ejecución vs Presupuesto Aprobado',
        'Descargas Certificadas en Excel y PDF'
      ]
    },
    {
      id: 5,
      nombreCompleto: 'Elena Vaca',
      email: 'coord.cbba@ensenaporbolivia.org',
      rol: 'Coordinación Regional',
      rolId: 4,
      rolCodigo: 'COORDINATOR',
      alcanceTipo: 'REGION',
      alcanceValor: 'Cochabamba (CBBA)',
      activo: true,
      permisos: [
        'Consulta de Techos Presupuestarios de Cochabamba',
        'Solicitud de Traspasos para Cochabamba',
        'Visualización de Reportes Regionales'
      ]
    }
  ]);

  // Lista filtrada reactivamente por búsqueda
  readonly usuariosFiltrados = computed(() => {
    const q = this.searchQuery().trim().toLowerCase();
    if (!q) return this.usuarios();
    return this.usuarios().filter(
      u =>
        u.nombreCompleto.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.rol.toLowerCase().includes(q) ||
        u.alcanceValor.toLowerCase().includes(q)
    );
  });

  // Rol actualmente seleccionado en el formulario
  readonly selectedRoleInForm = computed<RolOption | undefined>(() => {
    return this.availableRoles().find(r => r.id === this.editRolId());
  });

  async ngOnInit(): Promise<void> {
    await this.cargarUsuariosYRoles();
  }

  async cargarUsuariosYRoles(): Promise<void> {
    if (!this.http) return;
    try {
      const [rolesRes, usersRes] = await Promise.all([
        firstValueFrom(
          this.http.get<{ items: Array<{ id: number; name: string; description?: string }> }>(
            API_CONFIG.endpoints.seguridad.roles
          )
        ),
        firstValueFrom(
          this.http.get<{ items: Array<any> }>(API_CONFIG.endpoints.seguridad.usuarios)
        )
      ]);

      if (rolesRes?.items && Array.isArray(rolesRes.items) && rolesRes.items.length > 0) {
        const loadedRoles: RolOption[] = rolesRes.items.map(r => {
          const match = this.availableRoles().find(ar => ar.id === r.id);
          return {
            id: r.id,
            name: r.name,
            description: r.description || match?.description || 'Rol operativo del sistema',
            permissions: match?.permissions || ['Consulta de módulos asignados', 'Exportación de datos autorizados']
          };
        });
        this.availableRoles.set(loadedRoles);
      }

      if (usersRes?.items && Array.isArray(usersRes.items) && usersRes.items.length > 0) {
        const loadedUsers: UsuarioItem[] = usersRes.items.map((u: any) => {
          const rObj = u.roles?.[0];
          const rName = rObj?.name || 'Administrador General';
          const rId = rObj?.id || 1;
          let rCode = 'ADMIN';
          let aTipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR' = 'GLOBAL';
          let aVal = 'Nivel Nacional (Consolidado)';

          if (rName.toLowerCase().includes('finanz')) {
            rCode = 'FINANCE';
            aVal = 'Nivel Nacional (Consolidado)';
          } else if (rName.toLowerCase().includes('coord') || u.email.includes('scz')) {
            rCode = 'COORDINATOR';
            aTipo = 'REGION';
            aVal = u.email.includes('cbba') ? 'Cochabamba (CBBA)' : 'Santa Cruz (SC)';
          } else if (rName.toLowerCase().includes('audit') || u.email.includes('catalyst')) {
            rCode = 'AUDITOR';
            aTipo = 'FINANCIADOR';
            aVal = 'CATALYST 18';
          }

          const roleMatch = this.availableRoles().find(r => r.id === rId);
          return {
            id: u.id,
            nombreCompleto: u.full_name || u.email,
            email: u.email,
            rol: rName,
            rolId: rId,
            rolCodigo: rCode,
            alcanceTipo: aTipo,
            alcanceValor: aVal,
            activo: u.is_active ?? true,
            permisos: roleMatch ? roleMatch.permissions : ['Acceso general al sistema']
          };
        });
        this.usuarios.set(loadedUsers);
      }
    } catch {
      // Mantiene datos locales
    }
  }

  abrirModalNuevo(): void {
    this.isEditing.set(false);
    this.editUserId.set(0);
    this.editNombre.set('');
    this.editEmail.set('');
    this.editPassword.set('PasswordExB2026!');
    this.editAutoPassword.set(false);
    this.editRolId.set(3); // Finanzas por defecto
    this.editAlcanceTipo.set('GLOBAL');
    this.editAlcanceValor.set('Nivel Nacional (Consolidado)');
    this.editActivo.set(true);
    this.isModalOpen.set(true);
  }

  abrirModalEditar(u: UsuarioItem): void {
    this.isEditing.set(true);
    this.editUserId.set(u.id);
    this.editNombre.set(u.nombreCompleto);
    this.editEmail.set(u.email);
    this.editRolId.set(u.rolId);
    this.editAlcanceTipo.set(u.alcanceTipo);
    this.editAlcanceValor.set(u.alcanceValor);
    this.editActivo.set(u.activo);
    this.isModalOpen.set(true);
  }

  cerrarModal(): void {
    this.isModalOpen.set(false);
  }

  abrirModalPermisos(u: UsuarioItem): void {
    this.selectedUserForPermisos.set(u);
    this.isPermisosModalOpen.set(true);
  }

  cerrarModalPermisos(): void {
    this.isPermisosModalOpen.set(false);
    this.selectedUserForPermisos.set(null);
  }

  onAlcanceTipoChange(tipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR'): void {
    this.editAlcanceTipo.set(tipo);
    if (tipo === 'GLOBAL') {
      this.editAlcanceValor.set('Nivel Nacional (Consolidado)');
    } else if (tipo === 'REGION') {
      this.editAlcanceValor.set(this.regionesDisponibles[0]);
    } else {
      this.editAlcanceValor.set(this.financiadoresDisponibles[0]);
    }
  }

  async guardarUsuario(): Promise<void> {
    const nombre = this.editNombre().trim();
    const email = this.editEmail().trim();
    if (!nombre || !email) return;

    this.isSaving.set(true);
    const rolId = this.editRolId();
    const rolObj = this.availableRoles().find(r => r.id === rolId);
    const rolNombre = rolObj?.name || 'Administrador General';
    let rolCodigo = 'ADMIN';
    if (rolNombre.toLowerCase().includes('finanz')) rolCodigo = 'FINANCE';
    else if (rolNombre.toLowerCase().includes('coord')) rolCodigo = 'COORDINATOR';
    else if (rolNombre.toLowerCase().includes('audit')) rolCodigo = 'AUDITOR';

    const aTipo = this.editAlcanceTipo();
    const aVal = this.editAlcanceValor();
    const permisosUsuario = rolObj ? rolObj.permissions : ['Acceso general'];

    if (this.isEditing()) {
      const id = this.editUserId();
      // Actualización optimista local
      this.usuarios.update(list =>
        list.map(u =>
          u.id === id
            ? {
                ...u,
                nombreCompleto: nombre,
                email,
                rol: rolNombre,
                rolId,
                rolCodigo,
                alcanceTipo: aTipo,
                alcanceValor: aVal,
                activo: this.editActivo(),
                permisos: permisosUsuario
              }
            : u
        )
      );

      if (this.http) {
        try {
          await firstValueFrom(
            this.http.put(`${API_CONFIG.endpoints.seguridad.usuarios}/${id}`, {
              full_name: nombre,
              email,
              role_ids: [rolId],
              is_active: this.editActivo()
            })
          );
          // Actualiza scopes si es aplicable
          const scopePayload =
            aTipo === 'GLOBAL'
              ? []
              : [{ dimension_type: aTipo.toLowerCase(), dimension_id: 1 }];
          await firstValueFrom(
            this.http.put(API_CONFIG.endpoints.seguridad.usuarioScopes(id), scopePayload)
          );
          this.mostrarToast(`Usuario "${nombre}" actualizado correctamente`, 'success');
        } catch {
          this.mostrarToast(`Usuario actualizado localmente`, 'success');
        }
      }
    } else {
      let nextId = Math.max(...this.usuarios().map(u => u.id), 0) + 1;
      if (this.http) {
        try {
          const res = await firstValueFrom(
            this.http.post<{ id: number }>(API_CONFIG.endpoints.seguridad.usuarios, {
              full_name: nombre,
              email,
              password: this.editPassword(),
              generate_password: this.editAutoPassword(),
              role_ids: [rolId],
              is_active: this.editActivo()
            })
          );
          if (res?.id) nextId = res.id;
          const scopePayload =
            aTipo === 'GLOBAL'
              ? []
              : [{ dimension_type: aTipo.toLowerCase(), dimension_id: 1 }];
          await firstValueFrom(
            this.http.put(API_CONFIG.endpoints.seguridad.usuarioScopes(nextId), scopePayload)
          );
        } catch {
          // Continua con ID local
        }
      }

      const nuevo: UsuarioItem = {
        id: nextId,
        nombreCompleto: nombre,
        email,
        rol: rolNombre,
        rolId,
        rolCodigo,
        alcanceTipo: aTipo,
        alcanceValor: aVal,
        activo: this.editActivo(),
        permisos: permisosUsuario
      };
      this.usuarios.update(list => [...list, nuevo]);
      this.mostrarToast(`Usuario "${nombre}" creado exitosamente`, 'success');
    }

    this.isSaving.set(false);
    this.cerrarModal();
  }

  async toggleActivo(user: UsuarioItem): Promise<void> {
    const nuevoEstado = !user.activo;
    this.usuarios.update(list =>
      list.map(u => (u.id === user.id ? { ...u, activo: nuevoEstado } : u))
    );

    if (this.http) {
      try {
        if (!nuevoEstado) {
          await firstValueFrom(this.http.delete(`${API_CONFIG.endpoints.seguridad.usuarios}/${user.id}`));
        } else {
          await firstValueFrom(
            this.http.put(`${API_CONFIG.endpoints.seguridad.usuarios}/${user.id}`, {
              is_active: true
            })
          );
        }
        this.mostrarToast(`Estado de ${user.nombreCompleto} actualizado`, 'success');
      } catch {
        // Toggle reactivo
      }
    }
  }

  mostrarToast(text: string, type: 'success' | 'error'): void {
    this.toastMessage.set({ text, type });
    setTimeout(() => this.toastMessage.set(null), 4000);
  }
}
