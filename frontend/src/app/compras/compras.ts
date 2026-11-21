import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';
import { SidebarComponent } from '../shared/sidebar/sidebar';

@Component({
  selector: 'app-compras',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, SidebarComponent],
  templateUrl: './compras.html'
})
export class ComprasComponent implements OnInit {
  private readonly api = 'http://localhost:5000/api';

  sidebarAbierta = true;
  usuario: any = null;

  requisiciones: any[] = [];
  proveedores: any[] = [];
  materiales: any[] = [];
  resumen = {
    total_requisiciones: 0,
    presupuesto_pendiente: 0,
    requisiciones_pendientes: 0,
    por_aprobar: 0,
    recibidas: 0
  };

  busqueda = '';
  filtroEstado = 'TODOS';
  cargando = false;
  guardando = false;
  procesandoId: number | null = null;
  mensaje = '';
  error = '';

  nuevaRequisicion = {
    id_proveedor: null as number | null,
    id_material: null as number | null,
    cantidad: 1,
    costo_unitario: 0
  };

  constructor(
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const datos = localStorage.getItem('usuario_atelier');
    if (datos) {
      this.usuario = JSON.parse(datos);
    }
    this.refrescarVista();
    this.cargarDatos();
  }

  refrescarVista(): void {
    this.cdr.detectChanges();
  }

  toggleSidebar(): void {
    this.sidebarAbierta = !this.sidebarAbierta;
    this.refrescarVista();
  }

  cargarDatos(): void {
    this.cargando = true;
    this.error = '';

    forkJoin({
      requisiciones: this.http.get<any>(`${this.api}/almacen/requisiciones`),
      proveedores: this.http.get<any>(`${this.api}/almacen/proveedores`),
      materiales: this.http.get<any>(`${this.api}/almacen/materiales`)
    }).subscribe({
      next: ({ requisiciones, proveedores, materiales }) => {
        this.requisiciones = requisiciones.requisiciones || [];
        this.resumen = requisiciones.resumen || this.resumen;
        this.proveedores = proveedores.proveedores || [];
        this.materiales = materiales.materiales || [];
        this.cargando = false;
        this.refrescarVista();
      },
      error: (err) => {
        this.cargando = false;
        this.error = err.error?.message || 'No fue posible cargar las requisiciones.';
        this.refrescarVista();
      }
    });
  }

  get requisicionesFiltradas(): any[] {
    const texto = this.busqueda.trim().toLowerCase();

    return this.requisiciones.filter((r) => {
      const coincideTexto =
        !texto ||
        (r.material || '').toLowerCase().includes(texto) ||
        (r.proveedor || '').toLowerCase().includes(texto) ||
        (r.solicitante || '').toLowerCase().includes(texto) ||
        String(r.id_compra).includes(texto);

      const coincideEstado = this.filtroEstado === 'TODOS' || r.estado === this.filtroEstado;
      return coincideTexto && coincideEstado;
    });
  }

  get costoEstimado(): number {
    return Number((Number(this.nuevaRequisicion.cantidad || 0) * Number(this.nuevaRequisicion.costo_unitario || 0)).toFixed(2));
  }

  seleccionarMaterial(): void {
    const material = this.materiales.find((m) => m.id_material === Number(this.nuevaRequisicion.id_material));
    if (material) {
      this.nuevaRequisicion.costo_unitario = material.costo_unitario;
    }
    this.refrescarVista();
  }

  crearRequisicion(): void {
    if (!this.nuevaRequisicion.id_proveedor || !this.nuevaRequisicion.id_material) {
      this.error = 'Selecciona un proveedor y un insumo para crear la requisición.';
      this.refrescarVista();
      return;
    }
    if (Number(this.nuevaRequisicion.cantidad) <= 0) {
      this.error = 'La cantidad solicitada debe ser mayor a cero.';
      this.refrescarVista();
      return;
    }

    this.guardando = true;
    this.error = '';

    const payload = {
      id_proveedor: Number(this.nuevaRequisicion.id_proveedor),
      id_material: Number(this.nuevaRequisicion.id_material),
      id_usuario_solicita: Number(this.usuario?.id_usuario || 4),
      cantidad: Number(this.nuevaRequisicion.cantidad),
      costo_unitario: Number(this.nuevaRequisicion.costo_unitario)
    };

    this.http.post<any>(`${this.api}/almacen/requisiciones`, payload).subscribe({
      next: (res) => {
        this.guardando = false;
        this.mensaje = `${res.message} · Importe: $${Number(res.costo_total).toLocaleString('es-MX')} MXN`;
        this.nuevaRequisicion = { id_proveedor: null, id_material: null, cantidad: 1, costo_unitario: 0 };
        this.refrescarVista();
        this.cargarDatos();
        setTimeout(() => {
          this.mensaje = '';
          this.refrescarVista();
        }, 4500);
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.message || 'Error al crear la requisición.';
        this.refrescarVista();
      }
    });
  }

  cambiarEstado(requisicion: any, estado: string): void {
    if (estado === 'Recibido') {
      const confirmar = confirm(
        `¿Confirmar la entrada de ${requisicion.cantidad} ${requisicion.unidad_medida} de "${requisicion.material}"?\n\nEsta acción sumará la cantidad al stock actual.`
      );
      if (!confirmar) return;
    }

    this.procesandoId = requisicion.id_compra;
    this.error = '';

    this.http.put<any>(`${this.api}/almacen/requisiciones/${requisicion.id_compra}/estado`, { estado }).subscribe({
      next: (res) => {
        this.procesandoId = null;
        this.mensaje = res.stock_actualizado
          ? `${res.message}. Stock actualizado a ${res.stock_nuevo} unidades.`
          : res.message;
        this.refrescarVista();
        this.cargarDatos();
        setTimeout(() => {
          this.mensaje = '';
          this.refrescarVista();
        }, 4500);
      },
      error: (err) => {
        this.procesandoId = null;
        this.error = err.error?.message || 'No fue posible actualizar el estado.';
        this.refrescarVista();
      }
    });
  }

  claseEstado(estado: string): string {
    if (estado === 'Recibido') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (estado === 'Aprobado') return 'bg-blue-50 text-blue-700 border-blue-200';
    if (estado === 'Cancelado') return 'bg-red-50 text-red-700 border-red-200';
    return 'bg-amber-50 text-amber-700 border-amber-200';
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}