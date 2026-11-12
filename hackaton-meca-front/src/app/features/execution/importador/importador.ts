import { Component, inject, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { HasPermissionDirective } from '../../../core/permissions/has-permission';

@Component({
  selector: 'app-importador',
  imports: [CommonModule, DecimalPipe, BoxIconComponent, HasPermissionDirective],
  templateUrl: './importador.html',
  styleUrl: './importador.scss'
})
export class Importador {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly importaciones = this.financialService.importaciones;

  readonly isDragging = signal<boolean>(false);
  readonly selectedFile = signal<File | null>(null);
  readonly isUploading = signal<boolean>(false);
  readonly previewReady = signal<boolean>(false);

  readonly previewStats = signal({
    filasValidas: 142,
    filasError: 2,
    montoTotalBob: 185600.0,
    cuentaInexistente: 1,
    formatoInvalido: 1
  });

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(): void {
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  private handleFile(file: File): void {
    this.selectedFile.set(file);
    this.isUploading.set(true);

    // Simulación de prevalidación de esquema contable
    setTimeout(() => {
      this.isUploading.set(false);
      this.previewReady.set(true);
    }, 600);
  }

  cancelarPreview(): void {
    this.selectedFile.set(null);
    this.previewReady.set(false);
  }

  async confirmarIngesta(): Promise<void> {
    const file = this.selectedFile();
    if (file) {
      await this.financialService.subirPlanillaExcelApi(file);
    }
    this.cancelarPreview();
  }

  async revertir(loteId: number): Promise<void> {
    if (confirm(`¿Está seguro de revertir el Lote #${loteId}? Todos los movimientos asociados serán dados de baja en el libro mayor.`)) {
      await this.financialService.revertirLoteApi(loteId);
    }
  }
}
