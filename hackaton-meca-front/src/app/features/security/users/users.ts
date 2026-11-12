import { Component, signal, inject, OnInit } from '@angular/core';
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
  rolCodigo: string;
  alcanceTipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR';
  alcanceValor: string;
  activo: boolean;
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

  // Control de modal de creación / edición
  readonly isModalOpen = signal<boolean>(false);
  readonly isEditing = signal<boolean>(false);
  readonly editUserId = signal<number>(0);

  // Campos de formulario reactivo
  readonly editNombre = signal<string>('');
  readonly editEmail = signal<string>('');
  readonly editRolCodigo = signal<string>('ADMIN');
  readonly editAlcanceTipo = signal<'GLOBAL' | 'REGION' | 'FINANCIADOR'>('GLOBAL');
  readonly editAlcanceValor = signal<string>('Nivel Nacional (Consolidado)');
  readonly editActivo = signal<boolean>(true);

  readonly usuarios = signal<UsuarioItem[]>([
    {
      id: 1,
      nombreCompleto: 'Ana Morales',
      email: 'admin@ensenaporbolivia.org',
      rol: 'Administrador General',
      rolCodigo: 'ADMIN',
      alcanceTipo: 'GLOBAL',
      alcanceValor: 'Nivel Nacional (Consolidado)',
      activo: true
    },
    {
      id: 2,
      nombreCompleto: 'Carlos Rojas',
      email: 'finanzas@ensenaporbolivia.org',
      rol: 'Contador / Finanzas',
      rolCodigo: 'FINANCE',
      alcanceTipo: 'GLOBAL',
      alcanceValor: 'Operaciones Contables Nacional',
      activo: true
    },
    {
      id: 3,
      nombreCompleto: 'Mariana Paz',
      email: 'coord.scz@ensenaporbolivia.org',
      rol: 'Coordinador Regional',
      rolCodigo: 'COORDINATOR',
      alcanceTipo: 'REGION',
      alcanceValor: 'Santa Cruz (SC)',
      activo: true
    },
    {
      id: 4,
      nombreCompleto: 'Roberto Silva',
      email: 'auditor.catalyst@fundacion.org',
      rol: 'Auditor Externo Donante',
      rolCodigo: 'AUDITOR',
      alcanceTipo: 'FINANCIADOR',
      alcanceValor: 'CATALYST 18',
      activo: true
    },
    {
      id: 5,
      nombreCompleto: 'Elena Vaca',
      email: 'coord.cbba@ensenaporbolivia.org',
      rol: 'Coordinador Regional',
      rolCodigo: 'COORDINATOR',
      alcanceTipo: 'REGION',
      alcanceValor: 'Cochabamba (CBBA)',
      activo: true
    }
  ]);

  abrirModalNuevo(): void {
    this.isEditing.set(false);
    this.editUserId.set(0);
    this.editNombre.set('');
    this.editEmail.set('');
    this.editRolCodigo.set('FINANCE');
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
    this.editRolCodigo.set(u.rolCodigo);
    this.editAlcanceTipo.set(u.alcanceTipo);
    this.editAlcanceValor.set(u.alcanceValor);
    this.editActivo.set(u.activo);
    this.isModalOpen.set(true);
  }

  cerrarModal(): void {
    this.isModalOpen.set(false);
  }

  onAlcanceTipoChange(tipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR'): void {
    this.editAlcanceTipo.set(tipo);
    if (tipo === 'GLOBAL') {
      this.editAlcanceValor.set('Nivel Nacional (Consolidado)');
    } else if (tipo === 'REGION') {
      this.editAlcanceValor.set('Santa Cruz (SC)');
    } else {
      this.editAlcanceValor.set('CATALYST 18');
    }
  }

  async guardarUsuario(): Promise<void> {
    const nombre = this.editNombre().trim();
    const email = this.editEmail().trim();
    if (!nombre || !email) return;

    this.isSaving.set(true);
    const rolCod = this.editRolCodigo();
    let rolNombre = 'Administrador General';
    if (rolCod === 'FINANCE') rolNombre = 'Contador / Finanzas';
    else if (rolCod === 'COORDINATOR') rolNombre = 'Coordinador Regional';
    else if (rolCod === 'AUDITOR') rolNombre = 'Auditor Externo Donante';

    const roleIdMap: Record<string, number> = {
      ADMIN: 1,
      FINANCE: 2,
      COORDINATOR: 3,
      AUDITOR: 4
    };

    if (this.isEditing()) {
      const id = this.editUserId();
      this.usuarios.update(list =>
        list.map(u =>
          u.id === id
            ? {
                ...u,
                nombreCompleto: nombre,
                email,
                rol: rolNombre,
                rolCodigo: rolCod,
                alcanceTipo: this.editAlcanceTipo(),
                alcanceValor: this.editAlcanceValor(),
                activo: this.editActivo()
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
              role_ids: [roleIdMap[rolCod] ?? 1],
              is_active: this.editActivo()
            })
          );
        } catch {
          // Actualizado reactivamente
        }
      }
    } else {
      const nextId = Math.max(...this.usuarios().map(u => u.id), 0) + 1;
      const nuevo: UsuarioItem = {
        id: nextId,
        nombreCompleto: nombre,
        email,
        rol: rolNombre,
        rolCodigo: rolCod,
        alcanceTipo: this.editAlcanceTipo(),
        alcanceValor: this.editAlcanceValor(),
        activo: this.editActivo()
      };
      this.usuarios.update(list => [...list, nuevo]);

      if (this.http) {
        try {
          await firstValueFrom(
            this.http.post(API_CONFIG.endpoints.seguridad.usuarios, {
              full_name: nombre,
              email,
              password: 'PasswordExB2026!',
              role_ids: [roleIdMap[rolCod] ?? 1],
              is_active: this.editActivo()
            })
          );
        } catch {
          // Creado reactivamente
        }
      }
    }

    this.isSaving.set(false);
    this.cerrarModal();
  }

  async toggleActivo(user: UsuarioItem): Promise<void> {
    user.activo = !user.activo;
    if (this.http) {
      try {
        await firstValueFrom(
          this.http.put(`${API_CONFIG.endpoints.seguridad.usuarios}/${user.id}`, {
            is_active: user.activo
          })
        );
      } catch {
        // Toggle reactivo
      }
    }
  }

  async ngOnInit(): Promise<void> {
    if (!this.http) return;
    try {
      const resp = await firstValueFrom(this.http.get<any>(API_CONFIG.endpoints.seguridad.usuarios));
      const items = Array.isArray(resp) ? resp : resp?.items;
      if (Array.isArray(items) && items.length > 0) {
        const loaded: UsuarioItem[] = items.map((u: any) => {
          const rName = u.roles?.[0]?.name || 'Administrador General';
          let rCode = 'ADMIN';
          let aTipo: 'GLOBAL' | 'REGION' | 'FINANCIADOR' = 'GLOBAL';
          let aVal = 'Nivel Nacional (Consolidado)';

          if (rName.toLowerCase().includes('finanz')) {
            rCode = 'FINANCE';
            aVal = 'Operaciones Contables Nacional';
          } else if (rName.toLowerCase().includes('coord') || u.email.includes('scz')) {
            rCode = 'COORDINATOR';
            aTipo = 'REGION';
            aVal = 'Santa Cruz (SC)';
          } else if (rName.toLowerCase().includes('audit') || u.email.includes('catalyst')) {
            rCode = 'AUDITOR';
            aTipo = 'FINANCIADOR';
            aVal = 'CATALYST 18';
          }

          return {
            id: u.id,
            nombreCompleto: u.full_name || `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email,
            email: u.email,
            rol: rName,
            rolCodigo: rCode,
            alcanceTipo: aTipo,
            alcanceValor: aVal,
            activo: u.is_active ?? true
          };
        });
        this.usuarios.set(loaded);
      }
    } catch {
      // Mantiene usuarios demo por defecto
    }
  }
}
