"""Müşteri Redis sunucuları için lisans beyanı

Revision ID: 202611031100
Revises: 202611031000
Create Date: 2026-11-03 11:00:00
"""

from alembic import op

revision = "202611031100"
down_revision = "202611031000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE provider.cache_accounts
            ADD COLUMN license_type             VARCHAR(32),
            ADD COLUMN license_holder           VARCHAR(200),
            ADD COLUMN license_reference        VARCHAR(120),
            ADD COLUMN license_expires_on       DATE,
            ADD COLUMN license_key_ref          UUID REFERENCES provider.secrets(id),
            ADD COLUMN license_acknowledged_at  TIMESTAMPTZ,
            ADD COLUMN license_acknowledged_by  VARCHAR(255),
            ADD CONSTRAINT chk_cache_license_type CHECK (
                license_type IS NULL
                OR license_type IN ('rsal-2.0', 'sspl-1.0', 'agpl-3.0', 'redis-enterprise', 'redis-cloud')
            ),
            ADD CONSTRAINT chk_cache_redis_license CHECK (
                provider_type <> 'redis' OR (license_type IS NOT NULL AND license_acknowledged_at IS NOT NULL)
            ),
            ADD CONSTRAINT chk_cache_valkey_no_license CHECK (provider_type <> 'valkey' OR license_type IS NULL)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE provider.cache_accounts
            DROP CONSTRAINT IF EXISTS chk_cache_valkey_no_license,
            DROP CONSTRAINT IF EXISTS chk_cache_redis_license,
            DROP CONSTRAINT IF EXISTS chk_cache_license_type,
            DROP COLUMN IF EXISTS license_acknowledged_by,
            DROP COLUMN IF EXISTS license_acknowledged_at,
            DROP COLUMN IF EXISTS license_key_ref,
            DROP COLUMN IF EXISTS license_expires_on,
            DROP COLUMN IF EXISTS license_reference,
            DROP COLUMN IF EXISTS license_holder,
            DROP COLUMN IF EXISTS license_type
        """
    )
