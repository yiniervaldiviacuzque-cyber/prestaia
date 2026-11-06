# Despliegue en Render

## Backend Web Service

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/api/health`
- Variables: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `CORS_ORIGINS` (URL pública del Static Site), opcional `AI_API_KEY`.

## Frontend Static Site

- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Variables de build: `VITE_API_URL` (URL HTTPS del Web Service), `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
- Rewrite SPA: `/*` → `/index.html` (Rewrite).

Ejecutar y revisar primero la migración SQL en Supabase y crear al menos el primer usuario Auth/perfil. No publicar `DATABASE_URL`, contraseñas ni claves `service_role` en el Static Site. No se ha desplegado nada desde este trabajo.
