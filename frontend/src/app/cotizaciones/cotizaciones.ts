import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { SidebarComponent } from '../shared/sidebar/sidebar';

@Component({
  selector: 'app-cotizaciones',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule, FormsModule, SidebarComponent],
  templateUrl: './cotizaciones.html'
})
export class Cotizaciones implements OnInit {
  private apiUrl = 'http://localhost:5000/api/cotizaciones';

  sidebarAbierta: boolean = true;
  usuarioLogueado: any = null;

  cotizaciones: any[] = [];
  cotizacionesFiltradas: any[] = [];
  resumen: any = {
    cotizaciones_activas: 0,
    monto_cotizado: 0,
    pedidos_cerrados: 0,
    monto_cerrado: 0,
    tasa_conversion: 0
  };

  // Catálogos para el formulario de Nueva Cotización
  clientes: any[] = [];
  vendedores: any[] = [];
  productos: any[] = [];

  // Filtros
  filtroEstado: string = 'TODOS';
  textoBusqueda: string = '';

  // Alertas y modales
  mensajeAlerta: string = '';
  tipoAlerta: 'exito' | 'error' = 'exito';
  modalNuevaAbierto: boolean = false;
  modalDetalleAbierto: boolean = false;
  cotizacionSeleccionada: any = null;

  // Formulario de nueva cotización
  nuevaCotizacion = {
    id_cliente: null as number | null,
    id_vendedor: null as number | null
  };
  productoSeleccionadoId: number | null = null;
  cantidadSeleccionada: number = 1;
  itemsNuevaCotizacion: Array<{
    id_producto: number;
    nombre: string;
    precio_venta: number;
    cantidad: number;
    subtotal: number;
  }> = [];

  constructor(
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const datosGuardados = localStorage.getItem('usuario_atelier');
    if (datosGuardados) {
      this.usuarioLogueado = JSON.parse(datosGuardados);
      this.cargarCotizaciones();
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

  cargarCotizaciones(): void {
    this.http.get(this.apiUrl).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.cotizaciones = res.cotizaciones || [];
          this.resumen = res.resumen || this.resumen;
          this.aplicarFiltros();
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        console.error('Error al cargar cotizaciones:', err);
        this.mostrarMensaje('No se pudo conectar con Flask para cargar cotizaciones.', 'error');
      }
    });
  }

  cargarCatalogos(): void {
    this.http.get(`${this.apiUrl}/catalogos`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.clientes = res.clientes || [];
          this.vendedores = res.vendedores || [];
          this.productos = res.productos || [];
          if (this.clientes.length > 0 && !this.nuevaCotizacion.id_cliente) {
            this.nuevaCotizacion.id_cliente = this.clientes[0].id_usuario;
          }
          if (this.productos.length > 0 && !this.productoSeleccionadoId) {
            this.productoSeleccionadoId = this.productos[0].id_producto;
          }
          this.cdr.detectChanges();
        }
      },
      error: (err) => console.error('Error al cargar catálogos:', err)
    });
  }

  // --- FILTROS ---
  seleccionarEstado(estado: string): void {
    this.filtroEstado = estado;
    this.aplicarFiltros();
  }

  aplicarFiltros(): void {
    const busqueda = this.textoBusqueda.toLowerCase().trim();
    this.cotizacionesFiltradas = this.cotizaciones.filter((c) => {
      const coincideEstado =
        this.filtroEstado === 'TODOS' || c.estado_pedido === this.filtroEstado;
      const coincideTexto =
        !busqueda ||
        String(c.id_pedido).includes(busqueda) ||
        (c.cliente_nombre || '').toLowerCase().includes(busqueda) ||
        (c.vendedor_nombre || '').toLowerCase().includes(busqueda);
      return coincideEstado && coincideTexto;
    });
  }

  contarPorEstado(estado: string): number {
    if (estado === 'TODOS') return this.cotizaciones.length;
    return this.cotizaciones.filter((c) => c.estado_pedido === estado).length;
  }

  claseBadgeEstado(estado: string): string {
    switch (estado) {
      case 'Cotizacion':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      case 'Pagado':
        return 'bg-blue-50 text-blue-700 border border-blue-200';
      case 'En Produccion':
        return 'bg-purple-50 text-purple-700 border border-purple-200';
      case 'Listo Envio':
        return 'bg-cyan-50 text-cyan-700 border border-cyan-200';
      case 'Entregado':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  }

  // --- CREAR NUEVA COTIZACIÓN ---
  abrirModalNueva(): void {
    this.itemsNuevaCotizacion = [];
    this.cantidadSeleccionada = 1;
    this.nuevaCotizacion = {
      id_cliente: this.clientes[0]?.id_usuario || null,
      id_vendedor: this.usuarioLogueado?.id_usuario || this.vendedores[0]?.id_usuario || null
    };
    this.productoSeleccionadoId = this.productos[0]?.id_producto || null;
    this.modalNuevaAbierto = true;
  }

  agregarProductoACotizacion(): void {
    if (!this.productoSeleccionadoId || this.cantidadSeleccionada <= 0) return;
    const prod = this.productos.find((p) => p.id_producto === Number(this.productoSeleccionadoId));
    if (!prod) return;

    const existente = this.itemsNuevaCotizacion.find((i) => i.id_producto === prod.id_producto);
    if (existente) {
      existente.cantidad += Number(this.cantidadSeleccionada);
      existente.subtotal = Number(prod.precio_venta) * existente.cantidad;
    } else {
      const cant = Number(this.cantidadSeleccionada);
      this.itemsNuevaCotizacion.push({
        id_producto: prod.id_producto,
        nombre: prod.nombre,
        precio_venta: Number(prod.precio_venta),
        cantidad: cant,
        subtotal: Number(prod.precio_venta) * cant
      });
    }
    this.cantidadSeleccionada = 1;
  }

  quitarProducto(index: number): void {
    this.itemsNuevaCotizacion.splice(index, 1);
  }

  get totalNuevaCotizacion(): number {
    return this.itemsNuevaCotizacion.reduce((acc, it) => acc + it.subtotal, 0);
  }

  guardarCotizacion(): void {
    if (!this.nuevaCotizacion.id_cliente) {
      this.mostrarMensaje('Selecciona un cliente para la cotización.', 'error');
      return;
    }
    if (this.itemsNuevaCotizacion.length === 0) {
      this.mostrarMensaje('Agrega al menos un mueble antes de guardar.', 'error');
      return;
    }

    const payload = {
      id_cliente: this.nuevaCotizacion.id_cliente,
      id_vendedor: this.nuevaCotizacion.id_vendedor,
      items: this.itemsNuevaCotizacion.map((i) => ({
        id_producto: i.id_producto,
        cantidad: i.cantidad
      }))
    };

    this.http.post(this.apiUrl, payload).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalNuevaAbierto = false;
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarCotizaciones();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'Error al guardar la cotización.', 'error');
      }
    });
  }

  // --- APROBAR / ELIMINAR / DETALLE ---
  aprobarCotizacion(cot: any): void {
    if (!confirm(`¿Convertir la Cotización #${cot.id_pedido} a pedido Pagado y enviarla al taller?`)) {
      return;
    }
    this.http.put(`${this.apiUrl}/${cot.id_pedido}/aprobar`, {}).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalDetalleAbierto = false;
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarCotizaciones();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'Error al aprobar cotización.', 'error');
      }
    });
  }

  eliminarCotizacion(cot: any): void {
    if (!confirm(`¿Eliminar la Cotización #${cot.id_pedido}? Esta acción no se puede deshacer.`)) {
      return;
    }
    this.http.delete(`${this.apiUrl}/${cot.id_pedido}`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mostrarMensaje(res.mensaje, 'exito');
          this.cargarCotizaciones();
        }
      },
      error: (err) => {
        this.mostrarMensaje(err.error?.mensaje || 'No se pudo eliminar la cotización.', 'error');
      }
    });
  }

  verDetalle(cot: any): void {
    this.cotizacionSeleccionada = cot;
    this.modalDetalleAbierto = true;
  }

  exportarCSV(): void {
    const encabezados = ['Folio,Fecha,Cliente,Vendedor,Estado,Total MXN'];
    const filas = this.cotizacionesFiltradas.map(
      (c) =>
        `#${c.id_pedido},"${c.fecha_pedido}","${c.cliente_nombre}","${c.vendedor_nombre}",${c.estado_pedido},${c.total}`
    );
    const csv = '\uFEFF' + [encabezados, ...filas].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Cotizaciones_Atelier_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}