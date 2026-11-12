import { Component, OnDestroy, afterNextRender, inject } from '@angular/core';
import { KitRuntimeService } from '../kit-runtime';

@Component({
  selector: 'app-landing',
  standalone: true,
  templateUrl: './landing.html',
  styleUrl: './landing.scss'
})
export class Landing implements OnDestroy {
  private readonly kit = inject(KitRuntimeService);

  constructor() {
    afterNextRender(() => this.kit.startLanding());
  }

  ngOnDestroy(): void {
    this.kit.stopLanding();
  }
}
