import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router'; // Importamos Router por si quieres redirigir después
import { AuthService } from '../../services/auth'; // Conecta con tu servicio

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  // Variables para guardar lo que el usuario escriba
  correo = '';
  contrasena = '';
  mensajeError = '';

  constructor(
    private authService: AuthService,
    private router: Router // Inyectamos el Router
  ) {}

  iniciarSesion() {
    this.mensajeError = '';

    if (!this.correo || !this.contrasena) {
      this.mensajeError = 'Por favor, ingresa tu correo y contraseña.';
      return;
    }

    // Enviamos los datos a Flask
    this.authService.login(this.correo, this.contrasena).subscribe({
      next: (respuesta: any) => {
        console.log('Respuesta del servidor:', respuesta);
        
        if (respuesta.success) {
          // Guardamos la información del usuario en el navegador
          localStorage.setItem('usuario_atelier', JSON.stringify(respuesta.usuario));
          
          alert('¡Acceso concedido! Bienvenido a Atelier.');

          
           this.router.navigate(['/dashboard']);
        }
      },
      error: (error) => {
        console.error('Error:', error);
        this.mensajeError = 'Credenciales inválidas o usuario inactivo.';
      }
    });
  }
}