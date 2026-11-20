import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { DashboardComponent } from './dashboard/dashboard';
import { UsuariosComponent } from './usuarios/usuarios'; // Importa tu nuevo componente

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' }, // Mantiene tu flujo inicial
  { path: 'login', component: LoginComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'usuarios', component: UsuariosComponent } // Agregamos la nueva pantalla
];