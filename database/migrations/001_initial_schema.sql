-- PRESTAIA schema v1. Review and run in Supabase SQL Editor once.
-- Non-destructive: creates missing objects only; never drops existing data.
create extension if not exists pgcrypto;

do $$ begin
  create type public.prestaia_rol as enum ('administrador','analista','cobranzas');
exception when duplicate_object then null; end $$;

create table if not exists public.perfiles (
  id uuid primary key references auth.users(id) on delete cascade,
  rol varchar(30) not null default 'analista' check(rol in ('administrador','analista','cobranzas')), nombre varchar(120), activo boolean not null default true,
  creado_en timestamptz not null default now(), actualizado_en timestamptz not null default now()
);
create table if not exists public.clientes (
  id uuid primary key default gen_random_uuid(), codigo varchar(30) not null unique,
  tipo_documento varchar(30) not null, numero_documento varchar(40) not null,
  nombres varchar(100) not null, apellidos varchar(100) not null, telefono varchar(30), correo varchar(254),
  direccion text, ingresos_mensuales numeric(14,2) check (ingresos_mensuales is null or ingresos_mensuales >= 0),
  activo boolean not null default true, creado_en timestamptz not null default now(), actualizado_en timestamptz not null default now(),
  constraint uq_cliente_documento unique(tipo_documento, numero_documento)
);
create table if not exists public.creditos (
  id uuid primary key default gen_random_uuid(), codigo varchar(30) not null unique,
  cliente_id uuid not null references public.clientes(id) on delete restrict,
  monto numeric(14,2) not null check (monto > 0), tasa_interes numeric(7,4) not null check (tasa_interes between 0 and 100),
  plazo_meses integer not null check (plazo_meses between 1 and 600), frecuencia_pago varchar(20) not null default 'mensual' check (frecuencia_pago in ('semanal','quincenal','mensual')),
  fecha_desembolso date not null, fecha_vencimiento date not null check(fecha_vencimiento > fecha_desembolso),
  saldo_pendiente numeric(14,2) not null check(saldo_pendiente >= 0 and saldo_pendiente <= monto),
  estado varchar(20) not null default 'activo' check(estado in ('activo','pagado','vencido','cancelado')),
  creado_en timestamptz not null default now(), actualizado_en timestamptz not null default now()
);
create table if not exists public.cuotas (
  id uuid primary key default gen_random_uuid(), credito_id uuid not null references public.creditos(id) on delete cascade,
  numero integer not null check(numero > 0), fecha_vencimiento date not null, monto numeric(14,2) not null check(monto > 0),
  saldo_pendiente numeric(14,2) not null check(saldo_pendiente >= 0 and saldo_pendiente <= monto),
  estado varchar(20) not null default 'pendiente' check(estado in ('pendiente','pagada','parcial','vencida')),
  creado_en timestamptz not null default now(), unique(credito_id, numero)
);
create table if not exists public.pagos (
  id uuid primary key default gen_random_uuid(), cuota_id uuid not null references public.cuotas(id) on delete restrict,
  monto numeric(14,2) not null check(monto > 0), pagado_en timestamptz not null default now(), referencia varchar(100)
);
create table if not exists public.predicciones (
  id uuid primary key default gen_random_uuid(), credito_id uuid not null references public.creditos(id) on delete cascade,
  probabilidad_morosidad numeric(5,4) not null check(probabilidad_morosidad between 0 and 1), nivel_riesgo varchar(10) not null check(nivel_riesgo in ('bajo','medio','alto')),
  metodo varchar(40) not null default 'reglas_preliminares_v1', factores text not null default '[]', recomendacion text not null,
  creado_en timestamptz not null default now()
);
create table if not exists public.alertas (
  id uuid primary key default gen_random_uuid(), credito_id uuid references public.creditos(id) on delete cascade,
  cuota_id uuid references public.cuotas(id) on delete cascade, tipo varchar(40) not null, mensaje text not null,
  prioridad varchar(15) not null default 'media', clave_dedupe varchar(180) not null unique, resuelta boolean not null default false,
  creado_en timestamptz not null default now()
);
create table if not exists public.gestiones_cobranza (
  id uuid primary key default gen_random_uuid(), credito_id uuid not null references public.creditos(id) on delete cascade,
  cuota_id uuid references public.cuotas(id) on delete set null, usuario_id uuid references public.perfiles(id) on delete set null,
  canal varchar(30) not null, resultado varchar(50) not null, notas text, compromiso_monto numeric(14,2) check(compromiso_monto is null or compromiso_monto > 0),
  compromiso_fecha date, seguimiento_fecha date, creado_en timestamptz not null default now()
);

create index if not exists ix_clientes_documento on public.clientes(tipo_documento, numero_documento);
create index if not exists ix_creditos_cliente_estado on public.creditos(cliente_id, estado);
create index if not exists ix_cuotas_vencimiento_saldo on public.cuotas(fecha_vencimiento) where saldo_pendiente > 0;
create index if not exists ix_pagos_cuota_fecha on public.pagos(cuota_id, pagado_en desc);
create index if not exists ix_predicciones_credito_fecha on public.predicciones(credito_id, creado_en desc);
create index if not exists ix_alertas_abiertas on public.alertas(creado_en desc) where resuelta = false;
create index if not exists ix_gestiones_seguimiento on public.gestiones_cobranza(seguimiento_fecha) where seguimiento_fecha is not null;

-- API uses server-side DATABASE_URL and verifies Supabase Auth tokens. Browser roles cannot access financial rows.
alter table public.perfiles enable row level security;
alter table public.clientes enable row level security;
alter table public.creditos enable row level security;
alter table public.cuotas enable row level security;
alter table public.pagos enable row level security;
alter table public.predicciones enable row level security;
alter table public.alertas enable row level security;
alter table public.gestiones_cobranza enable row level security;

drop policy if exists "perfil propio lectura" on public.perfiles;
create policy "perfil propio lectura" on public.perfiles for select to authenticated using (id = auth.uid());
-- Deliberately no anon/authenticated financial table policies: access is through authenticated API service role/DB role only.
