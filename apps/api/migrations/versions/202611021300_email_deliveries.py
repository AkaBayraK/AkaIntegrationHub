"""e-posta gönderim kayıtları ve denemeleri (RLS)

Revision ID: 202611021300
Revises: 202611021200
Create Date: 2026-11-02 13:00:00
"""

from alembic import op

revision = "202611021300"
down_revision = "202611021200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS email")
    op.execute(
        """
        CREATE TABLE email.deliveries (
            id                UUID          PRIMARY KEY,
            tenant_id         UUID          NOT NULL REFERENCES tenancy.tenants(id),
            project_id        UUID,
            account_id        UUID          NOT NULL REFERENCES provider.smtp_accounts(id),
            kind              VARCHAR(16)   NOT NULL,
            message_id        VARCHAR(255)  NOT NULL,
            correlation_id    VARCHAR(64),
            idempotency_key   VARCHAR(128)  NOT NULL,
            request_hash      CHAR(64)      NOT NULL,
            recipient         VARCHAR(320)  NOT NULL,
            subject           VARCHAR(255)  NOT NULL,
            status            VARCHAR(24)   NOT NULL,
            attempt_count     INTEGER       NOT NULL DEFAULT 0,
            last_error_code   VARCHAR(64),
            created_by        VARCHAR(255)  NOT NULL,
            created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
            CONSTRAINT chk_delivery_kind CHECK (kind IN ('test', 'notification')),
            CONSTRAINT chk_delivery_status CHECK (status IN
                ('queued', 'sending', 'accepted_by_smtp', 'failed', 'retry_scheduled', 'cancelled')),
            CONSTRAINT uq_delivery_idempotency UNIQUE (tenant_id, idempotency_key)
        )
        """
    )
    op.execute("CREATE INDEX ix_deliveries_tenant_time ON email.deliveries (tenant_id, created_at DESC)")
    op.execute(
        """
        CREATE TABLE email.delivery_attempts (
            id                   UUID         PRIMARY KEY,
            tenant_id            UUID         NOT NULL REFERENCES tenancy.tenants(id),
            delivery_id          UUID         NOT NULL REFERENCES email.deliveries(id),
            account_id           UUID         NOT NULL,
            attempt_no           INTEGER      NOT NULL,
            outcome              VARCHAR(16)  NOT NULL,
            smtp_response_class  VARCHAR(8),
            error_code           VARCHAR(64),
            duration_ms          INTEGER      NOT NULL,
            created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT uq_attempt_no UNIQUE (delivery_id, attempt_no)
        )
        """
    )
    for table in ("email.deliveries", "email.delivery_attempts"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
        )
    op.execute("GRANT USAGE ON SCHEMA email TO aih_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA email TO aih_app")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS email.delivery_attempts")
    op.execute("DROP TABLE IF EXISTS email.deliveries")
