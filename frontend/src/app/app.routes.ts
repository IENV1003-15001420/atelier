import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './dashboard/dashboard';
import { UsuariosComponent } from './usuarios/usuarios';
import { AlmacenComponent } from './almacen/almacen';
import { ComprasComponent } from './compras/compras';
import { EcommerceComponent } from './ecommerce/ecommerce';
import { Cotizaciones } from './cotizaciones/cotizaciones';
import { Logistica } from './logistica/logistica';
import { Resenas } from './resenas/resenas';
import { Armado } from './armado/armado';
import { Acabados } from './acabados/acabados';
import { Recetas } from './recetas/recetas';
import { roleGuard } from './guards/role.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [roleGuard], data: { roles: [1] } },
  { path: 'usuarios', component: UsuariosComponent, canActivate: [roleGuard], data: { roles: [1] } },
  { path: 'almacen', component: AlmacenComponent, canActivate: [roleGuard], data: { roles: [1, 2, 4] } },
  { path: 'compras', component: ComprasComponent, canActivate: [roleGuard], data: { roles: [1, 2, 4] } },
  { path: 'cotizaciones', component: Cotizaciones, canActivate: [roleGuard], data: { roles: [1, 3] } },
  { path: 'resenas', component: Resenas, canActivate: [roleGuard], data: { roles: [1, 3] } },
  { path: 'armado', component: Armado, canActivate: [roleGuard], data: { roles: [1, 6] } },
  { path: 'acabados', component: Acabados, canActivate: [roleGuard], data: { roles: [1, 7] } },
  { path: 'recetas', component: Recetas, canActivate: [roleGuard], data: { roles: [1, 6, 7] } },
  { path: 'logistica', component: Logistica, canActivate: [roleGuard], data: { roles: [1, 8, 9] } },
  { path: 'ecommerce', component: EcommerceComponent },
  { path: '**', redirectTo: 'login' }
];