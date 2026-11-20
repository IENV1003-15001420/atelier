import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './dashboard/dashboard';
import { UsuariosComponent } from './usuarios/usuarios';
import { AlmacenComponent } from './almacen/almacen';
import { ComprasComponent } from './compras/compras';
import { EcommerceComponent } from './ecommerce/ecommerce';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' }, // Mantiene el flujo inicial
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'usuarios', component: UsuariosComponent },
  { path: 'almacen', component: AlmacenComponent },
  { path: 'compras', component: ComprasComponent },
  // La tienda es pública (PWA cliente); el checkout usa la cuenta cliente demo si no hay sesión.
  { path: 'ecommerce', component: EcommerceComponent },
  { path: '**', redirectTo: 'login' }
];