import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-resenas',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule, FormsModule],
  templateUrl: './resenas.html',
  styleUrl: './resenas.css'
})
export class Resenas implements OnInit {
  private apiUrl = 'http://localhost:5000/api/resenas';

  sidebarAbierta: boolean = true;
  usuarioLogueado: any = null;

  estrellas: number[] = [1, 2, 3, 4, 5];
  resenas: any[] = [];
  resenasFiltradas: any[] = [];
  resumen: any = {
    promedio_calificacion: 0,
    total_resenas: 0,
    pendientes_evaluar: 0,
    tasa_satisfaccion: 0
  };

  // Filtros
  filtroTipo: string = 'TODOS';
  textoBusqueda: string = '';

  // Alertas y Modal
  mensajeAlerta: string = '';
  tipoAlerta: 'exito' | 'error' = 'exito';
  modalEvaluarAbierto: boolean = false;
  resenaEditando: any = null;

  constructor(
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const datosGuardados = localStorage.getItem('usuario_atelier');
    if (datosGuardados) {
      this.usuarioLogueado = JSON.parse(datosGuardados);
      this.cargarResenas();
    } else {
      this.router.navigate(['/login']);
    }
  }

  get inicialesUsuario(): string {
    const nombre = this.usuarioLogueado?.nombre || 'Admin General';
    const partes = nombre.trim().split(/\s+/);
    return (partes[0][0] + (partes[1]?.[0] || '')).toUpperCase();
  }

  toggleSidebar(): void {
    this.sidebarAbierta = !this.sidebarAbierta;
  }

  mostrarMensaje(texto: string, tipo: 'exito' | 'error' = 'exito'): void {
    this.mensajeAlerta = texto;
    this.tipoAlerta = tipo;
    this.cdr.detectChanges();
  }

  cargarResenas(): void {
    this.http.get(this.apiUrl).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.resenas = res.resenas || [];
          this.resumen = res.resumen || this.resumen;
          this.aplicarFiltros();
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        console.error('Error al cargar reseñas:', err);
        this.mostrarMensaje('No se pudo conectar con Flask en el puerto 5000.', 'error');
      }
    });
  }

  // --- FILTROS ---
  seleccionarFiltro(tipo: string): void {
    this.filtroTipo = tipo;
    this.aplicarFiltros();
  }

  aplicarFiltros(): void {
    const q = this.textoBusqueda.toLowerCase().trim();
    this.resenasFiltradas = this.resenas.filter((r) => {
      let coincideTipo = true;
      if (this.filtroTipo === 'EVALUADAS') {
        coincideTipo = r.calificacion_cliente !== null;
      } else if (this.filtroTipo === 'PENDIENTES') {
        coincideTipo = r.calificacion_cliente === null;
      } else if (this.filtroTipo === 'POSITIVAS') {
        coincideTipo = r.calificacion_cliente !== null && r.calificacion_cliente >= 4;
      } else if (this.filtroTipo === 'ATENCION') {
        coincideTipo = r.calificacion_cliente !== null && r.calificacion_cliente <= 3;
      }

      const coincideTexto =
        !q ||
        String(r.id_pedido).includes(q) ||
        (r.cliente_nombre || '').toLowerCase().includes(q) ||
        (r.producto_nombre || '').toLowerCase().includes(q) ||
        (r.comentario_resena || '').toLowerCase().includes(q);

      return coincideTipo && coincideTexto;
    });
  }

  contarPorFiltro(tipo: string): number {
    if (tipo === 'TODOS') return this.resenas.length;
    if (tipo === 'EVALUADAS') return this.resenas.filter((r) => r.calificacion_cliente !== null).length;
    if (tipo === 'PENDIENTES') return this.resenas.filter((r) => r.calificacion_cliente === null).length;
    if (tipo === 'POSITIVAS') return this.resenas.filter((r) => r.calificacion_cliente !== null && r.calificacion_cliente >= 4).length;
    if (tipo === 'ATENCION') return this.resenas.filter((r) => r.calificacion_cliente !== null && r.calificacion_cliente <= 3).length;
    return 0;
  }

  etiquetaCalificacion(calif: number | null): string {
    if (!calif) return 'Sin evaluar';
    if (calif === 5) return 'Excelente';
    if (calif === 4) return 'Muy bueno';
    if (calif === 3) return 'Regular';
    if (calif === 2) return 'Inconforme';
    return 'Crítico';
  }

  // --- CAPTURAR / EDITAR ENCUESTA ---
  abrirModalEvaluar(item: any): void {
    this.resenaEditando = {
      id_detalle: item.id_detalle,
      id_pedido: item.id_pedido,
      cliente_nombre: item.cliente_nombre,
      producto_nombre: item.producto_nombre,
      cantidad: item.cantidad,
      calificacion_cliente: item.calificacion_cliente || 5,
      comentario_resena: item.comentario_resena || ''
    };
    this.modalEvaluarAbierto = true;
  }

  seleccionarEstrella(valor: number): void {
    if (this.resenaEditando) {
      this.resenaEditando.calificacion_cliente = valor;
    }
  }

  guardarResena(): void {
    if (!this.resenaEditando) return;
    const payload = {
      calificacion_cliente: this.resenaEditando.calificacion_cliente,
      comentario_resena: this.resenaEditando.comentario_resena
    };

    this.http.put(`${this.apiUrl}/${this.resenaEditando.id_detalle}`, payload).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalEvaluarAbierto = false;
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarResenas();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'No se pudo guardar la reseña.', 'error');
      }
    });
  }

  eliminarResena(item: any): void {
    if (!confirm(`¿Borrar la reseña del pedido #${item.id_pedido} (${item.producto_nombre})?`)) return;
    this.http.delete(`${this.apiUrl}/${item.id_detalle}`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarResenas();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'Error al eliminar la reseña.', 'error');
      }
    });
  }

  exportarCSV(): void {
    const encabezados = ['Pedido,Cliente,Producto,Estado Pedido,Calificacion,Comentario,Actualizacion'];
    const filas = this.resenasFiltradas.map(
      (r) =>
        `#${r.id_pedido},"${r.cliente_nombre}","${r.producto_nombre}",${r.estado_pedido},${r.calificacion_cliente ?? 'Pendiente'},"${(r.comentario_resena || '').replace(/"/g, '""')}","${r.fecha_actualizacion}"`
    );
    const csv = '\uFEFF' + [encabezados, ...filas].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Resenas_Atelier_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}