"""SMS hesapları, kontör hareketleri ve gönderim kayıtları

Revision ID: 202611031200
Revises: 202611031100
Create Date: 2026-11-03 12:00:00
"""

from alembic import op

revision = "202611031200"
down_revision = "202611031100"
branch_labels = None
depends_on = None

TENANT_TABLES = ("provider.sms_accounts", "provider.sms_credit_transactions", "sms.messages")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE provider.sms_accounts (
            id                    UUID          PRIMARY KEY,
            tenant_id             UUID          NOT NULL REFERENCES tenancy.tenants(id),
            project_id            UUID,
            name                  VARCHAR(120)  NOT NULL,
            provider_type         VARCHAR(32)   NOT NULL,
            sender_header         VARCHAR(11)   NOT NULL,
            username              VARCHAR(100),
            secret_ref            UUID          REFERENCES provider.secrets(id),
            environment           VARCHAR(16)   NOT NULL,
            enabled               BOOLEAN       NOT NULL DEFAULT TRUE,
            is_default            BOOLEAN       NOT NULL DEFAULT FALSE,
            credit_balance        INTEGER       NOT NULL DEFAULT 0 CHECK (credit_balance BETWEEN 0 AND 10000000),
            low_credit_threshold  INTEGER       NOT NULL DEFAULT 100 CHECK (low_credit_threshold >= 0),
            console_url           VARCHAR(2048),
            last_test_at          TIMESTAMPTZ,
            last_test_outcome     VARCHAR(16),
            version               INTEGER       NOT NULL DEFAULT 1,
            created_at            TIMESTAMPTZ   NOT NULL DEFAULT now(),
            created_by            VARCHAR(255)  NOT NULL,
            updated_at            TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_by            VARCHAR(255)  NOT NULL,
            CONSTRAINT chk_sms_provider CHECK (
                provider_type IN ('mock_test', 'netgsm', 'iletimerkezi', 'verimor', 'turkcell')
            ),
            CONSTRAINT chk_sms_env CHECK (environment IN ('test', 'production')),
            CONSTRAINT chk_sms_mock_test_only CHECK (provider_type <> 'mock_test' OR environment = 'test'),
            CONSTRAINT chk_sms_default_enabled CHECK (NOT is_default OR enabled),
            CONSTRAINT uq_sms_name UNIQUE (tenant_id, name)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_sms_single_default ON provider.sms_accounts "
        "(tenant_id, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'::uuid), environment) "
        "WHERE is_default"
    )
    op.execute(
        """
        CREATE TABLE provider.sms_credit_transactions (
            id             UUID          PRIMARY KEY,
            tenant_id      UUID          NOT NULL REFERENCES tenancy.tenants(id),
            account_id     UUID          NOT NULL REFERENCES provider.sms_accounts(id),
            kind           VARCHAR(16)   NOT NULL CHECK (kind IN ('load', 'consume', 'refund', 'adjust')),
            quantity       INTEGER       NOT NULL CHECK (quantity <> 0),
            balance_after  INTEGER       NOT NULL CHECK (balance_after >= 0),
            reason         VARCHAR(200),
            message_id     UUID,
            created_by     VARCHAR(255)  NOT NULL,
            created_at     TIMESTAMPTZ   NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_sms_credit_account ON provider.sms_credit_transactions (tenant_id, account_id, created_at DESC)"
    )
    op.execute("CREATE SCHEMA IF NOT EXISTS sms")
    op.execute(
        """
        CREATE TABLE sms.messages (
            id                   UUID          PRIMARY KEY,
            tenant_id            UUID          NOT NULL REFERENCES tenancy.tenants(id),
            project_id           UUID,
            account_id           UUID          NOT NULL REFERENCES provider.sms_accounts(id),
            kind                 VARCHAR(16)   NOT NULL,
            purpose              VARCHAR(16)   NOT NULL,
            type_code            VARCHAR(64),
            reference_type       VARCHAR(64),
            reference_id         VARCHAR(64),
            consent_reference    VARCHAR(120),
            idempotency_key      VARCHAR(128)  NOT NULL,
            request_hash         VARCHAR(64)   NOT NULL,
            phone_masked         VARCHAR(20)   NOT NULL,
            phone_fingerprint    VARCHAR(64)   NOT NULL,
            segments             INTEGER       NOT NULL CHECK (segments > 0),
            credit_cost          INTEGER       NOT NULL CHECK (credit_cost > 0),
            status               VARCHAR(16)   NOT NULL,
            provider_type        VARCHAR(32)   NOT NULL,
            provider_message_id  VARCHAR(100),
            error_code           VARCHAR(64),
            correlation_id       VARCHAR(64),
            duration_ms          INTEGER,
            created_by           VARCHAR(255)  NOT NULL,
            created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),
            CONSTRAINT chk_sms_message_status CHECK (status IN ('queued', 'sent', 'failed', 'unknown')),
            CONSTRAINT chk_sms_message_purpose CHECK (
                purpose IN ('otp', 'security', 'transactional', 'operational', 'marketing')
            ),
            CONSTRAINT chk_sms_marketing_consent CHECK (purpose <> 'marketing' OR consent_reference IS NOT NULL),
            CONSTRAINT uq_sms_idempotency UNIQUE (tenant_id, idempotency_key)
        )
        """
    )
    op.execute("CREATE INDEX ix_sms_messages_tenant ON sms.messages (tenant_id, created_at DESC)")
    op.execute("CREATE INDEX ix_sms_messages_account ON sms.messages (tenant_id, account_id, created_at DESC)")
    op.execute("CREATE INDEX ix_sms_messages_phone ON sms.messages (tenant_id, phone_fingerprint)")
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
        )
    op.execute("GRANT USAGE ON SCHEMA sms TO aih_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON provider.sms_accounts, provider.sms_credit_transactions TO aih_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON sms.messages TO aih_app")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sms.messages")
    op.execute("DROP SCHEMA IF EXISTS sms")
    op.execute("DROP TABLE IF EXISTS provider.sms_credit_transactions")
    op.execute("DROP TABLE IF EXISTS provider.sms_accounts")
