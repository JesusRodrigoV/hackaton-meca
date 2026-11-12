import {
  Component,
  inject,
  computed,
  afterNextRender,
  ElementRef,
  viewChild,
  OnInit,
  OnDestroy
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FinancialService } from '../../core/services/financial';
import { AuthService } from '../../core/auth/auth';
import { BoxIconComponent } from '../../shared/components/box-icon/box-icon';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, RouterLink, DecimalPipe, BoxIconComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit, OnDestroy {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly canvasFinanciador = viewChild<ElementRef<HTMLCanvasElement>>('chartFinanciador');
  readonly canvasRegiones = viewChild<ElementRef<HTMLCanvasElement>>('chartRegiones');

  private chartFinanciadorInstance: Chart | null = null;
  private chartRegionesInstance: Chart | null = null;

  readonly kpis = this.financialService.kpis;
  readonly techos = this.financialService.techos;

  // Filtrado de partidas críticas
  readonly partidasCriticas = computed(() => {
    return this.techos().filter(
      t => t.estado === 'SOBREEJECUCION' || t.estado === 'EJEC_SIN_PRESUP' || t.porcentajeEjecucion > 90
    );
  });

  constructor() {
    afterNextRender(() => {
      this.initCharts();
    });
  }

  ngOnInit(): void {
    this.financialService.cargarTechosApi();
  }

  private initCharts(): void {
    const elFin = this.canvasFinanciador()?.nativeElement;
    if (elFin) {
      this.chartFinanciadorInstance = new Chart(elFin, {
        type: 'doughnut',
        data: {
          labels: ['CATALYST 18', 'CEL (Comunidad)', 'KJCF (Fundación)'],
          datasets: [
            {
              data: [345000, 145000, 90000],
              backgroundColor: ['#2b255c', '#00923d', '#ecc562'],
              borderWidth: 2,
              borderColor: '#ffffff'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                boxWidth: 12,
                padding: 14,
                font: { family: 'Inter', size: 12 }
              }
            }
          },
          cutout: '72%'
        }
      });
    }

    const elReg = this.canvasRegiones()?.nativeElement;
    if (elReg) {
      this.chartRegionesInstance = new Chart(elReg, {
        type: 'bar',
        data: {
          labels: ['La Paz', 'Santa Cruz', 'Cochabamba', 'Nacional'],
          datasets: [
            {
              label: 'Vigente (BOB)',
              data: [300000, 105000, 90000, 85000],
              backgroundColor: '#2b255c',
              borderRadius: 4
            },
            {
              label: 'Ejecutado (BOB)',
              data: [220300, 112300, 68400, 38900],
              backgroundColor: '#00923d',
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                boxWidth: 12,
                padding: 14,
                font: { family: 'Inter', size: 12 }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: value => Number(value).toLocaleString() + ' Bs'
              },
              grid: {
                color: '#f1f5f9'
              }
            },
            x: {
              grid: {
                display: false
              }
            }
          }
        }
      });
    }
  }

  ngOnDestroy(): void {
    if (this.chartFinanciadorInstance) {
      this.chartFinanciadorInstance.destroy();
    }
    if (this.chartRegionesInstance) {
      this.chartRegionesInstance.destroy();
    }
  }
}
