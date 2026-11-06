"""Apply the reviewed, additive PRESTAIA SQL baseline."""
from pathlib import Path
from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    sql_path = Path(__file__).resolve().parents[3] / "database" / "migrations" / "001_initial_schema.sql"
    op.get_bind().exec_driver_sql(sql_path.read_text(encoding="utf-8"))

def downgrade():
    # Intentionally irreversible: preserve customer financial data.
    pass
