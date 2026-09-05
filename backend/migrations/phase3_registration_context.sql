-- Phase 3 compatibility migration.
-- Safe for an existing PostgreSQL database; it does not delete existing data.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS profile_for VARCHAR(40) NOT NULL DEFAULT 'self';

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS relationship VARCHAR(80);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS registration_location VARCHAR(200);

-- The application bootstrap seeds the single admin account.
-- Public registration always creates role='user'.
