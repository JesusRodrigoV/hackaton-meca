import { Component, input, CUSTOM_ELEMENTS_SCHEMA, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `
    <box-icon
      [attr.name]="name()"
      [attr.type]="type() === 'regular' ? null : type()"
      [attr.color]="color()"
      [attr.size]="size()"
      [attr.animation]="animation()"
    ></box-icon>
  `,
  styles: [`
    :host {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      vertical-align: middle;
      line-height: 0;
    }
    box-icon {
      display: inline-block;
      vertical-align: middle;
    }
  `],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BoxIconComponent {
  name = input.required<string>();
  type = input<'regular' | 'solid' | 'logo'>('regular');
  color = input<string>('currentColor');
  size = input<string>('sm'); // 'xs', 'sm', 'md', 'lg' o tamaño como '24px'
  animation = input<string | null>(null);
}
