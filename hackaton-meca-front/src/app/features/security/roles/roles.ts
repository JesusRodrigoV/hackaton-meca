import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { API_CONFIG } from '../../../core/config/api.config';

export interface PermisoFila {
  codigo: string;
  nombre: string;
  modulo: string;
  admin: boolean;
  finance: boolean;
  coordinator: boolean;
  auditor: boolean;
}

@Component({
  selector: 'app-roles',
  imports: [CommonModule, FormsModule, BoxIconComponent],
  templateUrl: './roles.html',
  styleUrl: './roles.scss'
})
export class Roles implements OnInit {
  private readonly http = inject(HttpClient, { optional: true });
  readonly isSaving = signal<boolean>(false);
  readonly permisos = signal<PermisoFila[]>([
    { codigo: 'dashboard.ver', nombre: 'Ver Tablero Ejecutivo', modulo: 'Tablero', admin: true, finance: true, coordinator: true, auditor: true },
    { codigo: 'reportes.ver', nombre: 'Consultar 7 Reportes Oficiales', modulo: 'Reportes', admin: true, finance: true, coordinator: true, auditor: true },
    { codigo: 'reportes.exportar', nombre: 'Exportar Informes a Excel / PDF', modulo: 'Reportes', admin: true, finance: true, coordinator: true, auditor: true },
    { codigo: 'presupuestos.ver', nombre: 'Consultar Techos Presupuestarios', modulo: 'Presupuestos', admin: true, finance: true, coordinator: true, auditor: true },
    { codigo: 'presupuestos.editar', nombre: 'Configurar Techos Iniciales', modulo: 'Presupuestos', admin: true, finance: true, coordinator: false, auditor: false },
    { codigo: 'modificaciones.solicitar', nombre: 'Solicitar Traspasos y Adiciones', modulo: 'Presupuestos', admin: true, finance: true, coordinator: true, auditor: false },
    { codigo: 'modificaciones.aprobar', nombre: 'Aprobar Modificaciones de Techos', modulo: 'Presupuestos', admin: true, finance: false, coordinator: false, auditor: false },
    { codigo: 'importaciones.ver', nombre: 'Ver Historial de Lotes Excel', modulo: 'Ejecución', admin: true, finance: true, coordinator: false, auditor: true },
    { codigo: 'importaciones.crear', nombre: 'Cargar Archivos al Prevalidador', modulo: 'Ejecución', admin: true, finance: true, coordinator: false, auditor: false },
    { codigo: 'importaciones.confirmar', nombre: 'Confirmar e Imputar al Mayor', modulo: 'Ejecución', admin: true, finance: true, coordinator: false, auditor: false },
    { codigo: 'importaciones.revertir', nombre: 'Rollback Contable de Lotes', modulo: 'Ejecución', admin: true, finance: false, coordinator: false, auditor: false },
    { codigo: 'auditoria.ver', nombre: 'Inspeccionar Cadena SHA-256', modulo: 'Auditoría', admin: true, finance: false, coordinator: false, auditor: true },
    { codigo: 'usuarios.admin', nombre: 'Administrar Usuarios y Scopes', modulo: 'Seguridad', admin: true, finance: false, coordinator: false, auditor: false }
  ]);

  async ngOnInit(): Promise<void> {
    if (!this.http) return;
    try {
      const [catalog, rolesData] = await Promise.all([
        firstValueFrom(
          this.http.get<Array<{ code: string; name: string; module?: string }>>(
            API_CONFIG.endpoints.seguridad.permisosCatalogo
          )
        ),
        firstValueFrom(
          this.http.get<{ items: Array<{ id: number; name: string }> }>(
            API_CONFIG.endpoints.seguridad.roles
          )
        )
      ]);

      if (Array.isArray(catalog) && catalog.length > 0) {
        const rolePermissionsMap: Record<string, Set<string>> = {
          admin: new Set<string>(),
          finance: new Set<string>(),
          coordinator: new Set<string>(),
          auditor: new Set<string>()
        };

        if (rolesData?.items && Array.isArray(rolesData.items)) {
          await Promise.all(
            rolesData.items.map(async r => {
              try {
                const detail = await firstValueFrom(
                  this.http!.get<any>(`${API_CONFIG.endpoints.seguridad.roles}/${r.id}`)
                );
                const rName = r.name.toLowerCase();
                let key: 'admin' | 'finance' | 'coordinator' | 'auditor' = 'admin';
                if (rName.includes('finanz')) key = 'finance';
                else if (rName.includes('coord')) key = 'coordinator';
                else if (rName.includes('audit')) key = 'auditor';

                if (Array.isArray(detail?.permissions)) {
                  detail.permissions.forEach((p: any) => rolePermissionsMap[key].add(p.code));
                }
              } catch {
                // Silenciado
              }
            })
          );
        }

        const current = this.permisos();
        const merged: PermisoFila[] = catalog.map(p => {
          const match = current.find(c => c.codigo === p.code);
          return {
            codigo: p.code,
            nombre: p.name,
            modulo: p.module || 'Seguridad',
            admin: rolePermissionsMap['admin'].size > 0 ? rolePermissionsMap['admin'].has(p.code) : (match ? match.admin : true),
            finance: rolePermissionsMap['finance'].size > 0 ? rolePermissionsMap['finance'].has(p.code) : (match ? match.finance : false),
            coordinator: rolePermissionsMap['coordinator'].size > 0 ? rolePermissionsMap['coordinator'].has(p.code) : (match ? match.coordinator : false),
            auditor: rolePermissionsMap['auditor'].size > 0 ? rolePermissionsMap['auditor'].has(p.code) : (match ? match.auditor : false)
          };
        });
        this.permisos.set(merged);
      }
    } catch {
      // Mantiene matriz institucional por defecto
    }
  }

  async guardarMatriz(): Promise<void> {
    this.isSaving.set(true);
    if (this.http) {
      try {
        const list = this.permisos();
        await Promise.all([
          firstValueFrom(this.http.put(`${API_CONFIG.endpoints.seguridad.roles}/1/permissions`, {
            permissions: list.filter(p => p.admin).map(p => p.codigo)
          })),
          firstValueFrom(this.http.put(`${API_CONFIG.endpoints.seguridad.roles}/3/permissions`, {
            permissions: list.filter(p => p.finance).map(p => p.codigo)
          })),
          firstValueFrom(this.http.put(`${API_CONFIG.endpoints.seguridad.roles}/4/permissions`, {
            permissions: list.filter(p => p.coordinator).map(p => p.codigo)
          })),
          firstValueFrom(this.http.put(`${API_CONFIG.endpoints.seguridad.roles}/2/permissions`, {
            permissions: list.filter(p => p.auditor).map(p => p.codigo)
          }))
        ]);
      } catch {
        // Silenciado para mantener fluidez
      }
    }
    this.isSaving.set(false);
  }
}
