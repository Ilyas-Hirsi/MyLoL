-- Survive Riot re-encrypting PUUIDs.
--
-- Riot encrypts the PUUID with the API key that requested it, so rotating the
-- key produces a different ciphertext for the same account — and development
-- keys expire every 24 hours. Without this, a returning player misses the
-- lookup and is given a brand-new, empty account on every rotation.
--
-- Account entry falls back to matching on Riot ID and tag, which do not rotate,
-- and rewrites that row's PUUID. That rewrite needs two things from the schema:
-- foreign keys that follow the change, and a uniqueness rule so a rotation can
-- never leave two rows for one player.
--
-- Idempotent: safe to re-run on a database that already has it.

BEGIN;

-- 1. Clear out any duplicate account rows left by earlier rotations, but only
--    where they own no data. A duplicate holding matches is not something this
--    migration should silently resolve.
DELETE FROM users u
WHERE EXISTS (
          SELECT 1 FROM users other
          WHERE lower(other.riot_id) = lower(u.riot_id)
            AND lower(other.tag)     = lower(u.tag)
            AND other.puuid <> u.puuid
      )
  AND NOT EXISTS (SELECT 1 FROM matches          c WHERE c.user_puuid = u.puuid)
  AND NOT EXISTS (SELECT 1 FROM champion_mastery c WHERE c.user_puuid = u.puuid)
  AND NOT EXISTS (SELECT 1 FROM matchup_stats    c WHERE c.user_puuid = u.puuid)
  AND NOT EXISTS (SELECT 1 FROM match_timelines  c WHERE c.user_puuid = u.puuid);

-- 2. A Riot ID identifies exactly one account, so the table should say so.
--    The absence of this rule is what allowed the duplicates above.
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_riot_id_tag_lower
    ON users (lower(riot_id), lower(tag));

-- 3. Let a user's PUUID be rewritten, and have every child row follow.
ALTER TABLE matches DROP CONSTRAINT IF EXISTS matches_user_puuid_fkey;
ALTER TABLE matches ADD CONSTRAINT matches_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid) ON UPDATE CASCADE;

ALTER TABLE champion_mastery DROP CONSTRAINT IF EXISTS champion_mastery_user_puuid_fkey;
ALTER TABLE champion_mastery ADD CONSTRAINT champion_mastery_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid) ON UPDATE CASCADE;

ALTER TABLE matchup_stats DROP CONSTRAINT IF EXISTS matchup_stats_user_puuid_fkey;
ALTER TABLE matchup_stats ADD CONSTRAINT matchup_stats_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid) ON UPDATE CASCADE;

ALTER TABLE match_timelines DROP CONSTRAINT IF EXISTS match_timelines_user_puuid_fkey;
ALTER TABLE match_timelines ADD CONSTRAINT match_timelines_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid) ON UPDATE CASCADE;

COMMIT;
