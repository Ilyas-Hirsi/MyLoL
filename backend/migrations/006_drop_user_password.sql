-- Remove the vestigial password column.
--
-- Account entry has no password: the Riot ID is verified against Riot's account
-- service and the matching user is returned or created. The column held '' for
-- every row and existed only because an earlier design had a sign-up step.

BEGIN;

ALTER TABLE users DROP COLUMN IF EXISTS hashed_password;

COMMIT;
