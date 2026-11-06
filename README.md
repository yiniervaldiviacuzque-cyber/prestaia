# PRESTAIA — INTELLIGENCE FINANCE

Inteligencia artificial para decisiones financieras más inteligentes.

PRESTAIA es una aplicación React/Vite conectada a una API FastAPI que persiste operaciones en PostgreSQL (Supabase). Incluye dashboard con datos reales, clientes, créditos y cuotas, evaluación preliminar explicable, cobranzas, alertas deduplicadas, asistente local y exportación de cartera CSV.

## Requisitos

- Node.js 20.19+ o 22.12+.
- Python 3.11+.
- Proyecto Supabase existente, acceso SQL Editor y credenciales de conexión PostgreSQL.
- Usuario de Supabase Auth creado manualmente y perfil asociado.

## Inicio rápido

1. Ejecutar `database/migrations/001_initial_schema.sql` una vez en Supabase SQL Editor después de revisar si las tablas existentes son compatibles. Es aditiva; no borra tablas ni datos.
2. Configurar `backend/.env` desde `backend/.env.example`, con `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `CORS_ORIGINS`.
3. Instalar backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
4. Iniciar backend: `uvicorn app.main:app --reload` (http://localhost:8000/docs).
5. Crear `frontend/.env.local` desde `frontend/.env.example`, establecer URL de API y datos públicos de Supabase.
6. Instalar e iniciar frontend: `cd frontend && npm install && npm run dev`.

Consulta `docs/CONFIGURACION.md` y `docs/DESPLIEGUE_RENDER.md`. No se cargan datos demo automáticamente.

## Límites implementados

La evaluación de riesgo actual usa reglas preliminares identificadas, no un modelo de ML entrenado. La API externa de IA no se invoca. No se crean usuarios ni contraseñas por defecto. Si el esquema de una base existente difiere del migration, debe prepararse una migración de adaptación antes de ejecutar la API.
