# Aviso — Autenticación JWT en construcción

**Fecha:** 2026-06-25

## Qué cambia

Hoy `/procesar/{pipeline}`, `/confirmar/{pipeline}` y `/rechazar/{pipeline}` no tienen autenticación — cualquiera con la URL puede disparar un proceso o rechazar un token activo. Se está agregando autenticación JWT con usuario individual por persona de P3, token expirando a las 8 horas.

## Por qué

Hallazgo de revisión de código del backend (Summary + P&L, PR #5). Bloqueante antes de exponer la API fuera de un entorno controlado.

## Cómo queda

- `POST /login` con `{usuario, password}` devuelve un JWT (`access_token`, expira en 8h).
- Los 3 endpoints de escritura ahora requieren header `Authorization: Bearer <token>`.
- No hay registro público — usuarios se crean con `scripts/crear_usuario.py <username> <password>`.
- El campo `usuario` que antes iba suelto en el body de `/procesar` desaparece: el `lock` ahora usa el usuario del token, no un campo que cualquiera podía llenar con cualquier nombre.
- Variable de entorno nueva y obligatoria en el servidor: `AGENTE_JWT_SECRET`.

Plan completo (TDD, 6 tareas) en `docs/superpowers/plans/2026-06-25-autenticacion-jwt.md`.

## Qué sigue

Ejecutar el plan. Al cerrarlo, queda resuelto el pendiente #4 de la sección 14 de `pipelines/summary/ESPECIFICACION.md`.
