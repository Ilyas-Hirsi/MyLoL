# MatchMetrics

**A personal League of Legends analytics platform that tells you which champions _you_ should pick — based on your own match history, not the global meta.**

Sites like op.gg and u.gg optimize for the average player across millions of games. MatchMetrics does the opposite: it ingests your real Riot Match-V5 data and answers the question those tools can't — _"of the champions **I** actually play, which one should **I** pick into this specific opponent?"_ Every number comes from games you personally played. No scraping, no fabricated stats.

---

## Why this is different from op.gg / u.gg

| Global aggregators | MatchMetrics |
| --- | --- |
| "Champion X has a 52% win rate this patch" | "**You** win 61% on Champion X into this lane opponent, over 18 games" |
| Recommends the meta pick | Recommends the pick that has actually worked *for you* |
| Same answer for every player | Personalized to your champion pool and your results |

Win-rate rankings are **confidence-adjusted** with a Wilson score lower bound, so a shiny 2–0 record doesn't outrank a proven 40–60 one. The interface shows the adjusted figure next to every raw percentage rather than hiding the discount.

## Features

- **Personal matchup analysis** — the lane opponents you lose to most, with your KDA, CS/min and damage/min against each, and a "thin sample" marker under five games.
- **"What should I pick into this?"** — for any opponent, every champion you have taken into that matchup, ranked by confidence-adjusted win rate.
- **Per-champion record** — your win rate on one of your champions, and which opponents it beats and loses to.
- **Form** — your last 20 results in sequence, because four losses in a row and four spread over twenty games are the same percentage and a different problem.
- **Riot API ingestion** — Match-V5 with rate-limit-aware requests and exponential backoff.
- **Redis caching** — per-data-type TTLs. The app runs without Redis, with caching disabled.

## Tech stack

**Backend:** FastAPI · PostgreSQL · SQLAlchemy · Redis · Pydantic · JWT auth

**Frontend:** React 18 · TypeScript · Vite · Material UI · TanStack Query · React Router

## Design

The interface is built as a stat sheet rather than a dashboard: structure comes from typography, alignment and hairline rules, and a container has to earn its border. Tokens live in [`frontend/src/theme/tokens.ts`](frontend/src/theme/tokens.ts) and are the single source for every colour, size and spacing step.

- **Spectral** (serif) for titles and headline figures, **Archivo** (grotesk) for everything else.
- `font-variant-numeric: tabular-nums` throughout, so figures sit on a fixed column and don't jitter between refetches.
- One accent — League gold `#C9A227` — plus muted win/loss. Every token passes WCAG AA against all three surface levels.
- No shadows except the dialog. Radius is 0 for data surfaces, 2px for controls, round only for an avatar.

## Architecture

```
backend/
  app/
    api/          # FastAPI routes (auth, users, matchups, champions)
    models/       # SQLAlchemy models (User, Match, ChampionMastery, MatchupStats, MatchTimeline)
    services/     # personal_stats, matchup_analyzer, champion_recommender,
                  #   riot_api, cache_service
    utils/        # auth + database helpers
  config/         # settings

frontend/
  src/
    pages/        # Dashboard, Matchups, Profile, account entry
    components/   # shell, and the data primitives the pages share
    theme/        # design tokens and the MUI theme built from them
    services/     # API client
    hooks/        # data-fetching hooks
    types/        # shared TypeScript types
```

The core is [`personal_stats.py`](backend/app/services/personal_stats.py): aggregation helpers that compute every statistic from the `matches` table with grouped SQL, so the recommender and matchup analyzer never issue one query per champion.

### Identity

**Users are keyed by their Riot PUUID** — there is no surrogate id.

Riot encrypts the PUUID with the API key that requested it, so rotating the key produces a different ciphertext for the same account. Development keys expire every 24 hours, which would otherwise mean a returning player resolving to a brand-new, empty account each day.

Account entry therefore falls back: if no row matches the PUUID Riot just returned, it looks the player up by Riot ID and tag — which do not rotate — and rewrites that row's PUUID. The four child tables carry `ON UPDATE CASCADE`, so their matches, timelines and mastery rows follow automatically. A unique index on `(lower(riot_id), lower(tag))` keeps a rotation from ever producing a duplicate account.

With a persistent API key the fallback simply never fires.

## Quick start

**Prerequisites:** Python 3.11, Node.js 18+, PostgreSQL 13+, and optionally Redis.

### Backend

```bash
cd backend
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Python **3.11** specifically — `psycopg2-binary==2.9.7` has no wheels for 3.12.

Create `backend/.env` first:

```ini
RIOT_API_KEY=RGAPI-your-key-here     # https://developer.riotgames.com
DB_HOST=localhost
DB_PORT=5432
DB_NAME=league_analytics
DB_USER=postgres
DB_PASSWORD=your-password
SECRET_KEY=a-long-random-string      # signs JWTs
DEBUG=True                           # enables /docs; leave unset in deployment
CORS_ORIGINS=http://localhost:3000
```

Tables are created from the models on first run, so a fresh database needs
nothing else.

An **existing** database is brought forward with the SQL in `backend/migrations/`,
applied in filename order. They are plain `psql`-compatible files — there is no
migration runner and no applied-migrations ledger, so check whether a change is
already present before running it. `006` and `007` are written to be safe to
re-run; the earlier ones are not.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

There is no `package.json` at the repository root — `npm run dev` must be run from `frontend/`.

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs (only when `DEBUG` is on) |

## API overview

**Auth** — `POST /auth/login`

One endpoint, no sign-up: it resolves the Riot ID against Riot's account service, then returns the matching user or creates one. Rate limited per client IP.

**Users** — `GET /users/profile`, `GET /users/match-history`, `POST /users/refresh-data`

**Matchups** — `GET /matchups/difficult`, `GET /matchups/details/{opponent}`, `GET /matchups/vs/{champion1}/{champion2}`

**Champions** — `GET /champions/recommendations`, `GET /champions/counters/{champion}`, `GET /champions/stats/{champion}`

## Security notes

- Every data endpoint derives the user from the JWT subject; none accepts a user identifier from the client.
- All database access goes through the SQLAlchemy ORM — no string-built SQL.
- Error responses carry fixed messages; exception detail goes to the log only.
- CORS is an explicit allowlist with credentials disabled, since auth is a Bearer token rather than a cookie.
- `/docs`, `/redoc` and `/openapi.json` are served only when `DEBUG` is enabled.
- The access token is kept in `localStorage`, which is readable by any script running on the page. Tokens expire in 30 minutes and there are no `dangerouslySetInnerHTML`, `eval` or user-rendered HTML paths in the app, but moving to an httpOnly cookie would need CSRF protection added alongside.

## Known issues

- **A Riot ID rename starts a new account.** Riot encrypts PUUIDs per API key, so account entry falls back to matching on Riot ID and tag (see *Identity* above). Change your Riot ID and neither handle matches any more, so you resolve to a fresh, empty account. Riot exposes nothing else that is stable across keys, so there is no clean fix short of a persistent API key.
- React Router carries two moderate advisories for open redirect via backslash paths. The app only ever navigates to fixed internal routes, so it is not reachable here; closing it needs React Router 7.

## Roadmap

- Deploy a live demo (frontend on Vercel, backend + Postgres + Redis containerized)
- Test coverage for the `personal_stats` aggregation layer, plus CI
- Surface the confidence interval on the dashboard as well as in matchup detail

## License

MIT
