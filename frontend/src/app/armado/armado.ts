import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { SidebarComponent } from '../shared/sidebar/sidebar';

@Component({
  selector: 'app-armado',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule, FormsModule, SidebarComponent],
  templateUrl: './armado.html'
  
})
export class Armado implements OnInit {
  private apiUrl = 'http://localhost:5000/api/produccion';
  sidebarAbierta = true;
  usuarioLogueado: any = null;
  ordenes: any[] = [];
  carpinteros: any[] = [];
  mensajeAlerta = '';

  constructor(private router: Router, private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    const datos = localStorage.getItem('usuario_atelier');
    if (!datos) { this.router.navigate(['/login']); return; }
    this.usuarioLogueado = JSON.parse(datos);
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.http.get(`${this.apiUrl}/ordenes`).subscribe((res: any) => {
      if (res.success) {
        this.ordenes = (res.ordenes || []).filter((o: any) =>
          o.fase_kanban === 'Pendiente' || o.fase_kanban === 'Corte y Armado'
        );
        this.cdr.detectChanges();
      }
    });
    this.http.get(`${this.apiUrl}/catalogos`).subscribe((res: any) => {
      if (res.success) {
        this.carpinteros = (res.operarios || []).filter((op: any) => op.id_rol === 6);
        this.cdr.detectChanges();
      }
    });
  }

  get pendientes() { return this.ordenes.filter(o => o.fase_kanban === 'Pendiente'); }
  get enArmado() { return this.ordenes.filter(o => o.fase_kanban === 'Corte y Armado'); }

  actualizarOrden(orden: any, nuevaFase: string): void {
    this.http.put(`${this.apiUrl}/ordenes/${orden.id_detalle}`, {
      fase_kanban: nuevaFase,
      id_operario_asignado: orden.id_operario_asignado,
      horas_invertidas: orden.horas_invertidas
    }).subscribe((res: any) => {
      if (res.success) {
        this.mensajeAlerta = res.mensaje;
        this.cargarDatos();
      }
    });
  }

  cerrarSesion(): void {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}