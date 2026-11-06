# API REST

Documentación OpenAPI interactiva: `/docs`.

Todas las rutas `/api` salvo health requieren `Authorization: Bearer <access_token>` de Supabase Auth. Errores se entregan con status HTTP y `detail` seguro.

| Método | Ruta | Función |
| --- | --- | --- |
| GET | `/api/health` | Conectividad de PostgreSQL |
| GET | `/api/dashboard` | Métricas, seguimiento, riesgo y alertas |
| GET/POST | `/api/clientes` | Buscar/listar y crear clientes |
| GET/PUT | `/api/clientes/{id}` | Detalle y edición |
| GET/POST | `/api/creditos` | Buscar/listar y registrar crédito con cronograma |
| GET | `/api/creditos/{id}` | Crédito y cuotas |
| PUT | `/api/creditos/{id}` | Actualiza código/estado; condiciones financieras quedan bloqueadas tras generar el cronograma |
| GET | `/api/pagos` | Historial de pagos, opcionalmente filtrado por crédito |
| POST | `/api/pagos` | Registra pago de una cuota pendiente |
| GET | `/api/predicciones` | Historial de evaluaciones |
| POST | `/api/predicciones/evaluar?credito_id=UUID` | Evaluación preliminar persistida |
| GET | `/api/cobranzas` | Cuotas con saldo |
| POST | `/api/cobranzas/gestiones` | Registrar gestión/compromiso |
| GET | `/api/cobranzas/gestiones` | Historial de gestiones |
| GET | `/api/alertas` | Genera de forma idempotente alertas de vencimiento y lista activas |
| PATCH | `/api/alertas/{id}?resuelta=true` | Resolver o reabrir una alerta |
| GET | `/api/reportes/cartera?formato=csv` | Cartera JSON o CSV; acepta `desde` y `hasta` |
| GET | `/api/asistente?q=...` | Respuesta local basada en agregados reales |

Dashboard cuando no hay filas entrega contadores y montos cero. `evolucion` agrega la cartera desembolsada por mes a partir de los créditos registrados; no representa saldos históricos. La evaluación de riesgo es una regla local explicable, no una IA entrenada.
