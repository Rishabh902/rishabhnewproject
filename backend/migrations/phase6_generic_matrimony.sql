-- Safe additive migration for existing Phase-3/5 PostgreSQL databases.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS caste VARCHAR(150);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS degree VARCHAR(200);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS weight_kg INTEGER;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS state VARCHAR(100);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS district VARCHAR(120);
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS city_or_village VARCHAR(150);

CREATE TABLE IF NOT EXISTS profile_photos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    original_name VARCHAR(255),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_profile_photos_user_id ON profile_photos(user_id);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
