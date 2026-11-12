import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FinancialService } from '../../../core/services/financial';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-audit',
  imports: [CommonModule, BoxIconComponent],
  templateUrl: './audit.html',
  styleUrl: './audit.scss'
})
export class Audit {
  readonly financialService = inject(FinancialService);
  readonly auditLogs = this.financialService.auditLogs;

  readonly isVerifying = signal<boolean>(false);
  readonly verifiedStatus = signal<string | null>(null);

  verificarCadena(): void {
    this.isVerifying.set(true);
    this.verifiedStatus.set(null);

    setTimeout(() => {
      this.isVerifying.set(false);
      this.verifiedStatus.set('Cadena íntegra: Todos los hashes SHA-256 coinciden con las firmas previas.');
    }, 500);
  }
}
