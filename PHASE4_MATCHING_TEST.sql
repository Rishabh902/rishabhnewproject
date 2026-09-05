-- Phase 4 matching diagnostics
-- Run these queries in PostgreSQL before testing /api/profiles/matches.

-- 1. Confirm the 50 test users exist.
SELECT COUNT(*) AS user_count FROM users WHERE role = 'user';

-- 2. Confirm profiles and their states.
SELECT status, COUNT(*)
FROM profiles
GROUP BY status
ORDER BY status;

-- 3. Confirm partner preferences.
SELECT COUNT(*) AS preference_count FROM partner_preferences;

-- 4. See active profiles that can enter the matching pool.
SELECT
    p.user_id,
    p.name,
    p.gender,
    p.preferred_location,
    p.profession,
    p.education,
    p.status
FROM profiles p
WHERE p.status = 'ACTIVE'
ORDER BY p.user_id;

-- 5. Check whether there are both genders among ACTIVE profiles.
SELECT gender, COUNT(*)
FROM profiles
WHERE status = 'ACTIVE'
GROUP BY gender
ORDER BY gender;

-- 6. Check missing matching fields.
SELECT
    COUNT(*) FILTER (WHERE preferred_location IS NULL OR TRIM(preferred_location) = '') AS missing_location,
    COUNT(*) FILTER (WHERE profession IS NULL OR TRIM(profession) = '') AS missing_profession,
    COUNT(*) FILTER (WHERE education IS NULL OR TRIM(education) = '') AS missing_qualification
FROM profiles
WHERE status = 'ACTIVE';

-- 7. Inspect preference coverage.
SELECT
    COUNT(*) FILTER (WHERE location IS NOT NULL AND TRIM(location) <> '') AS location_preferences,
    COUNT(*) FILTER (WHERE profession IS NOT NULL AND TRIM(profession) <> '') AS profession_preferences,
    COUNT(*) FILTER (WHERE education IS NOT NULL AND TRIM(education) <> '') AS qualification_preferences
FROM partner_preferences;

-- Important Phase 4 rule:
-- Location/profession/qualification differences no longer block a candidate.
-- They are ranking signals (40/30/30). Gender and configured age/height remain filters.
