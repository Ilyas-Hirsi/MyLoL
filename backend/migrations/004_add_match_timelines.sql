-- Per-minute laning-phase timeline series for each (user, match).
-- Idempotent: safe to run more than once.

CREATE TABLE IF NOT EXISTS match_timelines (
    id                  SERIAL PRIMARY KEY,
    match_id            VARCHAR(50) NOT NULL UNIQUE,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    champion            VARCHAR(50),
    opponent_champion   VARCHAR(50),
    team_position       VARCHAR(20),
    cs_series           JSON,
    opponent_cs_series  JSON,
    gold_diff_series    JSON,
    xp_diff_series      JSON,
    cs_diff_at_10       INTEGER,
    cs_diff_at_15       INTEGER,
    gold_diff_at_10     INTEGER,
    gold_diff_at_15     INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_match_timelines_user_id ON match_timelines(user_id);
CREATE INDEX IF NOT EXISTS idx_match_timelines_match_id ON match_timelines(match_id);
CREATE INDEX IF NOT EXISTS idx_match_timelines_user_opponent
    ON match_timelines(user_id, opponent_champion);
