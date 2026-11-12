import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth';
import { FinancialService } from '../../core/services/financial';
import { BoxIconComponent } from '../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [FormsModule, BoxIconComponent],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss'
})
export class Topbar {
  readonly auth = inject(AuthService);
  readonly financial = inject(FinancialService);
  private readonly router = inject(Router);

  onRoleChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const roleKey = target.value as 'ADMIN' | 'FINANCE' | 'COORDINATOR' | 'AUDITOR';
    this.auth.switchUser(roleKey);
  }

  onGestionChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.auth.setGestion(Number(target.value));
  }

  async onLogout(): Promise<void> {
    await this.auth.logout();
    this.router.navigate(['/login']);
  }
}
