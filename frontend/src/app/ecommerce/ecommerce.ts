import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';

interface Producto {
  id_producto: number;
  nombre: string;
  descripcion: string;
  categoria: string;
  precio_venta: number;
  tiempo_estimado_horas: number;
  requiere_instalacion: boolean;
  imagen_url: string | null;
  calificacion_promedio: number;
  total_resenas: number;
}

interface ItemCarrito extends Producto {
  cantidad: number;
}

@Component({
  selector: 'app-ecommerce',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './ecommerce.html'
})
export class EcommerceComponent implements OnInit, OnDestroy {
  private readonly api = 'http://localhost:5000/api';
  private readonly storageCarrito = 'atelier_carrito';
  private refrescoPedidos: any = null;

  usuario: any = null;
  clienteId = 5;
  cliente: any = null;

  vista: 'catalogo' | 'pedidos' = 'catalogo';
  productos: Producto[] = [];
  pedidos: any[] = [];
  carrito: ItemCarrito[] = [];
  carritoAbierto = false;

  categorias = ['TODAS', 'Comedor', 'Sala', 'Recámara', 'Oficina', 'Exterior'];
  categoriaActual = 'TODAS';
  busqueda = '';
  direccion = '';

  cargando = true;
  cargandoPedidos = false;
  procesandoCheckout = false;
  error = '';
  mensaje = '';
  ultimoPedido: any = null;

  estrellas = [1, 2, 3, 4, 5];
  fases = ['Pendiente', 'Corte y Armado', 'Barnizado y Secado', 'Control Calidad', 'Terminado'];

  modalResenaAbierto = false;
  guardandoResena = false;
  resena = {
    id_detalle: 0,
    producto: '',
    calificacion: 5,
    comentario: ''
  };

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const datos = localStorage.getItem('usuario_atelier');
    if (datos) {
      this.usuario = JSON.parse(datos);
      if (Number(this.usuario?.id_rol) === 5) {
        this.clienteId = Number(this.usuario.id_usuario);
      }
    }

    this.cargarCarrito();
    this.refrescarVista();
    this.cargarCatalogo();
    this.cargarCliente();
    this.cargarPedidos();

    // Rastreo en vivo: refresca las fases del Kanban sin recargar la página.
    this.refrescoPedidos = setInterval(() => {
      if (this.vista === 'pedidos') {
        this.cargarPedidos(true);
      }
    }, 30000);
  }

  ngOnDestroy(): void {
    if (this.refrescoPedidos) {
      clearInterval(this.refrescoPedidos);
    }
  }

  refrescarVista(): void {
    this.cdr.detectChanges();
  }

  // ---------------- CATÁLOGO ----------------

  get productosFiltrados(): Producto[] {
    const texto = this.busqueda.trim().toLowerCase();

    return this.productos.filter((producto) => {
      const coincideCategoria = this.categoriaActual === 'TODAS' || producto.categoria === this.categoriaActual;
      const coincideTexto =
        !texto ||
        producto.nombre.toLowerCase().includes(texto) ||
        (producto.descripcion || '').toLowerCase().includes(texto) ||
        (producto.categoria || '').toLowerCase().includes(texto);

      return coincideCategoria && coincideTexto;
    });
  }

  cargarCatalogo(): void {
    this.cargando = true;
    this.http.get<any>(`${this.api}/ecommerce/productos`).subscribe({
      next: (res) => {
        this.productos = res.productos || [];
        // Refresca los datos de las piezas que ya estaban guardadas en el carrito
        // para que tomen las imágenes y precios actuales del catálogo.
        this.carrito = this.carrito.map((item) => {
          const actual = this.productos.find((producto) => producto.id_producto === item.id_producto);
          return actual
            ? { ...item, nombre: actual.nombre, precio_venta: actual.precio_venta, imagen_url: actual.imagen_url }
            : item;
        });
        this.guardarCarrito();
        this.cargando = false;
        this.refrescarVista();
      },
      error: (err) => {
        this.cargando = false;
        this.error = err.error?.message || 'No fue posible cargar el catálogo.';
        this.refrescarVista();
      }
    });
  }

  cargarCliente(): void {
    this.http.get<any>(`${this.api}/ecommerce/cliente/${this.clienteId}`).subscribe({
      next: (res) => {
        this.cliente = res.cliente;
        if (!this.direccion && this.cliente?.direccion) {
          this.direccion = this.cliente.direccion;
        }
        this.refrescarVista();
      },
      error: () => {
        this.cliente = null;
        this.refrescarVista();
      }
    });
  }

  cambiarCategoria(categoria: string): void {
    this.categoriaActual = categoria;
    this.refrescarVista();
  }

  limpiarFiltros(): void {
    this.busqueda = '';
    this.categoriaActual = 'TODAS';
    this.refrescarVista();
  }

  imagenError(producto: Producto): void {
    producto.imagen_url = null;
    this.refrescarVista();
  }

  // ---------------- CARRITO ----------------

  get usandoClienteDemo(): boolean {
    return !this.usuario || Number(this.usuario?.id_rol) !== 5;
  }

  get carritoCantidad(): number {
    return this.carrito.reduce((total, item) => total + item.cantidad, 0);
  }

  get carritoTotal(): number {
    return Number(this.carrito.reduce((total, item) => total + item.precio_venta * item.cantidad, 0).toFixed(2));
  }

  agregarAlCarrito(producto: Producto): void {
    const existente = this.carrito.find((item) => item.id_producto === producto.id_producto);
    if (existente) {
      existente.cantidad += 1;
    } else {
      this.carrito.push({ ...producto, cantidad: 1 });
    }

    this.guardarCarrito();
    this.mensaje = `"${producto.nombre}" se agregó al carrito.`;
    this.refrescarVista();
    setTimeout(() => {
      this.mensaje = '';
      this.refrescarVista();
    }, 2500);
  }

  aumentar(item: ItemCarrito): void {
    item.cantidad += 1;
    this.guardarCarrito();
    this.refrescarVista();
  }

  disminuir(item: ItemCarrito): void {
    if (item.cantidad > 1) {
      item.cantidad -= 1;
    } else {
      this.quitarDelCarrito(item);
      return;
    }
    this.guardarCarrito();
    this.refrescarVista();
  }

  quitarDelCarrito(item: ItemCarrito): void {
    this.carrito = this.carrito.filter((linea) => linea.id_producto !== item.id_producto);
    this.guardarCarrito();
    this.refrescarVista();
  }

  private cargarCarrito(): void {
    const guardado = localStorage.getItem(this.storageCarrito);
    if (!guardado) return;

    try {
      this.carrito = JSON.parse(guardado) || [];
    } catch {
      this.carrito = [];
    }
  }

  private guardarCarrito(): void {
    localStorage.setItem(this.storageCarrito, JSON.stringify(this.carrito));
  }

  abrirCarrito(): void {
    this.carritoAbierto = true;
    this.error = '';
    this.refrescarVista();
  }

  cerrarCarrito(): void {
    this.carritoAbierto = false;
    this.refrescarVista();
  }

  // ---------------- CHECKOUT ----------------

  finalizarCompra(): void {
    if (this.carrito.length === 0) {
      this.error = 'Tu carrito está vacío.';
      this.refrescarVista();
      return;
    }
    if (!this.direccion.trim()) {
      this.error = 'Escribe la dirección de entrega para confirmar el pedido.';
      this.refrescarVista();
      return;
    }

    this.procesandoCheckout = true;
    this.error = '';

    const payload = {
      id_cliente: this.clienteId,
      direccion: this.direccion.trim(),
      items: this.carrito.map((item) => ({ id_producto: item.id_producto, cantidad: item.cantidad }))
    };

    this.http.post<any>(`${this.api}/ecommerce/checkout`, payload).subscribe({
      next: (res) => {
        this.procesandoCheckout = false;
        this.ultimoPedido = res.pedido;
        this.carrito = [];
        this.guardarCarrito();
        this.carritoAbierto = false;
        this.mensaje = `Pedido #${res.pedido.id_pedido} confirmado por ${this.formatoMoneda(res.pedido.total)} MXN. ¡Gracias!`;
        this.vista = 'pedidos';
        this.refrescarVista();
        this.cargarPedidos();
        setTimeout(() => {
          this.mensaje = '';
          this.refrescarVista();
        }, 6000);
      },
      error: (err) => {
        this.procesandoCheckout = false;
        this.error = err.error?.message || 'No fue posible procesar el pedido.';
        this.refrescarVista();
      }
    });
  }

  formatoMoneda(valor: number): string {
    return Number(valor || 0).toLocaleString('es-MX', { maximumFractionDigits: 0 });
  }

  // ---------------- MIS PEDIDOS ----------------

  cargarPedidos(silencioso = false): void {
    if (!silencioso) this.cargandoPedidos = true;
    this.http.get<any>(`${this.api}/ecommerce/mis-pedidos/${this.clienteId}`).subscribe({
      next: (res) => {
        this.pedidos = res.pedidos || [];
        this.cargandoPedidos = false;
        this.refrescarVista();
      },
      error: (err) => {
        this.cargandoPedidos = false;
        if (!silencioso) {
          this.error = err.error?.message || 'No fue posible cargar tus pedidos.';
        }
        this.refrescarVista();
      }
    });
  }

  irACatalogo(): void {
    this.vista = 'catalogo';
    this.error = '';
    this.refrescarVista();
  }

  irAPedidos(): void {
    this.vista = 'pedidos';
    this.error = '';
    this.refrescarVista();
    this.cargarPedidos();
  }

  colorFase(indice: number, posicion: number): string {
    if (posicion < indice) return 'bg-[#6E121E]';
    if (posicion === indice) return 'bg-[#b9884f]';
    return 'bg-stone-200';
  }

  abrirResena(item: any): void {
    this.resena = {
      id_detalle: item.id_detalle,
      producto: item.producto,
      calificacion: item.calificacion_cliente || 5,
      comentario: item.comentario_resena || ''
    };
    this.modalResenaAbierto = true;
    this.error = '';
    this.refrescarVista();
  }

  enviarResena(): void {
    if (this.resena.calificacion < 1 || this.resena.calificacion > 5) {
      this.error = 'Selecciona una calificación de 1 a 5 estrellas.';
      this.refrescarVista();
      return;
    }

    this.guardandoResena = true;
    this.error = '';

    this.http.put<any>(`${this.api}/ecommerce/resena/${this.resena.id_detalle}`, {
      calificacion: Number(this.resena.calificacion),
      comentario: this.resena.comentario
    }).subscribe({
      next: (res) => {
        this.guardandoResena = false;
        this.modalResenaAbierto = false;
        this.mensaje = res.message || 'Reseña registrada correctamente.';
        this.refrescarVista();
        this.cargarPedidos();
        this.cargarCatalogo();
        setTimeout(() => {
          this.mensaje = '';
          this.refrescarVista();
        }, 5000);
      },
      error: (err) => {
        this.guardandoResena = false;
        this.error = err.error?.message || 'No fue posible guardar la reseña.';
        this.refrescarVista();
      }
    });
  }
}
