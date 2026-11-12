import { Component, inject, signal } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-login',
  imports: [FormsModule, BoxIconComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly authService = inject(AuthService);

  readonly email = signal<string>('');
  readonly password = signal<string>('');
  readonly errorMessage = signal<string>('');
  readonly isSubmitting = signal<boolean>(false);

  // Flujo 2FA
  readonly step = signal<'credentials' | '2fa'>('credentials');
  readonly sessionToken = signal<string>('');
  readonly totpCode = signal<string>('');

  async onSubmit(): Promise<void> {
    this.errorMessage.set('');
    this.isSubmitting.set(true);

    try {
      if (this.step() === 'credentials') {
        const res = await this.authService.login(this.email(), this.password());
        this.isSubmitting.set(false);

        if (res.requires2Fa) {
          this.sessionToken.set(res.sessionToken || '');
          this.step.set('2fa');
          return;
        }

        if (res.success) {
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
          this.router.navigateByUrl(returnUrl);
        } else {
          this.errorMessage.set(res.error || 'Credenciales no válidas. Por favor verifique sus datos.');
        }
      } else {
        const ok = await this.authService.verifyLogin2Fa(this.sessionToken(), this.totpCode());
        this.isSubmitting.set(false);

        if (ok) {
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
          this.router.navigateByUrl(returnUrl);
        } else {
          this.errorMessage.set('Código de seguridad incorrecto o expirado. Intente nuevamente.');
        }
      }
    } catch {
      this.isSubmitting.set(false);
      this.errorMessage.set('Error al conectar con el servidor de autenticación.');
    }
  }

  volverACredenciales(): void {
    this.step.set('credentials');
    this.totpCode.set('');
    this.errorMessage.set('');
  }
}
