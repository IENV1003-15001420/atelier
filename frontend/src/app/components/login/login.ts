import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html'
})
export class LoginComponent {
  modo: 'login' | 'registro' = 'login';
  correo = '';
  contrasena = '';
  mensajeError = '';
  cargando = false;

  registro = {
    nombre: '',
    email: '',
    password: '',
    telefono: '',
    direccion: ''
  };

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  iniciarSesion() {
    this.mensajeError = '';

    if (!this.correo || !this.contrasena) {
      this.mensajeError = 'Por favor, ingresa tu correo y contraseña.';
      return;
    }

    this.cargando = true;
    this.authService.login(this.correo, this.contrasena).subscribe({
      next: (respuesta: any) => {
        this.cargando = false;
        if (respuesta.success && respuesta.usuario) {
          this.authService.guardarSesion(respuesta.usuario);
          const destino = this.authService.obtenerRutaInicio(respuesta.usuario.id_rol);
          this.router.navigate([destino]);
        }
      },
      error: () => {
        this.cargando = false;
        this.mensajeError = 'Credenciales inválidas o usuario inactivo.';
      }
    });
  }

  registrarCliente() {
    this.mensajeError = '';

    if (!this.registro.nombre || !this.registro.email || !this.registro.password) {
      this.mensajeError = 'Completa tu nombre, correo y contraseña.';
      return;
    }

    this.cargando = true;
    this.authService.registrarCliente(this.registro).subscribe({
      next: (respuesta: any) => {
        this.cargando = false;
        if (respuesta.success && respuesta.usuario) {
          this.authService.guardarSesion(respuesta.usuario);
          this.router.navigate(['/ecommerce']);
        }
      },
      error: (err) => {
        this.cargando = false;
        this.mensajeError = err.error?.message || 'No se pudo crear la cuenta.';
      }
    });
  }
}