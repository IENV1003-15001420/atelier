import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { SidebarComponent } from '../shared/sidebar/sidebar';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, RouterModule, HttpClientModule, FormsModule, SidebarComponent],
  templateUrl: './usuarios.html'
})
export class UsuariosComponent implements OnInit {
  sidebarAbierta: boolean = true;
  usuarioLogueado: any = null;
  
  usuarios: any[] = [];
  usuariosFiltrados: any[] = [];
  
  // Filtros y búsqueda
  filtroRolActual: string = 'TODOS';
  textoBusqueda: string = '';
  filtroEstado: string = 'TODOS';

  // Control de Modales
  modalNuevoAbierto: boolean = false;
  modalAuditoriaAbierto: boolean = false;

  // Formulario Nuevo Usuario
  nuevoUsuario = {
    nombre: '',
    email: '',
    password: '',
    telefono: '',
    direccion: '',
    id_rol: 6 // Por defecto Carpintero
  };

  constructor(
    private router: Router, 
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    const datosGuardados = localStorage.getItem('usuario_atelier');
    if (datosGuardados) {
      this.usuarioLogueado = JSON.parse(datosGuardados);
      this.cargarUsuarios();
    } else {
      this.router.navigate(['/login']);
    }
  }

  toggleSidebar() {
    this.sidebarAbierta = !this.sidebarAbierta;
  }

  cargarUsuarios() {
    this.http.get('http://localhost:5000/api/usuarios').subscribe({
      next: (res: any) => {
        if (res.success) {
          this.usuarios = res.usuarios || [];
          this.aplicarFiltros();
          this.cdr.detectChanges(); // Fuerza a Angular a renderizar la tabla y KPIs de inmediato
        }
      },
      error: (err) => {
        console.error('Error al cargar usuarios desde Flask:', err);
      }
    });
  }

  // --- LÓGICA DE FILTROS (PÍLDORAS, BUSCADOR Y ESTADO) ---
  seleccionarRol(rol: string) {
    this.filtroRolActual = rol;
    this.aplicarFiltros();
  }

  aplicarFiltros() {
    this.usuariosFiltrados = this.usuarios.filter(u => {
      const rol = (u.rolPrincipal || '').toUpperCase();
      const estado = (u.estado || '').toUpperCase();
      const nombre = (u.nombre || '').toLowerCase();
      const correo = (u.correo || '').toLowerCase();
      const estacion = (u.estacion || '').toLowerCase();

      // 1. Filtro por píldora de rol
      const coincideRol = this.filtroRolActual === 'TODOS' || 
                          rol.includes(this.filtroRolActual);
      
      // 2. Filtro por estado
      const coincideEstado = this.filtroEstado === 'TODOS' || 
                             estado === this.filtroEstado;

      // 3. Filtro por texto en buscador
      const busqueda = this.textoBusqueda.toLowerCase();
      const coincideTexto = nombre.includes(busqueda) ||
                            correo.includes(busqueda) ||
                            estacion.includes(busqueda);

      return coincideRol && coincideEstado && coincideTexto;
    });
  }

  contarPorRol(palabraClave: string): number {
    if (palabraClave === 'TODOS') return this.usuarios.length;
    return this.usuarios.filter(u => (u.rolPrincipal || '').toUpperCase().includes(palabraClave)).length;
  }

  get totalActivos(): number {
    return this.usuarios.filter(u => (u.estado || '').toUpperCase() === 'ACTIVO').length;
  }

  // --- BOTÓN 1: EXPORTAR DIRECTORIO (CSV) ---
  exportarNomina() {
    const encabezados = ['ID,Nombre,Correo,Rol,Estacion / Banco,Contacto y Registro,Estado'];
    const filas = this.usuariosFiltrados.map(u => 
      `${u.id},"${u.nombre}","${u.correo}","${u.rolPrincipal}","${u.estacion}","${u.acceso} (${u.accesoSub})",${u.estado}`
    );
    
    const csvContenido = '\uFEFF' + [encabezados, ...filas].join('\n');
    const blob = new Blob([csvContenido], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Directorio_Usuarios_Atelier_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // --- BOTÓN 2: AGREGAR NUEVO USUARIO ---
  abrirModalNuevo() {
    this.nuevoUsuario = { nombre: '', email: '', password: '', telefono: '', direccion: '', id_rol: 6 };
    this.modalNuevoAbierto = true;
  }

  guardarNuevoUsuario() {
    if (!this.nuevoUsuario.nombre || !this.nuevoUsuario.email) {
      alert('Por favor completa al menos el nombre y el correo.');
      return;
    }

    this.http.post('http://localhost:5000/api/usuarios', this.nuevoUsuario).subscribe({
      next: (res: any) => {
        if (res.success) {
          this.modalNuevoAbierto = false;
          this.cargarUsuarios();
        }
      },
      error: (err) => alert(err.error?.mensaje || 'Error al guardar usuario. Revisa la consola de Flask.')
    });
  }

  cerrarSesion() {
    localStorage.removeItem('usuario_atelier');
    this.router.navigate(['/login']);
  }
}