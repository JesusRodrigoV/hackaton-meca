import { Component, inject } from '@angular/core';
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

  readonly sections: NavSection[] = [
    {
      title: 'PRINCIPAL',
      items: [
        { label: 'Dashboard', route: '/dashboard', icon: 'grid-alt', permission: 'dashboard.ver' }
      ]
    },
    {
      title: 'PRESUPUESTOS',
      items: [
        { label: 'Techos Anuales', route: '/presupuestos/techos', icon: 'wallet', permission: 'presupuestos.ver' },
        { label: 'Modificaciones', route: '/presupuestos/modificaciones', icon: 'transfer-alt', permission: 'modificaciones.solicitar' }
      ]
    },
    {
      title: 'EJECUCIÓN CONTABLE',
      items: [
        { label: 'Libro de Movimientos', route: '/ejecucion/movimientos', icon: 'receipt', permission: 'reportes.ver' },
        { label: 'Importador Excel', route: '/ejecucion/importador', icon: 'cloud-upload', permission: 'importaciones.crear' }
      ]
    },
    {
      title: 'INFORMES Y CUENTAS',
      items: [
        { label: 'Centro 7 Reportes', route: '/reportes', icon: 'bar-chart-alt-2', permission: 'reportes.ver' }
      ]
    },
    {
      title: 'GOBERNANZA & CONTROL',
      items: [
        { label: 'Usuarios y Scopes', route: '/seguridad/usuarios', icon: 'user', permission: 'usuarios.admin' },
        { label: 'Matriz de Roles', route: '/seguridad/roles', icon: 'shield-quarter', permission: 'roles.admin' },
        { label: 'Bitácora Auditoría', route: '/seguridad/auditoria', icon: 'history', permission: 'auditoria.ver' }
      ]
    }
  ];
}
