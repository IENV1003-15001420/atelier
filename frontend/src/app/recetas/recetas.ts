import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { SidebarComponent } from '../shared/sidebar/sidebar';

@Component({
  selector: 'app-recetas',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, SidebarComponent],
  templateUrl: './recetas.html'
})
export class Recetas implements OnInit {
  private apiUrl = 'http://localhost:5000/api/recetas';
  sidebarAbierta = true;
  usuarioLogueado: any = null;

  productos: any[] = [];
  recetas: any[] = [];
  materiales: any[] = [];
  rolesTaller: any[] = [];
  productoSeleccionado: any = null;
  mensajeAlerta = '';

  nuevoProducto = {
    nombre: '',
    categoria: 'Sala',
    precio_venta: 0,
    tiempo_estimado_horas: 8,
    requiere_instalacion: false,
    descripcion: ''
  };

  nuevoPaso = {
    id_material: null as number | null,
    cantidad_necesaria: 1,
    orden_fase: 1,
    id_rol_responsable: 6,
    instruccion_tecnica: ''
  };

  constructor(private router: Router, private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    const datos = localStorage.getItem('usuario_atelier');
    if (!datos) { this.router.navigate(['/login']); return; }
    this.usuarioLogueado = JSON.parse(datos);
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.http.get(this.apiUrl).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.productos = res.productos || [];
          this.recetas = res.recetas || [];
          this.materiales = res.materiales || [];
          this.rolesTaller = res.roles_taller || [];
          if (!this.productoSeleccionado && this.productos.length > 0) {
            this.productoSeleccionado = this.productos[0];
          }
          if (!this.nuevoPaso.id_material && this.materiales.length > 0) {
            this.nuevoPaso.id_material = this.materiales[0].id_material;
          }
          this.cdr.detectChanges();
        }
      },
      error: (err) => {
        this.mensajeAlerta = `Error al conectar con el servidor (${err.status || 'sin conexión'}). Verifica que app.py tenga registrado routes_romo.`;
        this.cdr.detectChanges();
      }
    });
  }

  get recetasProductoActual() {
    if (!this.productoSeleccionado) return [];
    return this.recetas.filter(r => r.id_producto === this.productoSeleccionado.id_producto);
  }

  guardarProducto(): void {
    if (!this.nuevoProducto.nombre.trim()) {
      this.mensajeAlerta = 'Escribe el nombre del mueble antes de guardar.';
      return;
    }
    this.http.post(`${this.apiUrl}/productos`, this.nuevoProducto).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mensajeAlerta = res.mensaje;
          this.nuevoProducto = { nombre: '', categoria: 'Sala', precio_venta: 0, tiempo_estimado_horas: 8, requiere_instalacion: false, descripcion: '' };
          this.cargarDatos();
        } else {
          this.mensajeAlerta = res.mensaje || 'No se pudo guardar el mueble.';
        }
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mensajeAlerta = `Error al guardar mueble (${err.status}): ${err.error?.mensaje || err.message}`;
        this.cdr.detectChanges();
      }
    });
  }

  agregarPaso(): void {
    if (!this.productoSeleccionado || !this.nuevoPaso.id_material) return;
    this.http.post(`${this.apiUrl}/pasos`, {
      ...this.nuevoPaso,
      id_producto: this.productoSeleccionado.id_producto
    }).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mensajeAlerta = res.mensaje;
          this.nuevoPaso.instruccion_tecnica = '';
          this.cargarDatos();
        }
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mensajeAlerta = `Error al agregar paso (${err.status}): ${err.error?.mensaje || err.message}`;
        this.cdr.detectChanges();
      }
    });
  }

  eliminarPaso(idReceta: number): void {
    this.http.delete(`${this.apiUrl}/pasos/${idReceta}`).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.mensajeAlerta = res.mensaje;
          this.cargarDatos();
        }
      }
    });
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}