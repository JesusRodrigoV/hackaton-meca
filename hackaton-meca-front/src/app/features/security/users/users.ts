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

  toggleActivo(user: UsuarioItem): void {
    user.activo = !user.activo;
  }

  async ngOnInit(): Promise<void> {
    if (!this.http) return;
    try {
      const resp = await firstValueFrom(this.http.get<any>(API_CONFIG.endpoints.seguridad.usuarios));
      const items = Array.isArray(resp) ? resp : resp?.items;
      if (Array.isArray(items) && items.length > 0) {
        const loaded: UsuarioItem[] = items.map((u: any) => ({
          id: u.id,
          nombreCompleto: u.full_name || `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email,
          email: u.email,
          rol: u.roles?.[0]?.name || 'Usuario',
          rolCodigo: u.roles?.[0]?.code || 'ADMIN',
          alcanceTipo: 'GLOBAL',
          alcanceValor: 'Nivel Nacional',
          activo: u.is_active ?? true
        }));
        this.usuarios.set(loaded);
      }
    } catch {
      // Mantiene usuarios demo por defecto
    }
  }
}
