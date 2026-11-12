import { Component, HostListener, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth';
import { BoxIconComponent } from '../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, FormsModule, BoxIconComponent],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss'
})
export class Topbar implements OnInit {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Estado del modal de 2FA
  readonly showModal2Fa = signal<boolean>(false);
  readonly setupData = signal<{ secret: string; otpauth_uri: string; qr_code?: string } | null>(null);
  readonly verifyCode = signal<string>('');
  readonly disablePassword = signal<string>('');
  readonly disableCode = signal<string>('');
  readonly backupCodes = signal<string[]>([]);
  readonly errorMessage = signal<string>('');
  readonly successMessage = signal<string>('');
  readonly isProcessing = signal<boolean>(false);
  readonly copiado = signal<boolean>(false);

  ngOnInit(): void {
    this.auth.check2FaStatus();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.showModal2Fa()) {
      this.cerrarModal2Fa();
    }
  }

  onGestionChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.auth.setGestion(Number(target.value));
  }

  async onLogout(): Promise<void> {
    await this.auth.logout();
    this.router.navigate(['/login']);
  }

  abrirModal2Fa(): void {
    this.showModal2Fa.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.verifyCode.set('');
    this.disablePassword.set('');
    this.disableCode.set('');
    this.setupData.set(null);
    this.backupCodes.set([]);
    this.copiado.set(false);
    this.auth.check2FaStatus();
  }

  cerrarModal2Fa(): void {
    this.showModal2Fa.set(false);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.verifyCode.set('');
    this.disablePassword.set('');
    this.disableCode.set('');
    this.setupData.set(null);
    this.copiado.set(false);
  }

  copiarClaveSecreta(): void {
    const sec = this.setupData()?.secret;
    if (sec && typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(sec);
      this.copiado.set(true);
      setTimeout(() => this.copiado.set(false), 2000);
    }
  }

  async iniciarSetup2Fa(): Promise<void> {
    this.isProcessing.set(true);
    this.errorMessage.set('');
    const data = await this.auth.setup2Fa();
    this.isProcessing.set(false);
    if (data) {
      this.setupData.set(data);
    } else {
      this.errorMessage.set('No se pudo generar la clave de seguridad. Verifique su sesión.');
    }
  }

  async confirmarActivar2Fa(): Promise<void> {
    const code = this.verifyCode().trim();
    if (!code) {
      this.errorMessage.set('Ingrese el código de 6 dígitos generado por su aplicación.');
      return;
    }

    this.isProcessing.set(true);
    this.errorMessage.set('');
    const res = await this.auth.enable2Fa(code);
    this.isProcessing.set(false);

    if (res.success) {
      this.successMessage.set('¡Autenticación de dos pasos activada exitosamente!');
      this.backupCodes.set(res.backupCodes || []);
      this.setupData.set(null);
    } else {
      this.errorMessage.set(res.error || 'Código incorrecto. Intente nuevamente.');
    }
  }

  async confirmarDesactivar2Fa(): Promise<void> {
    const pwd = this.disablePassword().trim();
    const code = this.disableCode().trim();
    if (!pwd || !code) {
      this.errorMessage.set('Ingrese su contraseña actual y el código 2FA para confirmar.');
      return;
    }

    this.isProcessing.set(true);
    this.errorMessage.set('');
    const res = await this.auth.disable2Fa(pwd, code);
    this.isProcessing.set(false);

    if (res.success) {
      this.successMessage.set('2FA deshabilitado correctamente.');
      this.disablePassword.set('');
      this.disableCode.set('');
    } else {
      this.errorMessage.set(res.error || 'Contraseña o código 2FA incorrectos.');
    }
  }
}
