import { Injectable } from '@angular/core';

/**
 * Carga el runtime del kit de diseño sólo en la landing.
 * Cada vista usa una cadena de consulta distinta para que los módulos
 * vuelvan a ejecutarse cuando Angular reconstruye el DOM.
 */
@Injectable({ providedIn: 'root' })
export class KitRuntimeService {
  private view = 0;
  private started = false;

  startLanding(): void {
    const view = ++this.view;
    const boot = () => {
      this.module(`/assets/kit/motion/motion.js?v=${view}`);
      this.module(`/assets/kit/layout/layout.js?v=${view}`);
      this.module(`/assets/kit/moments/moments.js?v=${view}`);
      this.module(`/assets/kit/system.js?v=${view}`);
      this.started = true;
    };

    // Two frames: Angular has painted the view before the kit reads the DOM.
    requestAnimationFrame(() => requestAnimationFrame(boot));
  }

  stopLanding(): void {
    if (!this.started) return;

    document.querySelectorAll<HTMLElement>('[data-fx-mounted]').forEach((element) => {
      const fx = (element as HTMLElement & { __fx?: { destroy?: () => void } }).__fx;
      fx?.destroy?.();
    });

    document.querySelectorAll<HTMLElement>('[data-moment-mounted]').forEach((element) => {
      const moment = (element as HTMLElement & {
        __moment?: { destroy?: () => void };
      }).__moment;
      moment?.destroy?.();
      delete (element as HTMLElement & { __moment?: unknown }).__moment;
      delete (element as HTMLElement & { __momentP?: unknown }).__momentP;
      element.removeAttribute('data-moment-mounted');
    });

    document.body.classList.remove('nav-locked');
    this.started = false;
  }

  private module(src: string): void {
    const script = document.createElement('script');
    script.type = 'module';
    script.src = src;
    script.async = true;
    document.body.appendChild(script);
  }
}
