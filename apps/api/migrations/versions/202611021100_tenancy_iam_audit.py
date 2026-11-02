"""tenancy, kimlik sağlayıcı eşlemesi ve append-only audit

Revision ID: 202611021100
Revises: 202610151200
Create Date: 2026-11-02 11:00:00
"""

from alembic import op

revision = "202611021100"
down_revision = "202610151200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS tenancy")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.execute(
        """
        CREATE TABLE tenancy.tenants (
            id          UUID         PRIMARY KEY,
            slug        VARCHAR(64)  NOT NULL UNIQUE,
            name        VARCHAR(200) NOT NULL,
            enabled     BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT chk_tenant_slug CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$')
        )
        """
    )
    # Bir OIDC issuer (ör. BuildingFlow realm'i) tek bir tenant'a bağlanır. Token'daki tenant bilgisi
    # istemciden değil, doğrulanmış issuer eşlemesinden türetilir (ADR-0005/0006).
    op.execute(
        """
        CREATE TABLE tenancy.identity_providers (
            id                  UUID          PRIMARY KEY,
            tenant_id           UUID          NOT NULL REFERENCES tenancy.tenants(id),
            issuer              VARCHAR(512)  NOT NULL UNIQUE,
            jwks_uri            VARCHAR(512),
            allowed_client_ids  TEXT[]        NOT NULL,
            tenant_admin_roles  TEXT[]        NOT NULL DEFAULT '{}',
            viewer_roles        TEXT[]        NOT NULL DEFAULT '{}',
            platform_admin_roles TEXT[]       NOT NULL DEFAULT '{}',
            enabled             BOOLEAN       NOT NULL DEFAULT TRUE,
            created_at          TIMESTAMPTZ   NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE audit.audit_events (
            id             UUID         PRIMARY KEY,
            occurred_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
            tenant_id      UUID,
            actor_subject  VARCHAR(255) NOT NULL,
            actor_issuer   VARCHAR(512),
            actor_via      VARCHAR(32)  NOT NULL DEFAULT 'api',
            action         VARCHAR(100) NOT NULL,
            resource_type  VARCHAR(100) NOT NULL,
            resource_id    VARCHAR(100),
            outcome        VARCHAR(20)  NOT NULL,
            correlation_id VARCHAR(64),
            details        JSONB        NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )
    op.execute("CREATE INDEX ix_audit_tenant_time ON audit.audit_events (tenant_id, occurred_at DESC)")
    op.execute(
        """
        CREATE FUNCTION audit.reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit.audit_events is append-only';
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER trg_audit_append_only BEFORE UPDATE OR DELETE ON audit.audit_events "
        "FOR EACH ROW EXECUTE FUNCTION audit.reject_mutation()"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit.audit_events")
    op.execute("DROP FUNCTION IF EXISTS audit.reject_mutation()")
    op.execute("DROP TABLE IF EXISTS tenancy.identity_providers")
    op.execute("DROP TABLE IF EXISTS tenancy.tenants")
