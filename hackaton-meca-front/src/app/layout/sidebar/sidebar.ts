import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../core/auth/auth';
import { HasPermissionDirective } from '../../core/permissions/has-permission';
import { BoxIconComponent } from '../../shared/components/box-icon/box-icon';

interface NavItem {
  label: string;
  route: string;
  icon: string;
  permission?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive, HasPermissionDirective, BoxIconComponent],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class Sidebar {
  readonly auth = inject(AuthService);

  // Estado reactivo de colapso con persistencia
  readonly isCollapsed = signal<boolean>(false);

  readonly sections: NavSection[] = [
    {
      title: 'PRINCIPAL',
      items: [
        { label: 'Resumen general', route: '/dashboard', icon: 'grid-alt', permission: 'dashboard.ver' }
      ]
    },
    {
      title: 'PRESUPUESTOS',
      items: [
        { label: 'Presupuesto anual', route: '/presupuestos/techos', icon: 'wallet', permission: 'presupuestos.ver' },
        { label: 'Traspasos y ajustes', route: '/presupuestos/modificaciones', icon: 'transfer-alt', permission: 'modificaciones.solicitar' }
      ]
    },
    {
      title: 'GASTOS',
      items: [
        { label: 'Registro de gastos', route: '/ejecucion/movimientos', icon: 'receipt', permission: 'reportes.ver' },
        { label: 'Cargar desde Excel', route: '/ejecucion/importador', icon: 'cloud-upload', permission: 'importaciones.crear' }
      ]
    },
    {
      title: 'REPORTES',
      items: [
        { label: 'Reportes financieros', route: '/reportes', icon: 'bar-chart-alt-2', permission: 'reportes.ver' }
      ]
    },
    {
      title: 'SEGURIDAD',
      items: [
        { label: 'Usuarios y accesos', route: '/seguridad/usuarios', icon: 'user', permission: 'usuarios.admin' },
        { label: 'Permisos por rol', route: '/seguridad/roles', icon: 'shield-quarter', permission: 'roles.admin' },
        { label: 'Auditoría de cambios', route: '/seguridad/auditoria', icon: 'history', permission: 'auditoria.ver' }
      ]
    }
  ];

  toggleCollapse(): void {
    this.isCollapsed.update(v => !v);
  }
}
