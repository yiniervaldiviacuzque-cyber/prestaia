"""Add Telegram loan applications without altering financial tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_telegram_solicitudes"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "solicitudes_telegram",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("codigo", sa.String(30), nullable=False, unique=True),
        sa.Column("telegram_user_id", sa.String(40), nullable=False),
        sa.Column("telegram_chat_id", sa.String(40), nullable=False),
        sa.Column("telegram_username", sa.String(100)),
        sa.Column("nombres", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("tipo_documento", sa.String(10), nullable=False),
        sa.Column("numero_documento", sa.String(30), nullable=False),
        sa.Column("celular", sa.String(30), nullable=False),
        sa.Column("correo", sa.String(150)),
        sa.Column("direccion", sa.String(250)),
        sa.Column("ocupacion", sa.String(120), nullable=False),
        sa.Column("ingresos_mensuales", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_solicitado", sa.Numeric(12, 2), nullable=False),
        sa.Column("plazo_meses", sa.Integer(), nullable=False),
        sa.Column("consentimiento_datos", sa.Boolean(), nullable=False),
        sa.Column("foto_file_id", sa.String(250)),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("observaciones", sa.Text()),
        sa.Column("requiere_asesor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revisado_por", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("perfiles.id"), nullable=True),
        sa.Column("revisado_en", sa.DateTime(timezone=True)),
    )

    op.create_index(
        "ix_solicitudes_telegram_estado",
        "solicitudes_telegram", ["estado"]
    )
    op.create_index(
        "ix_solicitudes_telegram_usuario",
        "solicitudes_telegram", ["telegram_user_id"]
    )
    op.create_index(
        "ix_solicitudes_telegram_documento",
        "solicitudes_telegram", ["numero_documento"]
    )
    op.create_index(
        "ix_solicitudes_telegram_fecha",
        "solicitudes_telegram", ["creado_en"]
    )


def downgrade():
    # Este downgrade elimina la tabla y todas las solicitudes de Telegram.
    op.drop_table("solicitudes_telegram")
