import { Component, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/auth/auth';
import { BoxIconComponent } from '../../shared/components/box-icon/box-icon';

export interface AppNotification {
  id: number;
  tipo: 'urgente' | 'aviso' | 'solicitud';
  titulo: string;
  mensaje: string;
  tiempo: string;
  leido: boolean;
  ruta?: string;
}

@Component({
  selector: 'app-topbar',
  imports: [CommonModule, FormsModule, RouterLink, BoxIconComponent],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss'
})
export class Topbar {
  readonly auth = inject(AuthService);

  readonly showNotifications = signal<boolean>(false);

  readonly notifications = signal<AppNotification[]>([
    {
      id: 1,
      tipo: 'urgente',
      titulo: 'Sobregiro en partida 5.1.02',
      mensaje: 'Honorarios Asesores Pedagógicos (Santa Cruz) superó el techo en Bs 7.300.',
      tiempo: 'Hace 25 min',
      leido: false,
      ruta: '/presupuestos/techos'
    },
    {
      id: 2,
      tipo: 'urgente',
      titulo: 'Gasto sin presupuesto asignado',
      mensaje: 'Partida 5.5.01 Gastos Notariales registra Bs 4.850 sin techo previo.',
      tiempo: 'Hace 1 hora',
      leido: false,
      ruta: '/presupuestos/techos'
    },
    {
      id: 3,
      tipo: 'solicitud',
      titulo: 'Solicitud de traspaso pendiente',
      mensaje: 'Mariana Paz solicitó traspaso de Bs 5.000 para talleres presenciales.',
      tiempo: 'Hace 3 horas',
      leido: false,
      ruta: '/presupuestos/modificaciones'
    },
    {
      id: 4,
      tipo: 'aviso',
      titulo: 'Archivo cargado con 2 errores',
      mensaje: 'El lote GASTOS_CAMPO_SANTA_CRUZ_MARZO.xlsx tiene 2 filas sin procesar.',
      tiempo: 'Ayer',
      leido: true,
      ruta: '/ejecucion/importador'
    }
  ]);

  readonly unreadCount = computed(() =>
    this.notifications().filter(n => !n.leido).length
  );

  toggleNotifications(): void {
    this.showNotifications.update(v => !v);
  }

  closeNotifications(): void {
    this.showNotifications.set(false);
  }

  markAllAsRead(): void {
    this.notifications.update(list => list.map(n => ({ ...n, leido: true })));
  }

  onRoleChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const roleKey = target.value as 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR';
    this.auth.switchUser(roleKey);
  }

  onGestionChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.auth.setGestion(Number(target.value));
  }
}
