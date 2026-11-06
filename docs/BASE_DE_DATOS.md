# Base de datos

`database/migrations/001_initial_schema.sql` crea perfiles, clientes, créditos, cuotas, pagos, predicciones, alertas y gestiones de cobranza con PK/FK, restricciones e índices. Usa `IF NOT EXISTS` y no elimina objetos ni filas. RLS se activa en todas las tablas; no se instala política pública ni de lectura financiera para roles del navegador. El baseline también está registrado en `backend/alembic/versions/001_initial_schema.py`; ejecutar `alembic upgrade head` desde `backend` después de configurar `DATABASE_URL`.

No se pudo consultar el proyecto remoto desde este entorno, por lo que la migración está preparada pero no ejecutada. Antes de ejecutarla, inspeccionar el catálogo de Supabase por tablas preexistentes y comparar columnas. El SQL no realiza introspección destructiva ni adapta columnas incompatibles.

La aplicación usa SQLAlchemy con migración SQL versionada. Para futuras versiones, crear un nuevo archivo numerado; nunca editar migraciones ya aplicadas.
