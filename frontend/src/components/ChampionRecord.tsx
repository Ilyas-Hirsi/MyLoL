import React, { useEffect, useMemo } from 'react';
import Box from '@mui/material/Box';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useChampionStats, useMatchHistory } from '../hooks/useApi';
import { formatKDA } from '../utils/helpers';
import { color, space } from '../theme/tokens';
import SectionHeading from './SectionHeading';
import StatList from './StatList';
import RecordBar from './RecordBar';
import RecordTable from './RecordTable';
import EmptyState from './EmptyState';
import LoadingBar from './LoadingBar';

/**
 * Your record on one of your own champions, and which opponents it wins and
 * loses into.
 *
 * This is what the unrouted ChampionsPage did, minus the half that duplicated
 * the dashboard. Its champion search took free text and guessed at
 * capitalisation ("master yi" → "Master Yi", which the API does not accept);
 * the list of champions you have actually played comes straight out of match
 * history, so there is nothing to mistype and nothing to guess.
 */
const ChampionRecord: React.FC<{ champion: string; onChange: (c: string) => void }> = ({
  champion,
  onChange,
}) => {
  const { data: matches, isLoading: matchesLoading } = useMatchHistory();
  const { data: stats, isLoading: statsLoading, error } = useChampionStats(champion);

  const played = useMemo(() => {
    const counts = new Map<string, number>();
    (matches ?? []).forEach((m) => counts.set(m.champion, (counts.get(m.champion) ?? 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [matches]);

  // Open on the champion with the most games rather than an empty select.
  useEffect(() => {
    if (!champion && played.length > 0) onChange(played[0][0]);
  }, [champion, played, onChange]);

  if (matchesLoading) return <LoadingBar label="Loading your champions" />;

  if (played.length === 0) {
    return (
      <EmptyState
        title="No champions to show yet."
        detail="Once matches are recorded, every champion you have played will be listed here."
      />
    );
  }

  const losses = stats ? stats.games - Math.round((stats.win_rate / 100) * stats.games) : 0;
  const wins = stats ? stats.games - losses : 0;

  return (
    <>
      {statsLoading && <LoadingBar label={`Loading your record on ${champion}`} />}

      <Box sx={{ paddingBottom: `${space[5]}px` }}>
        <TextField
          select
          label="Champion"
          value={champion}
          onChange={(e) => onChange(e.target.value)}
          size="small"
          sx={{ minWidth: 240 }}
        >
          {played.map(([name, count]) => (
            <MenuItem key={name} value={name}>
              {name}
              <Box component="span" sx={{ color: color.textLo, marginLeft: `${space[2]}px` }}>
                {count}
              </Box>
            </MenuItem>
          ))}
        </TextField>
      </Box>

      {error && (
        <Typography role="alert" variant="body2" sx={{ color: color.loss }}>
          Could not load your record on {champion}.
        </Typography>
      )}

      {stats && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: `${space[7]}px` }}>
          <Box>
            <Typography sx={{ fontSize: 14, color: color.text }}>
              <Box component="span" sx={{ color: color.win }}>
                {wins}
              </Box>
              <Box component="span" sx={{ color: color.textLo }}>
                –
              </Box>
              <Box component="span" sx={{ color: color.loss }}>
                {losses}
              </Box>{' '}
              in {stats.games} {stats.games === 1 ? 'game' : 'games'} — {stats.win_rate}% win rate
            </Typography>
            <Box sx={{ marginTop: `${space[3]}px` }}>
              <RecordBar winRate={stats.win_rate} width={200} />
            </Box>
          </Box>

          <Box>
            <SectionHeading as="h3">Your averages on {champion}</SectionHeading>
            {/* ban_rate is not shown: the backend hardcodes it to 0.0 because
                there is no personal analogue for a ban. */}
            <StatList
              columns={4}
              stats={[
                {
                  label: 'KDA',
                  value: formatKDA(stats.avg_kda.kills, stats.avg_kda.deaths, stats.avg_kda.assists),
                  note: `${stats.avg_kda.kills} / ${stats.avg_kda.deaths} / ${stats.avg_kda.assists}`,
                },
                { label: 'CS / min', value: stats.avg_cs_per_min },
                { label: 'Damage / min', value: stats.avg_damage_per_min },
                {
                  label: 'Share of your games',
                  value: `${stats.pick_rate}%`,
                  note: `${stats.games} of your matches`,
                },
              ]}
            />
          </Box>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
              gap: `${space[7]}px ${space[6]}px`,
            }}
          >
            <Box>
              <SectionHeading as="h3">{champion} beats</SectionHeading>
              <RecordTable
                rows={stats.strong_against ?? []}
                nameHeading="Opponent"
                emptyMessage={`No opponent has a losing record against your ${champion} yet.`}
                showCaption={false}
              />
            </Box>
            <Box>
              <SectionHeading as="h3">{champion} loses to</SectionHeading>
              <RecordTable
                rows={stats.weak_against ?? []}
                nameHeading="Opponent"
                emptyMessage={`No opponent has beaten your ${champion} yet.`}
                showCaption={false}
              />
            </Box>
          </Box>

          <Typography variant="caption" sx={{ display: 'block' }}>
            Adjusted is the lower bound of a 95% interval on the win rate, so a 1–0 record does not
            outrank a 6–4 one. Rows are ordered by it.
          </Typography>
        </Box>
      )}
    </>
  );
};

export default ChampionRecord;
