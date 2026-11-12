import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FinancialService } from '../../../core/services/financial';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-audit',
  imports: [CommonModule, BoxIconComponent],
  templateUrl: './audit.html',
  styleUrl: './audit.scss'
})
export class Audit implements OnInit {
  readonly financialService = inject(FinancialService);
  readonly auditLogs = this.financialService.auditLogs;

  readonly isVerifying = signal<boolean>(false);
  readonly verifiedStatus = signal<string | null>(null);

  ngOnInit(): void {
    this.financialService.cargarAuditoriaApi();
  }

  async verificarCadena(): Promise<void> {
    this.isVerifying.set(true);
    this.verifiedStatus.set(null);

    const valid = await this.financialService.verificarIntegridadCadenaApi();
    this.isVerifying.set(false);
    if (valid) {
      this.verifiedStatus.set('Cadena criptográfica íntegra: Todos los hashes SHA-256 coinciden con las firmas previas.');
    } else {
      this.verifiedStatus.set('Alerta: Se detectó una inconsistencia en la cadena de bloques de auditoría.');
    }
  }
}
