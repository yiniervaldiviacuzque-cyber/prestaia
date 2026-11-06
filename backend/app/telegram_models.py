from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .main import Base


class SolicitudTelegram(Base):
    __tablename__ = "solicitudes_telegram"

    id: Mapped[object] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    telegram_user_id: Mapped[str] = mapped_column(String(40), nullable=False)
    telegram_chat_id: Mapped[str] = mapped_column(String(40), nullable=False)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100))

    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(10), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(30), nullable=False)
    celular: Mapped[str] = mapped_column(String(30), nullable=False)
    correo: Mapped[Optional[str]] = mapped_column(String(150))
    direccion: Mapped[Optional[str]] = mapped_column(String(250))
    ocupacion: Mapped[str] = mapped_column(String(120), nullable=False)

    ingresos_mensuales: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    monto_solicitado: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    plazo_meses: Mapped[int] = mapped_column(Integer, nullable=False)

    consentimiento_datos: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    foto_file_id: Mapped[Optional[str]] = mapped_column(String(250))

    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pendiente"
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    requiere_asesor: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    revisado_por: Mapped[Optional[object]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("perfiles.id"), nullable=True
    )
    revisado_en: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    __table_args__ = (
        Index("ix_solicitudes_telegram_estado", "estado"),
        Index("ix_solicitudes_telegram_usuario", "telegram_user_id"),
        Index("ix_solicitudes_telegram_documento", "numero_documento"),
        Index("ix_solicitudes_telegram_fecha", "creado_en"),
    )
