-- Key users by their Riot PUUID instead of a surrogate integer id.
--
-- A user IS their PUUID: it is assigned by Riot and it is what every Riot API
-- call is made with. The surrogate `users.id` added a second identity that had
-- to be looked up before any real work could happen, and `riot_id` was indexed
-- as though it were a key when it is only a display name.
--
-- Runs as a single transaction. The backfill is checked before anything is
-- dropped, so a partial mapping aborts rather than stranding rows.

BEGIN;

-- 1. Give every child table the new key.
ALTER TABLE matches          ADD COLUMN IF NOT EXISTS user_puuid VARCHAR(100);
ALTER TABLE champion_mastery ADD COLUMN IF NOT EXISTS user_puuid VARCHAR(100);
ALTER TABLE matchup_stats    ADD COLUMN IF NOT EXISTS user_puuid VARCHAR(100);
ALTER TABLE match_timelines  ADD COLUMN IF NOT EXISTS user_puuid VARCHAR(100);

-- 2. Backfill it from the join that is about to be removed.
UPDATE matches          c SET user_puuid = u.puuid FROM users u WHERE c.user_id = u.id;
UPDATE champion_mastery c SET user_puuid = u.puuid FROM users u WHERE c.user_id = u.id;
UPDATE matchup_stats    c SET user_puuid = u.puuid FROM users u WHERE c.user_id = u.id;
UPDATE match_timelines  c SET user_puuid = u.puuid FROM users u WHERE c.user_id = u.id;

-- 3. Refuse to go further if any row failed to map. Dropping user_id after a
--    partial backfill would destroy the only way to recover the association.
DO $$
DECLARE orphaned BIGINT;
BEGIN
    SELECT (SELECT count(*) FROM matches          WHERE user_puuid IS NULL)
         + (SELECT count(*) FROM champion_mastery WHERE user_puuid IS NULL)
         + (SELECT count(*) FROM matchup_stats    WHERE user_puuid IS NULL)
         + (SELECT count(*) FROM match_timelines  WHERE user_puuid IS NULL)
      INTO orphaned;

    IF orphaned > 0 THEN
        RAISE EXCEPTION
            'Aborting: % child row(s) could not be mapped to a puuid.', orphaned;
    END IF;
END $$;

-- 4. Drop the old foreign keys, then the old column. Postgres drops the
--    indexes and NOT NULL constraints that depend on user_id along with it.
ALTER TABLE matches          DROP CONSTRAINT IF EXISTS matches_user_id_fkey;
ALTER TABLE champion_mastery DROP CONSTRAINT IF EXISTS champion_mastery_user_id_fkey;
ALTER TABLE matchup_stats    DROP CONSTRAINT IF EXISTS matchup_stats_user_id_fkey;
ALTER TABLE match_timelines  DROP CONSTRAINT IF EXISTS match_timelines_user_id_fkey;

ALTER TABLE matches          DROP COLUMN IF EXISTS user_id;
ALTER TABLE champion_mastery DROP COLUMN IF EXISTS user_id;
ALTER TABLE matchup_stats    DROP COLUMN IF EXISTS user_id;
ALTER TABLE match_timelines  DROP COLUMN IF EXISTS user_id;

ALTER TABLE matches          ALTER COLUMN user_puuid SET NOT NULL;
ALTER TABLE champion_mastery ALTER COLUMN user_puuid SET NOT NULL;
ALTER TABLE matchup_stats    ALTER COLUMN user_puuid SET NOT NULL;
ALTER TABLE match_timelines  ALTER COLUMN user_puuid SET NOT NULL;

-- 5. Make puuid the primary key. Dropping users_pkey also drops ix_users_id.
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE users DROP COLUMN IF EXISTS id;
DROP INDEX IF EXISTS ix_users_puuid;  -- superseded by the primary key index
ALTER TABLE users ADD PRIMARY KEY (puuid);

-- riot_id is a display name, not an identifier. Nothing should look a user up
-- by it, so it no longer carries an index.
DROP INDEX IF EXISTS ix_users_riot_id;

-- 6. Re-establish the relationships against the new key.
ALTER TABLE matches
    ADD CONSTRAINT matches_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid);
ALTER TABLE champion_mastery
    ADD CONSTRAINT champion_mastery_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid);
ALTER TABLE matchup_stats
    ADD CONSTRAINT matchup_stats_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid);
ALTER TABLE match_timelines
    ADD CONSTRAINT match_timelines_user_puuid_fkey
    FOREIGN KEY (user_puuid) REFERENCES users(puuid);

-- 7. Index the access paths the app actually uses. These mirror the intent of
--    migration 002, which was written against user_id.
CREATE INDEX IF NOT EXISTS idx_matches_user_puuid
    ON matches(user_puuid);
CREATE INDEX IF NOT EXISTS idx_matches_user_puuid_game_creation
    ON matches(user_puuid, game_creation);
CREATE INDEX IF NOT EXISTS idx_matches_user_puuid_position
    ON matches(user_puuid, team_position);
CREATE INDEX IF NOT EXISTS idx_matches_user_puuid_game_mode
    ON matches(user_puuid, game_mode);
CREATE INDEX IF NOT EXISTS idx_matches_opponent_champion
    ON matches(opponent_champion);

CREATE INDEX IF NOT EXISTS idx_champion_mastery_user_puuid
    ON champion_mastery(user_puuid);
CREATE INDEX IF NOT EXISTS idx_matchup_stats_user_puuid
    ON matchup_stats(user_puuid);
CREATE INDEX IF NOT EXISTS idx_match_timelines_user_puuid
    ON match_timelines(user_puuid);
CREATE INDEX IF NOT EXISTS idx_match_timelines_user_puuid_opponent
    ON match_timelines(user_puuid, opponent_champion);

COMMIT;
