"""SMTP hesapları, şifreli secret store, bağlantı testleri ve RLS

Uygulama tenant bağlamında ``SET LOCAL ROLE aih_app`` ile çalışır. ``aih_app`` süper kullanıcı değildir,
bu yüzden ``FORCE ROW LEVEL SECURITY`` politikaları geliştirme ortamında (süper kullanıcı bağlantısıyla) da uygulanır.

Revision ID: 202611021200
Revises: 202611021100
Create Date: 2026-11-02 12:00:00
"""

from alembic import op

revision = "202611021200"
down_revision = "202611021100"
branch_labels = None
depends_on = None

TENANT_TABLES = ("provider.secrets", "provider.smtp_accounts", "provider.smtp_connection_tests")


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'aih_app') THEN
                CREATE ROLE aih_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
            END IF;
            EXECUTE format('GRANT aih_app TO %I', current_user);
        END
        $$
        """
    )
    op.execute("CREATE SCHEMA IF NOT EXISTS provider")
    op.execute(
        """
        CREATE TABLE provider.secrets (
            id          UUID         PRIMARY KEY,
            tenant_id   UUID         NOT NULL REFERENCES tenancy.tenants(id),
            kind        VARCHAR(32)  NOT NULL,
            key_id      VARCHAR(32)  NOT NULL,
            ciphertext  BYTEA        NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            rotated_at  TIMESTAMPTZ
        )
        """
    )
    op.execute(
        """
        CREATE TABLE provider.smtp_accounts (
            id                     UUID          PRIMARY KEY,
            tenant_id              UUID          NOT NULL REFERENCES tenancy.tenants(id),
            project_id             UUID,
            name                   VARCHAR(120)  NOT NULL,
            provider_type          VARCHAR(32)   NOT NULL,
            host                   VARCHAR(253)  NOT NULL,
            port                   INTEGER       NOT NULL CHECK (port BETWEEN 1 AND 65535),
            tls_mode               VARCHAR(16)   NOT NULL,
            auth_mode              VARCHAR(16)   NOT NULL,
            username               VARCHAR(320),
            secret_ref             UUID          REFERENCES provider.secrets(id),
            sender_address         VARCHAR(320)  NOT NULL,
            sender_name            VARCHAR(200),
            reply_to               VARCHAR(320),
            environment            VARCHAR(16)   NOT NULL,
            enabled                BOOLEAN       NOT NULL DEFAULT TRUE,
            is_default             BOOLEAN       NOT NULL DEFAULT FALSE,
            priority               INTEGER       NOT NULL DEFAULT 100,
            timeout_seconds        INTEGER       NOT NULL DEFAULT 15 CHECK (timeout_seconds BETWEEN 1 AND 120),
            rate_limit_per_minute  INTEGER       CHECK (rate_limit_per_minute > 0),
            last_test_at           TIMESTAMPTZ,
            last_test_outcome      VARCHAR(16),
            last_success_send_at   TIMESTAMPTZ,
            version                INTEGER       NOT NULL DEFAULT 1,
            created_at             TIMESTAMPTZ   NOT NULL DEFAULT now(),
            created_by             VARCHAR(255)  NOT NULL,
            updated_at             TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_by             VARCHAR(255)  NOT NULL,
            CONSTRAINT chk_smtp_tls CHECK (tls_mode IN ('starttls', 'implicit', 'none')),
            CONSTRAINT chk_smtp_auth CHECK (auth_mode IN ('smtp_auth', 'oauth2', 'none')),
            CONSTRAINT chk_smtp_env CHECK (environment IN ('test', 'production')),
            CONSTRAINT chk_smtp_prod_tls CHECK (environment <> 'production' OR tls_mode <> 'none'),
            CONSTRAINT chk_smtp_default_enabled CHECK (NOT is_default OR enabled),
            CONSTRAINT uq_smtp_name UNIQUE (tenant_id, name)
        )
        """
    )
    # Tenant + proje + ortam başına tek varsayılan hesap.
    op.execute(
        "CREATE UNIQUE INDEX uq_smtp_single_default ON provider.smtp_accounts "
        "(tenant_id, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'::uuid), environment) "
        "WHERE is_default"
    )
    op.execute("CREATE INDEX ix_smtp_accounts_tenant ON provider.smtp_accounts (tenant_id, environment, priority)")
    op.execute(
        """
        CREATE TABLE provider.smtp_connection_tests (
            id           UUID          PRIMARY KEY,
            tenant_id    UUID          NOT NULL REFERENCES tenancy.tenants(id),
            account_id   UUID          NOT NULL REFERENCES provider.smtp_accounts(id),
            test_type    VARCHAR(32)   NOT NULL,
            outcome      VARCHAR(16)   NOT NULL,
            error_code   VARCHAR(64),
            steps        JSONB         NOT NULL DEFAULT '[]'::jsonb,
            duration_ms  INTEGER       NOT NULL,
            created_at   TIMESTAMPTZ   NOT NULL DEFAULT now(),
            created_by   VARCHAR(255)  NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_smtp_tests_account ON provider.smtp_connection_tests (tenant_id, account_id, created_at DESC)"
    )

    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
        )

    op.execute("GRANT USAGE ON SCHEMA provider, tenancy, audit, platform TO aih_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA provider TO aih_app")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA tenancy TO aih_app")
    op.execute("GRANT INSERT ON audit.audit_events TO aih_app")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS provider.smtp_connection_tests")
    op.execute("DROP TABLE IF EXISTS provider.smtp_accounts")
    op.execute("DROP TABLE IF EXISTS provider.secrets")
