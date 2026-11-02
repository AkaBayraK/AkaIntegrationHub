"""create platform schema (Flyway V202610151200 karşılığı)

Flyway ile kurulmuş veritabanlarında da güvenle çalışır (IF NOT EXISTS / ON CONFLICT).

Revision ID: 202610151200
Revises:
Create Date: 2026-10-15 12:00:00
"""

from alembic import op

revision = "202610151200"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS platform")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS platform.installation (
            id           SMALLINT     PRIMARY KEY DEFAULT 1,
            installed_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
            edition      VARCHAR(16)  NOT NULL DEFAULT 'self-hosted',
            CONSTRAINT chk_installation_singleton CHECK (id = 1),
            CONSTRAINT chk_installation_edition CHECK (edition IN ('saas', 'self-hosted'))
        )
        """
    )
    op.execute("INSERT INTO platform.installation (id) VALUES (1) ON CONFLICT (id) DO NOTHING")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform.installation")
