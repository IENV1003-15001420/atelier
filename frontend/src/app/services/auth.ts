import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

export interface UsuarioSesion {
  id_usuario: number;
  nombre: string;
  email: string;
  id_rol: number;
  nombre_rol: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:5000/api/auth';
  private readonly storageKey = 'usuario_atelier';

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, { email, password });
  }

  registrarCliente(datos: {
    nombre: string;
    email: string;
    password: string;
    telefono?: string;
    direccion?: string;
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}/registro`, datos);
  }

  guardarSesion(usuario: UsuarioSesion): void {
    localStorage.setItem(this.storageKey, JSON.stringify(usuario));
  }

  obtenerUsuario(): UsuarioSesion | null {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  obtenerRutaInicio(idRol: number): string {
    const rutas: Record<number, string> = {
      1: '/dashboard',     // Administrador
      2: '/almacen',       // Almacén
      3: '/cotizaciones',  // Ventas
      4: '/compras',       // Compras
      5: '/ecommerce',     // Cliente
      6: '/armado',        // Carpintero
      7: '/acabados',      // Barnizador
      8: '/logistica',     // Instalador
      9: '/logistica'      // Logística
    };
    return rutas[Number(idRol)] || '/login';
  }

  cerrarSesion(): void {
    localStorage.removeItem(this.storageKey);
    this.router.navigate(['/login']);
  }
}