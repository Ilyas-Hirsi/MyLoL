import React, { useMemo } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import {
  useMatchHistory,
  useDifficultMatchups,
  useChampionRecommendations,
} from '../hooks/useApi';
import { Match } from '../types';
import { color, font, size, space } from '../theme/tokens';
import PageHeader from '../components/PageHeader';
import SectionHeading from '../components/SectionHeading';
import LoadingBar from '../components/LoadingBar';
import EmptyState from '../components/EmptyState';
import RecordBar from '../components/RecordBar';

const FORM_LENGTH = 20;

/**
 * The last 20 results in order, newest last.
 *
 * Sequence is information a win rate throws away — four losses in a row and
 * four losses spread over twenty games are the same percentage and a different
 * situation. The strip is read by sighted users as a shape and by screen
 * readers as the sentence in its aria-label.
 */
const FormStrip: React.FC<{ results: boolean[] }> = ({ results }) => {
  const wins = results.filter(Boolean).length;
  return (
    <Box
      role="img"
      aria-label={`Last ${results.length} games: ${wins} wins, ${results.length - wins} losses, oldest first`}
      sx={{ display: 'flex', gap: '3px', alignItems: 'flex-end' }}
    >
      {results.map((win, i) => (
        <Box
          key={i}
          sx={{
            width: 10,
            height: win ? 22 : 12,
            backgroundColor: win ? color.win : color.loss,
            opacity: 0.35 + (0.65 * (i + 1)) / results.length,
          }}
        />
      ))}
    </Box>
  );
};

const DashboardPage: React.FC = () => {
  const { data: matches, isLoading: matchesLoading, error: matchesError } = useMatchHistory();
  const { data: difficult, isLoading: difficultLoading } = useDifficultMatchups();
  const { data: recommendations, isLoading: recsLoading } = useChampionRecommendations();

  const summary = useMemo(() => {
    const all: Match[] = matches ?? [];
    const sorted = [...all].sort((a, b) => {
      const ta = a.game_creation ? Date.parse(a.game_creation) : 0;
      const tb = b.game_creation ? Date.parse(b.game_creation) : 0;
      return ta - tb;
    });
    const wins = all.filter((m) => m.win).length;
    const recent = sorted.slice(-FORM_LENGTH);
    return {
      games: all.length,
      wins,
      losses: all.length - wins,
      winRate: all.length ? (wins / all.length) * 100 : 0,
      form: recent.map((m) => m.win),
      formWins: recent.filter((m) => m.win).length,
    };
  }, [matches]);

  const isLoading = matchesLoading || difficultLoading || recsLoading;

  if (matchesError) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <Typography role="alert" variant="body2" sx={{ color: color.loss }}>
          Could not load your matches. Check the backend is running, then reload.
        </Typography>
      </>
    );
  }

  if (!isLoading && summary.games === 0) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <EmptyState
          title="No matches recorded yet."
          detail="Fetch your match history from the rail on the left, then your record and the matchups costing you games will appear here."
        />
      </>
    );
  }

  return (
    <>
      {isLoading && <LoadingBar label="Loading your record" />}

      <PageHeader
        title="Dashboard"
        description="Your record so far, and the matchups costing you games."
      />

      {/* The headline fact, set in the display face at a size nothing else on
          the page competes with. No card: it is the first thing on the page,
          which is emphasis enough. */}
      <Box component="section" sx={{ marginBottom: `${space[8]}px` }}>
        <Typography variant="overline" sx={{ color: color.textLo, display: 'block' }}>
          Overall record
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'baseline',
            flexWrap: 'wrap',
            gap: `${space[3]}px ${space[4]}px`,
            marginTop: `${space[2]}px`,
          }}
        >
          <Typography
            sx={{ fontFamily: font.display, fontWeight: 600, fontSize: 44, lineHeight: 1, color: color.textHi }}
          >
            <Box component="span" sx={{ color: color.win }}>{summary.wins}</Box>
            <Box component="span" sx={{ color: color.textLo }}>–</Box>
            <Box component="span" sx={{ color: color.loss }}>{summary.losses}</Box>
          </Typography>
          <Typography sx={{ fontSize: 15, color: color.text }}>
            {summary.winRate.toFixed(1)}% across {summary.games} games
          </Typography>
        </Box>
        <Box sx={{ marginTop: `${space[4]}px` }}>
          <RecordBar winRate={summary.winRate} width={260} />
        </Box>

        {summary.form.length > 0 && (
          <Box sx={{ marginTop: `${space[6]}px` }}>
            <Typography variant="overline" sx={{ color: color.textLo, display: 'block' }}>
              Last {summary.form.length} games
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: `${space[4]}px`, marginTop: `${space[3]}px` }}>
              <FormStrip results={summary.form} />
              <Typography variant="caption">
                {summary.formWins}W {summary.form.length - summary.formWins}L
              </Typography>
            </Box>
          </Box>
        )}
      </Box>

      {/* Asymmetric on purpose: what is going wrong deserves more width than
          what to do about it, and neither is a card. */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: 'minmax(0, 3fr) minmax(0, 2fr)' },
          gap: `${space[8]}px ${space[7]}px`,
        }}
      >
        <Box component="section">
          <SectionHeading trailing={difficult && difficult.length > 5 ? `top 5 of ${difficult.length}` : undefined}>
            Where you are losing
          </SectionHeading>

          {!difficultLoading && (!difficult || difficult.length === 0) ? (
            <EmptyState
              title="No losing matchups."
              detail="No opponent currently has a winning record against you."
            />
          ) : (
            <Box component="ul" sx={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {(difficult ?? []).slice(0, 5).map((m: any) => (
                <Box
                  component="li"
                  key={m.champion}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: `${space[4]}px`,
                    paddingBlock: `${space[3]}px`,
                    borderBottom: `1px solid ${color.rule}`,
                  }}
                >
                  <Typography sx={{ fontSize: 14, color: color.textHi, flex: 1, minWidth: 0 }}>
                    {m.champion}
                  </Typography>
                  <Typography sx={{ fontSize: 13, whiteSpace: 'nowrap' }}>
                    <Box component="span" sx={{ color: color.win }}>{m.wins}</Box>
                    <Box component="span" sx={{ color: color.textLo }}>–</Box>
                    <Box component="span" sx={{ color: color.loss }}>{m.losses}</Box>
                  </Typography>
                  <RecordBar winRate={m.win_rate} />
                  <Typography sx={{ fontSize: 13, color: color.textHi, width: 40, textAlign: 'right' }}>
                    {m.win_rate.toFixed(0)}%
                  </Typography>
                </Box>
              ))}
            </Box>
          )}

          <Button
            component={RouterLink}
            to="/matchups"
            variant="text"
            sx={{ paddingInline: 0, minWidth: 0, marginTop: `${space[4]}px` }}
          >
            See all matchups
          </Button>
        </Box>

        <Box component="section">
          <SectionHeading>Picks that have worked</SectionHeading>

          {!recsLoading && (!recommendations || recommendations.length === 0) ? (
            <EmptyState
              title="No suggestions yet."
              detail="These appear once you have enough games against the opponents beating you."
            />
          ) : (
            <Box component="ul" sx={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {(recommendations ?? []).map((r: any) => (
                <Box
                  component="li"
                  key={r.champion}
                  sx={{ paddingBlock: `${space[4]}px`, borderBottom: `1px solid ${color.rule}` }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'baseline', gap: `${space[3]}px` }}>
                    <Typography sx={{ fontSize: 14, fontWeight: 500, color: color.textHi, flex: 1 }}>
                      {r.champion}
                    </Typography>
                    <Typography sx={{ fontSize: 13, color: color.textHi }}>
                      {r.counter_win_rate.toFixed(0)}%
                    </Typography>
                  </Box>
                  {/* The backend writes this sentence and it already carries the
                      sample size, which is the part that matters. */}
                  <Typography variant="body2" sx={{ color: color.textLo, marginTop: `${space[1]}px`, maxWidth: size.prose }}>
                    {r.reason}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </>
  );
};

export default DashboardPage;
