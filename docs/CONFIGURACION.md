# Configuración local y seguridad

## Variables backend

Copiar `backend/.env.example` a `backend/.env`:

- `DATABASE_URL`: URL PostgreSQL de Supabase (no usar en el frontend).
- `SUPABASE_URL`: URL del proyecto PRESTAIA conocido.
- `SUPABASE_ANON_KEY`: clave pública anon/publishable usada solo para verificar sesión de Auth.
- `CORS_ORIGINS`: orígenes separados por coma.
- `AI_API_KEY`: opcional, reservado; el asistente actual no llama proveedores externos.

## Variables frontend

Copiar `frontend/.env.example` a `frontend/.env.local`. `VITE_SUPABASE_ANON_KEY` es una clave pública de cliente, nunca una service role key. `VITE_API_URL` es la URL del backend. Los cambios VITE requieren reiniciar Vite.

## Primer usuario y roles

1. Crear el usuario desde Supabase Dashboard → Authentication → Users → Add user; asignar su propio correo y contraseña allí.
2. Tras ejecutar la migración, crear su perfil con el UUID Auth real:

```sql
insert into public.perfiles (id, rol, nombre)
values ('UUID_REAL_DE_AUTH', 'administrador', 'Administrador')
on conflict (id) do nothing;
```

No sustituir el UUID por un valor inventado. La API deniega acceso sin perfil activo. Roles iniciales: `administrador`, `analista`, `cobranzas`.

La autenticación actual cubre inicio y cierre de sesión; la sesión queda en localStorage y expira según Supabase. La API valida cada token en Supabase Auth. Para endurecimiento de producción, evaluar cookies HttpOnly mediante BFF y rotación de refresh token.
