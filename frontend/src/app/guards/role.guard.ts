import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const usuario = authService.obtenerUsuario();

  if (!usuario) {
    router.navigate(['/login']);
    return false;
  }

  const idRol = Number(usuario.id_rol);
  const rolesPermitidos: number[] = route.data?.['roles'] || [];

  // El Administrador (1) tiene acceso completo a todo el sistema
  if (idRol === 1 || rolesPermitidos.includes(idRol)) {
    return true;
  }

  // Si intenta abrir otro módulo, lo redirige a su pantalla principal
  router.navigate([authService.obtenerRutaInicio(idRol)]);
  return false;
};