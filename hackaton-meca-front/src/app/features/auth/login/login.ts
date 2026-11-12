import { Component, inject, signal } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService, PRESET_USERS } from '../../../core/auth/auth';
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

  readonly email = signal<string>('admin@ensenaporbolivia.org');
  readonly password = signal<string>('••••••••••••');
  readonly errorMessage = signal<string>('');
  readonly isSubmitting = signal<boolean>(false);

  readonly demoRoles = [
    {
      key: 'ADMIN' as const,
      name: 'Director General',
      role: 'Admin General',
      scope: 'Consolidado Nacional',
      icon: 'shield-quarter',
      color: '#2b255c'
    },
    {
      key: 'FINANCE' as const,
      name: 'Técnico Finanzas',
      role: 'Contabilidad',
      scope: 'Operaciones y Mayor',
      icon: 'calculator',
      color: '#00923d'
    },
    {
      key: 'COORDINATOR' as const,
      name: 'Coord. Santa Cruz',
      role: 'Coordinador Regional',
      scope: 'Región: Santa Cruz',
      icon: 'map-pin',
      color: '#ecc562'
    },
    {
      key: 'AUDITOR' as const,
      name: 'Auditor CATALYST',
      role: 'Auditor Donante',
      scope: 'Financiador: CATALYST 18',
      icon: 'file-find',
      color: '#0d2439'
    }
  ];

  loginAsDemo(roleKey: 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR'): void {
    const preset = PRESET_USERS[roleKey];
    if (preset) {
      this.email.set(preset.email);
      this.authService.switchUser(roleKey);
      const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
      this.router.navigateByUrl(returnUrl);
    }
  }

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
