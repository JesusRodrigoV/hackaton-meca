import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
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
  private readonly router = inject(Router);

  onGestionChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.auth.setGestion(Number(target.value));
  }

  async onLogout(): Promise<void> {
    await this.auth.logout();
    this.router.navigate(['/login']);
  }
}
