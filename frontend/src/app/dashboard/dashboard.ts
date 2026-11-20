import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, HttpClientModule, RouterModule],
  templateUrl: './dashboard.html'
})
export class DashboardComponent implements OnInit {
  @ViewChild('graficaVentas') graficaCanvas!: ElementRef;
  chart: any;
  usuario: any = null;
  
  // Variables de datos
  ventasMes: number = 0;
  proyectosActivos: number = 0;
  alertasStock: number = 0;

  // Variable para controlar la barra lateral
  sidebarAbierta: boolean = true;

  constructor(private router: Router, private http: HttpClient) {}

  ngOnInit() {
    const datosGuardados = localStorage.getItem('usuario_atelier');
    if (datosGuardados) {
      this.usuario = JSON.parse(datosGuardados);
      this.cargarDatosDashboard();
    } else {
      this.router.navigate(['/login']);
    }
  }

  // Función para abrir/cerrar la barra lateral
  toggleSidebar() {
    this.sidebarAbierta = !this.sidebarAbierta;
    // Redibujar la gráfica un instante después de la animación para que se ajuste al nuevo ancho
    setTimeout(() => {
      if (this.chart) this.chart.resize();
    }, 300);
  }

  cargarDatosDashboard() {
    this.http.get('http://localhost:5000/api/dashboard').subscribe({
      next: (res: any) => {
        if (res.success) {
          this.ventasMes = res.ventas_mes;
          this.proyectosActivos = res.proyectos_activos;
          this.alertasStock = res.alertas_stock;

          // Damos un pequeño respiro a Angular para que renderice el canvas antes de dibujar
          setTimeout(() => {
            this.renderizarGrafica(res.grafica.meses, res.grafica.ventas, res.grafica.gastos);
          }, 100);
        }
      },
      error: (err) => console.error('Error al conectar con Flask:', err)
    });
  }

  renderizarGrafica(meses: string[], ventas: number[], gastos: number[]) {
    if (!this.graficaCanvas) return;
    if (this.chart) this.chart.destroy();

    this.chart = new Chart(this.graficaCanvas.nativeElement, {
      data: {
        labels: meses,
        datasets: [
          {
            type: 'line', label: 'Tendencia', data: ventas,
            borderColor: '#5c4938', borderWidth: 2, tension: 0.2, pointRadius: 3
          },
          {
            type: 'bar', label: 'Ventas (MXN)', data: ventas,
            backgroundColor: '#6b1d24', borderRadius: 4, barPercentage: 0.6
          },
          {
            type: 'bar', label: 'Gasto', data: gastos,
            backgroundColor: '#b8c7d9', borderRadius: 4, barPercentage: 0.6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { display: false, beginAtZero: true }
        }
      }
    });
  }

  cerrarSesion() {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}