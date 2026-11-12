import { Component, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { HasPermissionDirective } from '../../../core/permissions/has-permission';

@Component({
  selector: 'app-modificaciones',
  imports: [CommonModule, FormsModule, DecimalPipe, BoxIconComponent, HasPermissionDirective],
  templateUrl: './modificaciones.html',
  styleUrl: './modificaciones.scss'
})
export class Modificaciones {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly modificaciones = this.financialService.modificaciones;
  readonly techos = this.financialService.techos;

  readonly showModal = signal<boolean>(false);
  readonly tipoModificacion = signal<'TRASPASO' | 'INCREMENTO' | 'DISMINUCION'>('TRASPASO');
  readonly cuentaOrigen = signal<string>('5.1.02 - Honorarios Asesores Pedagógicos');
  readonly cuentaDestino = signal<string>('5.1.01 - Sueldos y Cargas Sociales Profesores');
  readonly montoBob = signal<number>(5000);
  readonly descripcion = signal<string>('');
  readonly errorValidacion = signal<string>('');

  abrirModal(): void {
    this.showModal.set(true);
    this.errorValidacion.set('');
    this.descripcion.set('');
    this.montoBob.set(5000);
  }

  cerrarModal(): void {
    this.showModal.set(false);
  }

  guardarSolicitud(): void {
    if (this.montoBob() <= 0) {
      this.errorValidacion.set('El monto debe ser superior a 0 BOB.');
      return;
    }
    if (!this.descripcion().trim()) {
      this.errorValidacion.set('Debe ingresar una justificación técnica o legal.');
      return;
    }

    const solicitante = this.authService.currentUser()?.fullName ?? 'Usuario Operativo';

    this.financialService.agregarModificacion({
      tipo: this.tipoModificacion(),
      descripcion: this.descripcion(),
      cuentaOrigen: this.tipoModificacion() === 'TRASPASO' ? this.cuentaOrigen() : undefined,
      cuentaDestino: this.cuentaDestino(),
      montoBob: this.montoBob(),
      solicitante
    });

    this.cerrarModal();
  }

  aprobar(id: number): void {
    const aprobador = this.authService.currentUser()?.fullName ?? 'Aprobador Autorizado';
    this.financialService.aprobarModificacion(id, aprobador);
  }
}
