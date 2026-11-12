import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth/auth';
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
