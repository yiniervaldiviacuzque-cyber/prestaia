from datetime import datetime, timezone
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .telegram_models import SolicitudTelegram


class ActualizarSolicitudTelegram(BaseModel):
    estado: Literal["pendiente", "observada", "aprobada", "rechazada"]
    observaciones: Optional[str] = Field(default=None, max_length=2000)


def serializar_solicitud(obj):
    return {
        "id": str(obj.id),
        "codigo": obj.codigo,
        "telegram_username": obj.telegram_username,
        "nombres": obj.nombres,
        "apellidos": obj.apellidos,
        "tipo_documento": obj.tipo_documento,
        "numero_documento": obj.numero_documento,
        "celular": obj.celular,
        "correo": obj.correo,
        "direccion": obj.direccion,
        "ocupacion": obj.ocupacion,
        "ingresos_mensuales": str(obj.ingresos_mensuales),
        "monto_solicitado": str(obj.monto_solicitado),
        "plazo_meses": obj.plazo_meses,
        "consentimiento_datos": obj.consentimiento_datos,
        "foto_disponible": bool(obj.foto_file_id),
        "estado": obj.estado,
        "observaciones": obj.observaciones,
        "requiere_asesor": obj.requiere_asesor,
        "creado_en": obj.creado_en,
        "revisado_en": obj.revisado_en,
        "revisado_por": str(obj.revisado_por) if obj.revisado_por else None,
    }


def build_telegram_router(db_session, require_roles):
    router = APIRouter(
        prefix="/api/telegram",
        tags=["Solicitudes de Telegram"]
    )
    acceso = require_roles("administrador", "analista")

    @router.get("/solicitudes")
    def listar_solicitudes(
        estado: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_session),
        user=Depends(acceso),
    ):
        query = select(SolicitudTelegram)
        if estado:
            if estado not in ("pendiente", "observada", "aprobada", "rechazada"):
                raise HTTPException(400, "Estado no válido")
            query = query.where(SolicitudTelegram.estado == estado)

        query = query.order_by(desc(SolicitudTelegram.creado_en))
        query = query.offset(offset).limit(limit)
        rows = db.scalars(query).all()

        return {
            "total": len(rows),
            "solicitudes": [serializar_solicitud(row) for row in rows],
        }

    @router.get("/solicitudes/{solicitud_id}")
    def detalle_solicitud(
        solicitud_id: UUID,
        db: Session = Depends(db_session),
        user=Depends(acceso),
    ):
        obj = db.get(SolicitudTelegram, solicitud_id)
        if not obj:
            raise HTTPException(404, "Solicitud no encontrada")
        return serializar_solicitud(obj)

    @router.patch("/solicitudes/{solicitud_id}")
    def actualizar_solicitud(
        solicitud_id: UUID,
        data: ActualizarSolicitudTelegram,
        db: Session = Depends(db_session),
        user=Depends(acceso),
    ):
        obj = db.get(SolicitudTelegram, solicitud_id)
        if not obj:
            raise HTTPException(404, "Solicitud no encontrada")

        obj.estado = data.estado
        obj.observaciones = data.observaciones
        obj.revisado_por = user["id"]
        obj.revisado_en = datetime.now(timezone.utc)

        db.commit()
        db.refresh(obj)
        return serializar_solicitud(obj)

    return router
