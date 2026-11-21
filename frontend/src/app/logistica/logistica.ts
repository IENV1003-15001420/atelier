import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-logistica',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule, FormsModule],
  templateUrl: './logistica.html',
  styleUrl: './logistica.css'
})
export class Logistica implements OnInit {
  private apiUrl = 'http://localhost:5000/api/logistica';

  sidebarAbierta: boolean = true;
  usuarioLogueado: any = null;

  envios: any[] = [];
  enviosFiltrados: any[] = [];
  estadosDisponibles: string[] = ['Programado', 'En Ruta', 'Instalando', 'Finalizado'];
  estadoFinal: string = 'Finalizado';

  resumen: any = {
    programados: 0,
    en_curso: 0,
    finalizados: 0,
    pendientes_programar: 0
  };

  // Catálogos
  choferes: any[] = [];
  instaladores: any[] = [];
  pedidos: any[] = [];

  // Filtros
  filtroEstado: string = 'TODOS';
  textoBusqueda: string = '';

  // Alertas y Modales
  mensajeAlerta: string = '';
  tipoAlerta: 'exito' | 'error' = 'exito';
  modalNuevoAbierto: boolean = false;
  modalEditarAbierto: boolean = false;

  // Formulario Nuevo Envío
  nuevoEnvio = {
    id_pedido: null as number | null,
    id_chofer: null as number | null,
    id_instalador: null as number | null,
    direccion_entrega: '',
    fecha_programada: ''
  };

  // Formulario Editar / Avanzar Estado
  envioEditando: any = null;

  constructor(
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const datosGuardados = localStorage.getItem('usuario_atelier');
    if (datosGuardados) {
      this.usuarioLogueado = JSON.parse(datosGuardados);
      this.cargarEnvios();
      this.cargarCatalogos();
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

  cargarEnvios(): void {
    this.http.get(this.apiUrl).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.envios = res.envios || [];
          this.resumen = res.resumen || this.resumen;
          if (res.estados?.length) this.estadosDisponibles = res.estados;
          if (res.estado_final) this.estadoFinal = res.estado_final;
          this.aplicarFiltros();
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        console.error('Error al cargar logística:', err);
        this.mostrarMensaje('No se pudo conectar con Flask en el puerto 5000.', 'error');
      }
    });
  }

  cargarCatalogos(): void {
    this.http.get(`${this.apiUrl}/catalogos`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.choferes = res.choferes || [];
          this.instaladores = res.instaladores || [];
          this.pedidos = res.pedidos || [];
          if (res.estados?.length) this.estadosDisponibles = res.estados;
          this.cdr.detectChanges();
        }
      },
      error: (err) => console.error('Error al cargar catálogos de logística:', err)
    });
  }

  // --- FILTROS ---
  seleccionarEstado(estado: string): void {
    this.filtroEstado = estado;
    this.aplicarFiltros();
  }

  aplicarFiltros(): void {
    const q = this.textoBusqueda.toLowerCase().trim();
    this.enviosFiltrados = this.envios.filter((e) => {
      const coincideEstado =
        this.filtroEstado === 'TODOS' || e.estado_entrega === this.filtroEstado;
      const coincideTexto =
        !q ||
        String(e.id_envio).includes(q) ||
        String(e.id_pedido).includes(q) ||
        (e.cliente_nombre || '').toLowerCase().includes(q) ||
        (e.direccion_entrega || '').toLowerCase().includes(q) ||
        (e.chofer_nombre || '').toLowerCase().includes(q) ||
        (e.instalador_nombre || '').toLowerCase().includes(q);
      return coincideEstado && coincideTexto;
    });
  }

  contarPorEstado(estado: string): number {
    if (estado === 'TODOS') return this.envios.length;
    return this.envios.filter((e) => e.estado_entrega === estado).length;
  }

  claseBadgeEstado(estado: string): string {
    if (estado === 'Programado') return 'bg-amber-50 text-amber-700 border border-amber-200';
    if (estado === 'En Ruta') return 'bg-blue-50 text-blue-700 border border-blue-200';
    if (estado === 'Instalando') return 'bg-purple-50 text-purple-700 border border-purple-200';
    return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
  }

  // --- PROGRAMAR NUEVO ENVÍO ---
  abrirModalNuevo(): void {
    const primerPedido = this.pedidos[0];
    this.nuevoEnvio = {
      id_pedido: primerPedido?.id_pedido || null,
      id_chofer: this.choferes[0]?.id_usuario || null,
      id_instalador: this.instaladores[0]?.id_usuario || null,
      direccion_entrega: primerPedido?.cliente_direccion || '',
      fecha_programada: new Date(Date.now() + 86400000).toISOString().slice(0, 16)
    };
    this.modalNuevoAbierto = true;
  }

  alCambiarPedido(): void {
    const ped = this.pedidos.find((p) => p.id_pedido === Number(this.nuevoEnvio.id_pedido));
    if (ped?.cliente_direccion) {
      this.nuevoEnvio.direccion_entrega = ped.cliente_direccion;
    }
  }

  guardarNuevoEnvio(): void {
    if (!this.nuevoEnvio.id_pedido) {
      this.mostrarMensaje('Selecciona un pedido para programar la entrega.', 'error');
      return;
    }
    if (!this.nuevoEnvio.direccion_entrega.trim()) {
      this.mostrarMensaje('Ingresa la dirección de entrega.', 'error');
      return;
    }

    this.http.post(this.apiUrl, this.nuevoEnvio).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalNuevoAbierto = false;
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarEnvios();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'Error al programar envío.', 'error');
      }
    });
  }

  // --- ACTUALIZAR ESTADO / EVIDENCIA ---
  abrirModalEditar(env: any): void {
    this.envioEditando = {
      id_envio: env.id_envio,
      id_pedido: env.id_pedido,
      cliente_nombre: env.cliente_nombre,
      id_chofer: env.id_chofer,
      id_instalador: env.id_instalador,
      direccion_entrega: env.direccion_entrega,
      fecha_programada: env.fecha_input || '',
      estado_entrega: env.estado_entrega,
      evidencia_foto_url: env.evidencia_foto_url || ''
    };
    this.modalEditarAbierto = true;
  }

  guardarActualizacion(): void {
    if (!this.envioEditando) return;
    this.http.put(`${this.apiUrl}/${this.envioEditando.id_envio}`, this.envioEditando).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalEditarAbierto = false;
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarEnvios();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'No se pudo actualizar el envío.', 'error');
      }
    });
  }

  eliminarEnvio(env: any): void {
    if (!confirm(`¿Eliminar el envío #${env.id_envio} del pedido #${env.id_pedido}?`)) return;
    this.http.delete(`${this.apiUrl}/${env.id_envio}`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarEnvios();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'Error al eliminar el envío.', 'error');
      }
    });
  }

  exportarCSV(): void {
    const encabezados = ['Envio,Pedido,Cliente,Direccion,Chofer,Instalador,Fecha,Estado'];
    const filas = this.enviosFiltrados.map(
      (e) =>
        `#${e.id_envio},#${e.id_pedido},"${e.cliente_nombre}","${e.direccion_entrega}","${e.chofer_nombre}","${e.instalador_nombre}","${e.fecha_programada}",${e.estado_entrega}`
    );
    const csv = '\uFEFF' + [encabezados, ...filas].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Logistica_Atelier_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}