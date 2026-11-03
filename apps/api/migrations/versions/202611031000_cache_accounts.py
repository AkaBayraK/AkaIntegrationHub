"""Cache (Valkey/Redis) hesapları ve sağlayıcı yönetim arayüzü adresi

Revision ID: 202611031000
Revises: 202611021300
Create Date: 2026-11-03 10:00:00
"""

from alembic import op

revision = "202611031000"
down_revision = "202611021300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE provider.smtp_accounts ADD COLUMN console_url VARCHAR(2048)")
    op.execute(
        """
        CREATE TABLE provider.cache_accounts (
            id                 UUID          PRIMARY KEY,
            tenant_id          UUID          NOT NULL REFERENCES tenancy.tenants(id),
            project_id         UUID,
            name               VARCHAR(120)  NOT NULL,
            provider_type      VARCHAR(32)   NOT NULL,
            host               VARCHAR(253)  NOT NULL,
            port               INTEGER       NOT NULL CHECK (port BETWEEN 1 AND 65535),
            tls_enabled        BOOLEAN       NOT NULL DEFAULT FALSE,
            auth_mode          VARCHAR(16)   NOT NULL,
            username           VARCHAR(255),
            secret_ref         UUID          REFERENCES provider.secrets(id),
            database_index     INTEGER       NOT NULL DEFAULT 0 CHECK (database_index BETWEEN 0 AND 15),
            key_prefix         VARCHAR(120),
            environment        VARCHAR(16)   NOT NULL,
            enabled            BOOLEAN       NOT NULL DEFAULT TRUE,
            is_default         BOOLEAN       NOT NULL DEFAULT FALSE,
            timeout_seconds    INTEGER       NOT NULL DEFAULT 5 CHECK (timeout_seconds BETWEEN 1 AND 60),
            console_url        VARCHAR(2048),
            last_test_at       TIMESTAMPTZ,
            last_test_outcome  VARCHAR(16),
            server_version     VARCHAR(64),
            version            INTEGER       NOT NULL DEFAULT 1,
            created_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
            created_by         VARCHAR(255)  NOT NULL,
            updated_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_by         VARCHAR(255)  NOT NULL,
            CONSTRAINT chk_cache_provider CHECK (provider_type IN ('valkey', 'redis')),
            CONSTRAINT chk_cache_auth CHECK (auth_mode IN ('none', 'password', 'acl')),
            CONSTRAINT chk_cache_env CHECK (environment IN ('test', 'production')),
            CONSTRAINT chk_cache_prod_auth CHECK (environment <> 'production' OR auth_mode <> 'none'),
            CONSTRAINT chk_cache_default_enabled CHECK (NOT is_default OR enabled),
            CONSTRAINT uq_cache_name UNIQUE (tenant_id, name)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_cache_single_default ON provider.cache_accounts "
        "(tenant_id, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'::uuid), environment) "
        "WHERE is_default"
    )
    op.execute("CREATE INDEX ix_cache_accounts_tenant ON provider.cache_accounts (tenant_id, environment)")
    op.execute("ALTER TABLE provider.cache_accounts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE provider.cache_accounts FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON provider.cache_accounts "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
        "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON provider.cache_accounts TO aih_app")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS provider.cache_accounts")
    op.execute("ALTER TABLE provider.smtp_accounts DROP COLUMN IF EXISTS console_url")
