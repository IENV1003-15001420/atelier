import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, UsuarioSesion } from '../../services/auth';

interface ItemMenu {
  ruta: string;
  icono: string;
  titulo: string;
  roles: number[];
}

interface SeccionMenu {
  encabezado: string;
  items: ItemMenu[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.html'
})
export class SidebarComponent implements OnInit {
  @Input() abierta = true;
  usuario: UsuarioSesion | null = null;
  seccionesVisibles: SeccionMenu[] = [];

  private readonly catalogoMenu: SeccionMenu[] = [
    {
      encabezado: 'VISIÓN GENERAL',
      items: [
        { ruta: '/dashboard', icono: '📊', titulo: 'Panel de Control', roles: [1] }
      ]
    },
    {
      encabezado: 'TALLER Y PRODUCCIÓN',
      items: [
        { ruta: '/armado', icono: '📐', titulo: 'Armado y Fabricación', roles: [1, 6] },
        { ruta: '/acabados', icono: '🖌️', titulo: 'Pintura y Acabados', roles: [1, 7] },
        { ruta: '/recetas', icono: '📋', titulo: 'Catálogo y Recetas', roles: [1, 6, 7] },
        { ruta: '/logistica', icono: '🚚', titulo: 'Logística e Instalaciones', roles: [1, 8, 9] }
      ]
    },
    {
      encabezado: 'INVENTARIO Y MATERIALES',
      items: [
        { ruta: '/compras', icono: '📦', titulo: 'Compras Generales', roles: [1, 2, 4] },
        { ruta: '/almacen', icono: '🪵', titulo: 'Almacén e Inventarios', roles: [1, 2, 4] }
      ]
    },
    {
      encabezado: 'COMERCIO DIGITAL',
      items: [
        { ruta: '/cotizaciones', icono: '📝', titulo: 'Cotizaciones CRM', roles: [1, 3] },
        { ruta: '/ecommerce', icono: '🛒', titulo: 'Tienda en Línea', roles: [1, 3, 5] },
        { ruta: '/resenas', icono: '⭐', titulo: 'Reseñas y Encuestas', roles: [1, 3] }
      ]
    },
    {
      encabezado: 'ADMINISTRACIÓN',
      items: [
        { ruta: '/usuarios', icono: '🫂', titulo: 'Gestión de Usuarios', roles: [1] }
      ]
    }
  ];

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.usuario = this.authService.obtenerUsuario();
    const idRol = Number(this.usuario?.id_rol || 0);

    this.seccionesVisibles = this.catalogoMenu
      .map((seccion) => ({
        encabezado: seccion.encabezado,
        items: seccion.items.filter((item) => idRol === 1 || item.roles.includes(idRol))
      }))
      .filter((seccion) => seccion.items.length > 0);
  }
}