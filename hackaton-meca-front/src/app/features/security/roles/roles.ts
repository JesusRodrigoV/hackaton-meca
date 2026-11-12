import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

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
export class Roles {
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

  guardarMatriz(): void {
    alert('Matriz de permisos actualizada exitosamente.');
  }
}
