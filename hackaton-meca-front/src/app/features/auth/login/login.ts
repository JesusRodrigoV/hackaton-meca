import {
  Component,
  OnDestroy,
  afterNextRender,
  inject,
  signal
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { JSEncrypt } from 'jsencrypt';
import { AuthService } from '../../../core/auth/auth';

type LoginStep = 'credentials' | '2fa';

interface LoginResponse {
  access_token?: string;
  token_type?: string;
  step?: string;
  session_token?: string;
  reset_token?: string;
  detail?: unknown;
  message?: unknown;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login implements OnDestroy {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly formBuilder = inject(FormBuilder);

  readonly form = this.formBuilder.nonNullable.group({
    identifier: ['', [Validators.required]],
    password: ['', [Validators.required]],
    code: ['']
  });

  readonly step = signal<LoginStep>('credentials');
  readonly showPassword = signal(false);
  readonly isSubmitting = signal(false);
  readonly errorMessage = signal('');
  readonly infoMessage = signal('');
  readonly sessionToken = signal('');

  readonly recaptchaSiteKey =
    document
      .querySelector<HTMLMetaElement>('meta[name="recaptcha-site-key"]')
      ?.content?.trim() ?? '';

  private recaptchaWidgetId: number | null = null;
  private recaptchaLoading: Promise<void> | null = null;
  private readonly timers: number[] = [];

  constructor() {
    afterNextRender(() => {
      void this.mountRecaptcha();
    });
  }

  ngOnDestroy(): void {
    this.timers.forEach((timer) => window.clearTimeout(timer));
  }

  showError(controlName: 'identifier' | 'password'): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || control.dirty);
  }

  async onSubmit(): Promise<void> {
    this.errorMessage.set('');
    this.infoMessage.set('');

    if (this.step() === '2fa') {
      await this.verifyTwoFactor();
      return;
    }

    if (this.form.controls.identifier.invalid || this.form.controls.password.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const recaptchaToken = this.getRecaptchaToken();
    if (this.recaptchaSiteKey && !recaptchaToken) {
      this.errorMessage.set(
        'Completa la verificación de seguridad antes de ingresar.'
      );
      return;
    }

    this.isSubmitting.set(true);
    const identifier = this.form.controls.identifier.value.trim();

    try {
      const publicKey = await this.fetchPublicKey();
      const encryptedPassword = this.encryptPassword(
        this.form.controls.password.value,
        publicKey
      );

      const response = await fetch('/zooconnect/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        },
        body: JSON.stringify({
          identifier,
          password: encryptedPassword,
          recaptcha_token: recaptchaToken ?? null
        })
      });

      const data = (await this.readJson(response)) as LoginResponse;

      if (!response.ok) {
        this.errorMessage.set(this.messageFor(data, response.status));
        this.resetRecaptcha();
        return;
      }

      if (data.access_token) {
        this.finishLogin(data.access_token, identifier);
        return;
      }

      if (data.step === '2fa_required' && data.session_token) {
        this.sessionToken.set(data.session_token);
        this.step.set('2fa');
        this.form.controls.code.setValue('');
        this.infoMessage.set(
          'Ingresa el código de seis dígitos de tu dispositivo de autenticación.'
        );
        return;
      }

      if (data.reset_token) {
        this.errorMessage.set(
          'Debes cambiar tu contraseña antes de ingresar. Usa el enlace de restablecimiento enviado a tu correo institucional.'
        );
        return;
      }

      this.errorMessage.set(
        'El servidor devolvió una respuesta inesperada. Intenta nuevamente.'
      );
    } catch (error) {
      this.errorMessage.set(this.networkMessage(error));
      this.resetRecaptcha();
    } finally {
      this.isSubmitting.set(false);
    }
  }

  async verifyTwoFactor(): Promise<void> {
    const code = this.form.controls.code.value.trim();
    if (!code) {
      this.form.controls.code.markAsTouched();
      this.errorMessage.set('Ingresa el código de verificación.');
      return;
    }

    if (!this.sessionToken()) {
      this.errorMessage.set(
        'La sesión de verificación expiró. Vuelve a ingresar tu usuario y contraseña.'
      );
      this.backToCredentials();
      return;
    }

    this.isSubmitting.set(true);

    try {
      const response = await fetch('/zooconnect/auth/2fa/verify-login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        },
        body: JSON.stringify({
          session_token: this.sessionToken(),
          code
        })
      });

      const data = (await this.readJson(response)) as LoginResponse;

      if (!response.ok) {
        this.errorMessage.set(this.messageFor(data, response.status));
        return;
      }

      if (data.access_token) {
        this.finishLogin(
          data.access_token,
          this.form.controls.identifier.value.trim()
        );
        return;
      }

      if (data.reset_token) {
        this.errorMessage.set(
          'Debes cambiar tu contraseña antes de ingresar. Usa el enlace de restablecimiento enviado a tu correo institucional.'
        );
        return;
      }

      this.errorMessage.set(
        'El código no fue aceptado. Revisa el dispositivo e intenta nuevamente.'
      );
    } catch (error) {
      this.errorMessage.set(this.networkMessage(error));
    } finally {
      this.isSubmitting.set(false);
    }
  }

  backToCredentials(): void {
    this.step.set('credentials');
    this.sessionToken.set('');
    this.form.controls.code.setValue('');
    this.errorMessage.set('');
    this.infoMessage.set('');
    this.resetRecaptcha();
  }

  private finishLogin(token: string, identifier: string): void {
    this.authService.setSession(token, identifier);
    void this.router.navigate(['/dashboard']);
  }

  private async fetchPublicKey(): Promise<string> {
    const response = await fetch('/zooconnect/auth/public-key', {
      headers: { Accept: 'application/json' }
    });

    if (!response.ok) {
      throw new Error(
        'No se pudo obtener la llave de seguridad del servidor.'
      );
    }

    const data = (await response.json()) as { public_key?: string };
    if (!data.public_key) {
      throw new Error('El servidor no devolvió una llave de seguridad válida.');
    }

    return data.public_key;
  }

  private encryptPassword(password: string, publicKey: string): string {
    const encryptor = new JSEncrypt();
    encryptor.setPublicKey(publicKey);
    const encrypted = encryptor.encrypt(password);

    if (!encrypted) {
      throw new Error('No se pudo cifrar la contraseña en este navegador.');
    }

    return encrypted;
  }

  private async readJson(response: Response): Promise<LoginResponse> {
    try {
      return (await response.json()) as LoginResponse;
    } catch {
      return {};
    }
  }

  private messageFor(data: LoginResponse, status: number): string {
    const detail = this.detailOf(data);
    const lower = detail.toLowerCase();

    if (status === 403) {
      if (lower.includes('seguridad')) {
        return 'El acceso requiere la verificación de seguridad. La clave de reCAPTCHA no está configurada en este entorno.';
      }
      return detail || 'No tienes permiso para ingresar al sistema.';
    }

    if (status === 401) {
      return 'Credenciales inválidas. Revisa tu usuario y contraseña.';
    }

    if (status === 429) {
      return 'Demasiados intentos. Espera un minuto y vuelve a intentar.';
    }

    if (status === 422) {
      return 'Revisa los datos ingresados e intenta nuevamente.';
    }

    if (status === 400) {
      return detail || 'No se pudo completar el inicio de sesión.';
    }

    return (
      detail ||
      `No se pudo completar el inicio de sesión (código ${status}).`
    );
  }

  private detailOf(data: LoginResponse): string {
    const detail =
      (data as Record<string, unknown>)['detail'] ??
      (data as Record<string, unknown>)['message'] ??
      (data as Record<string, unknown>)['error'];

    if (typeof detail === 'string') return detail;

    if (detail && typeof detail === 'object') {
      const record = detail as Record<string, unknown>;
      const message = record['message'] ?? record['status'];
      if (typeof message === 'string') return message;
    }

    return '';
  }

  private networkMessage(error: unknown): string {
    if (error instanceof TypeError) {
      return 'No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.';
    }

    if (error instanceof Error && error.message) {
      return error.message;
    }

    return 'No se pudo completar el inicio de sesión. Intenta nuevamente.';
  }

  private async mountRecaptcha(): Promise<void> {
    if (!this.recaptchaSiteKey) return;

    try {
      await this.loadRecaptcha();
    } catch {
      // El formulario muestra el motivo al intentar ingresar sin token.
    }
  }

  private loadRecaptcha(): Promise<void> {
    if (!this.recaptchaSiteKey) return Promise.resolve();
    if (this.recaptchaLoading) return this.recaptchaLoading;

    this.recaptchaLoading = new Promise<void>((resolve, reject) => {
      const existing = document.querySelector<HTMLScriptElement>(
        'script[data-exb-recaptcha]'
      );

      if (existing) {
        this.waitForRecaptcha(resolve, reject);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://www.google.com/recaptcha/api.js?render=explicit';
      script.async = true;
      script.defer = true;
      script.dataset['exbRecaptcha'] = '';
      script.onload = () => this.waitForRecaptcha(resolve, reject);
      script.onerror = () =>
        reject(new Error('No se pudo cargar la verificación de seguridad.'));
      document.head.appendChild(script);
    });

    return this.recaptchaLoading;
  }

  private waitForRecaptcha(
    resolve: () => void,
    reject: (error: Error) => void
  ): void {
    let attempts = 0;

    const tick = (): void => {
      const grecaptcha = (
        window as unknown as {
          grecaptcha?: {
            render?: (element: HTMLElement, options: object) => number;
            getResponse?: (widgetId: number) => string;
            reset?: (widgetId: number) => void;
          };
        }
      ).grecaptcha;

      if (grecaptcha?.render) {
        try {
          if (this.recaptchaWidgetId === null) {
            const container = document.getElementById('recaptcha-container');
            if (!container) {
              this.schedule(tick, 100);
              return;
            }

            this.recaptchaWidgetId = grecaptcha.render(container, {
              sitekey: this.recaptchaSiteKey,
              theme: 'dark'
            });
          }
          resolve();
        } catch (error) {
          reject(
            error instanceof Error
              ? error
              : new Error('No se pudo iniciar la verificación de seguridad.')
          );
        }
        return;
      }

      attempts += 1;
      if (attempts > 60) {
        reject(new Error('No se pudo cargar la verificación de seguridad.'));
        return;
      }

      this.schedule(tick, 100);
    };

    tick();
  }

  private schedule(callback: () => void, delay: number): void {
    const timer = window.setTimeout(callback, delay);
    this.timers.push(timer);
  }

  private getRecaptchaToken(): string | undefined {
    if (!this.recaptchaSiteKey || this.recaptchaWidgetId === null) {
      return undefined;
    }

    const grecaptcha = (
      window as unknown as {
        grecaptcha?: { getResponse?: (widgetId: number) => string };
      }
    ).grecaptcha;

    return grecaptcha?.getResponse?.(this.recaptchaWidgetId) || undefined;
  }

  private resetRecaptcha(): void {
    if (this.recaptchaWidgetId === null) return;

    const grecaptcha = (
      window as unknown as {
        grecaptcha?: { reset?: (widgetId: number) => void };
      }
    ).grecaptcha;

    grecaptcha?.reset?.(this.recaptchaWidgetId);
  }
}
