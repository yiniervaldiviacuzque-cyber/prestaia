# Arquitectura PRESTAIA

React + Vite sirve la interfaz. Los servicios frontend llaman exclusivamente a FastAPI; la autenticación de usuario usa Supabase Auth password grant y envía el access token como bearer. FastAPI valida ese token consultando `/auth/v1/user`, carga el rol de `perfiles` y aplica autorizaciones por endpoint. SQLAlchemy 2 conecta al PostgreSQL administrado por Supabase mediante `DATABASE_URL`. Las tablas tienen RLS habilitado y no conceden acceso financiero directo a `anon` ni `authenticated` desde PostgREST.

El `DATABASE_URL` se guarda únicamente en el entorno del backend. Debe usar una conexión privada/SSL y un rol backend limitado al esquema PRESTAIA. La identidad de Supabase se asocia mediante `perfiles.id = auth.users.id`. Se recomienda que el proceso no use `service_role` como clave de cliente.

La evaluación v1 es basada en reglas, guarda versión/método y factores. El esquema deja guardadas evaluaciones históricas para medir un modelo supervisado futuro con etiquetas verificables.
