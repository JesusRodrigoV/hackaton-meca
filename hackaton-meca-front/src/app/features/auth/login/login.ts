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

  async onSubmit(): Promise<void> {
    this.errorMessage.set('');
    this.isSubmitting.set(true);

    try {
      const ok = await this.authService.login(this.email(), this.password());
      this.isSubmitting.set(false);
      if (ok) {
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
        this.router.navigateByUrl(returnUrl);
      } else {
        this.errorMessage.set('Credenciales no válidas. Por favor verifique sus datos.');
      }
    } catch {
      this.isSubmitting.set(false);
      this.errorMessage.set('Error al conectar con el servidor de autenticación.');
    }
  }
}
