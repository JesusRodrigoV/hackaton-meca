import { Injectable, inject } from '@angular/core';
import { ResolveFn } from '@angular/router';

const PUBLIC_STYLES = [
  '/assets/kit/system.css',
  '/assets/kit/ui/base.css',
  '/assets/kit/ui/cards.css',
  '/assets/kit/ui/window/fragment.css',
  '/assets/kit/motion/motion.css',
  '/assets/kit/backgrounds/backgrounds.css',
  '/assets/kit/layout/layout.css',
  '/assets/kit/icons/icon.css',
  '/assets/kit/diagrams/diagram.css',
  '/assets/kit/moments/letters-assemble/moment.css',
  '/assets/page.css',
  '/assets/login.css'
];

@Injectable({ providedIn: 'root' })
export class PublicCssService {
  private links: HTMLLinkElement[] = [];
  private pending: Promise<void> | null = null;

  ensure(): Promise<void> {
    if (this.pending) return this.pending;

    this.pending = Promise.all(
      PUBLIC_STYLES.map((href) => this.load(href))
    ).then(() => undefined);

    return this.pending;
  }

  remove(): void {
    this.links.forEach((link) => link.remove());
    this.links = [];
    this.pending = null;
  }

  private load(href: string): Promise<void> {
    const existing = document.querySelector<HTMLLinkElement>(
      `link[data-exb-public][href="${href}"]`
    );
    if (existing) {
      this.links.push(existing);
      return Promise.resolve();
    }

    return new Promise<void>((resolve) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.dataset['exbPublic'] = '';
      link.onload = () => resolve();
      link.onerror = () => resolve();
      document.head.appendChild(link);
      this.links.push(link);
    });
  }
}

export const publicCssResolver: ResolveFn<boolean> = () =>
  inject(PublicCssService)
    .ensure()
    .then(() => true);
