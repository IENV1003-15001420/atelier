import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';

interface Material {
  id_material: number;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
  stock_minimo: number;
  costo_unitario: number;
  stock_comprometido: number;
  stock_disponible: number;
  valor_inventario: number;
  alerta_stock_bajo: boolean;
  requiere_reorden: boolean;
  porcentaje_vs_minimo: number;
}

interface Movimiento {
  id_compra: number;
  material: string;
  unidad_medida: string;
  cantidad: number;
  costo_total: number;
  estado: string;
  tipo: string;
  proveedor: string;
  solicitante: string;
  fecha: string;
}

@Component({
  selector: 'app-almacen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './almacen.html'
})
export class AlmacenComponent implements OnInit {
  private readonly api = 'http://localhost:5000/api';

  sidebarAbierta = true;
  usuario: any = null;

  materiales: Material[] = [];
  movimientos: Movimiento[] = [];
  resumen = {
    total_materiales: 0,
    unidades_totales: 0,
    valor_inventario: 0,
    alertas_stock_bajo: 0,
    requieren_reorden: 0,
    comprometido_total: 0
  };

  busqueda = '';
  filtro = 'TODOS';
  cargando = false;
  mensaje = '';
  error = '';

  modalNuevoAbierto = false;
  guardando = false;
  nuevoMaterial = {
    nombre: '',
    unidad_medida: 'Piezas',
    stock_actual: 0,
    stock_minimo: 5,
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
      materiales: this.http.get<any>(`${this.api}/almacen/materiales`),
      movimientos: this.http.get<any>(`${this.api}/almacen/movimientos`)
    }).subscribe({
      next: ({ materiales, movimientos }) => {
        this.materiales = materiales.materiales || [];
        this.resumen = materiales.resumen || this.resumen;
        this.movimientos = movimientos.movimientos || [];
        this.cargando = false;
        this.refrescarVista();
      },
      error: (err) => {
        this.cargando = false;
        this.error = err.error?.message || 'No fue posible conectar con el módulo de almacén.';
        this.refrescarVista();
      }
    });
  }

  cambiarFiltro(filtro: string): void {
    this.filtro = filtro;
    this.refrescarVista();
  }

  actualizarBusqueda(): void {
    this.refrescarVista();
  }

  get materialesFiltrados(): Material[] {
    const texto = this.busqueda.trim().toLowerCase();

    return this.materiales.filter((material) => {
      const coincideTexto =
        !texto ||
        material.nombre.toLowerCase().includes(texto) ||
        material.unidad_medida.toLowerCase().includes(texto);

      let coincideFiltro = true;
      if (this.filtro === 'BAJO') coincideFiltro = material.alerta_stock_bajo;
      if (this.filtro === 'REORDEN') coincideFiltro = material.requiere_reorden;
      if (this.filtro === 'NORMAL') coincideFiltro = !material.alerta_stock_bajo;

      return coincideTexto && coincideFiltro;
    });
  }

  get materialesAlerta(): Material[] {
    return this.materiales.filter((material) => material.alerta_stock_bajo);
  }

  escala(material: Material): number {
    return Math.max(material.stock_actual, material.stock_minimo * 1.25, 1);
  }

  barraActual(material: Material): number {
    return Math.max(2, Math.min(100, Math.round((material.stock_actual / this.escala(material)) * 100)));
  }

  barraMinimo(material: Material): number {
    return Math.min(98, Math.round((material.stock_minimo / this.escala(material)) * 100));
  }

  colorBarra(material: Material): string {
    if (material.stock_actual <= material.stock_minimo) return 'bg-amber-500';
    if (material.requiere_reorden) return 'bg-[#b9884f]';
    return 'bg-emerald-500';
  }

  abrirModalNuevo(): void {
    this.nuevoMaterial = {
      nombre: '',
      unidad_medida: 'Piezas',
      stock_actual: 0,
      stock_minimo: 5,
      costo_unitario: 0
    };
    this.modalNuevoAbierto = true;
    this.refrescarVista();
  }

  guardarMaterial(): void {
    if (!this.nuevoMaterial.nombre.trim() || !this.nuevoMaterial.unidad_medida.trim()) {
      this.error = 'Completa el nombre y la unidad de medida del insumo.';
      this.refrescarVista();
      return;
    }

    this.guardando = true;
    this.error = '';

    this.http.post<any>(`${this.api}/almacen/materiales`, this.nuevoMaterial).subscribe({
      next: (res) => {
        this.guardando = false;
        this.modalNuevoAbierto = false;
        this.mensaje = res.message || 'Insumo registrado correctamente.';
        this.refrescarVista();
        this.cargarDatos();
        setTimeout(() => {
          this.mensaje = '';
          this.refrescarVista();
        }, 3500);
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.message || 'Error al registrar el insumo.';
        this.refrescarVista();
      }
    });
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}
