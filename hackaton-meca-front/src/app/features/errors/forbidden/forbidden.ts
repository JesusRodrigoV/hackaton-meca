import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-forbidden',
  standalone: true,
  imports: [CommonModule, RouterLink, BoxIconComponent],
  templateUrl: './forbidden.html',
  styleUrls: ['./forbidden.scss']
})
export class Forbidden {
  readonly auth = inject(AuthService);
}
