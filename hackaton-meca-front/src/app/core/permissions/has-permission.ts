import {
  Directive,
  Input,
  TemplateRef,
  ViewContainerRef,
  effect,
  inject,
  signal
} from '@angular/core';
import { AuthService } from '../auth/auth';

@Directive({
  selector: '[appHasPermission]',
  standalone: true
})
export class HasPermissionDirective {
  private readonly auth = inject(AuthService);
  private readonly templateRef = inject(TemplateRef<unknown>);
  private readonly viewContainer = inject(ViewContainerRef);

  private readonly permissionSig = signal<string | null>(null);
  private isRendered = false;

  constructor() {
    effect(() => {
      const code = this.permissionSig();
      // Se evalúa reactivamente cuando cambia el usuario o el permiso
      const hasPerm = code ? this.auth.hasPermission(code) : true;

      if (hasPerm && !this.isRendered) {
        this.viewContainer.createEmbeddedView(this.templateRef);
        this.isRendered = true;
      } else if (!hasPerm && this.isRendered) {
        this.viewContainer.clear();
        this.isRendered = false;
      }
    });
  }

  @Input('appHasPermission')
  set permission(code: string | null) {
    this.permissionSig.set(code);
  }
}
