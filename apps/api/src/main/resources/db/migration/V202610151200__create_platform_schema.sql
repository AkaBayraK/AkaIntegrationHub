-- rollback: DROP TABLE platform.installation; (forward-fix: yeni bir V…__revert_installation migration'ı ile)
CREATE TABLE IF NOT EXISTS platform.installation (
    id           SMALLINT     PRIMARY KEY DEFAULT 1,
    installed_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    edition      VARCHAR(16)  NOT NULL DEFAULT 'self-hosted',
    CONSTRAINT chk_installation_singleton CHECK (id = 1),
    CONSTRAINT chk_installation_edition CHECK (edition IN ('saas', 'self-hosted'))
);

INSERT INTO platform.installation (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
