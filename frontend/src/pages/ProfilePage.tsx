import React, { useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { useUserProfile, useMatchHistory } from '../hooks/useApi';
import { Match } from '../types';
import { formatKDA, formatHMSFromMinutes } from '../utils/helpers';
import { color, space } from '../theme/tokens';
import PageHeader from '../components/PageHeader';
import SectionHeading from '../components/SectionHeading';
import StatList from '../components/StatList';
import LoadingBar from '../components/LoadingBar';
import EmptyState from '../components/EmptyState';
import RecordBar from '../components/RecordBar';

const PAGE = 15;

const ProfilePage: React.FC = () => {
  const { data: user, isLoading: userLoading, error: userError } = useUserProfile();
  const { data: matches, isLoading: matchesLoading } = useMatchHistory();
  const [shown, setShown] = useState(PAGE);

  const { totals, byChampion, recent } = useMemo(() => {
    const all: Match[] = matches ?? [];
    const wins = all.filter((m) => m.win).length;

    const k = all.reduce((s, m) => s + m.kda.kills, 0);
    const d = all.reduce((s, m) => s + m.kda.deaths, 0);
    const a = all.reduce((s, m) => s + m.kda.assists, 0);

    const perChampion = new Map<string, { games: number; wins: number }>();
    all.forEach((m) => {
      const e = perChampion.get(m.champion) ?? { games: 0, wins: 0 };
      e.games += 1;
      if (m.win) e.wins += 1;
      perChampion.set(m.champion, e);
    });

    return {
      totals: {
        games: all.length,
        wins,
        losses: all.length - wins,
        winRate: all.length ? (wins / all.length) * 100 : 0,
        kda: all.length ? formatKDA(k, d, a) : '—',
      },
      byChampion: [...perChampion.entries()]
        .map(([champion, e]) => ({ champion, ...e, winRate: (e.wins / e.games) * 100 }))
        .sort((x, y) => y.games - x.games)
        .slice(0, 8),
      recent: [...all].sort((x, y) => {
        const tx = x.game_creation ? Date.parse(x.game_creation) : 0;
        const ty = y.game_creation ? Date.parse(y.game_creation) : 0;
        return ty - tx;
      }),
    };
  }, [matches]);

  if (userError) {
    return (
      <>
        <PageHeader title="Profile" />
        <Typography role="alert" variant="body2" sx={{ color: color.loss }}>
          Could not load your profile. Check the backend is running, then reload.
        </Typography>
      </>
    );
  }

  return (
    <>
      {(userLoading || matchesLoading) && <LoadingBar label="Loading your profile" />}

      <PageHeader title="Profile" description="Your account and everything recorded against it." />

      {/* Identity as a line of text, not an avatar card. The circle is the one
          round thing in the system and it was doing nothing but holding an
          initial. */}
      <Box component="section" sx={{ marginBottom: `${space[8]}px` }}>
        <Typography sx={{ fontSize: 22, color: color.textHi }}>
          {user?.riot_id}
          <Box component="span" sx={{ color: color.textLo }}>#{user?.tag}</Box>
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', marginTop: `${space[2]}px` }}>
          Recorded here since{' '}
          {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
          {user?.last_updated ? '' : ' · not yet synced'}
        </Typography>
      </Box>

      <Box component="section" sx={{ marginBottom: `${space[8]}px` }}>
        <SectionHeading>Lifetime totals</SectionHeading>
        <StatList
          columns={4}
          stats={[
            { label: 'Games', value: totals.games },
            {
              label: 'Record',
              value: (
                <>
                  <Box component="span" sx={{ color: color.win }}>{totals.wins}</Box>
                  <Box component="span" sx={{ color: color.textLo }}>–</Box>
                  <Box component="span" sx={{ color: color.loss }}>{totals.losses}</Box>
                </>
              ),
            },
            { label: 'Win rate', value: `${totals.winRate.toFixed(1)}%` },
            { label: 'Average KDA', value: totals.kda },
          ]}
        />
      </Box>

      <Box component="section" sx={{ marginBottom: `${space[8]}px` }}>
        <SectionHeading trailing={byChampion.length === 8 ? 'top 8 by games' : undefined}>
          Champions you play
        </SectionHeading>
        {byChampion.length === 0 ? (
          <EmptyState title="No champions recorded yet." />
        ) : (
          <Box component="ul" sx={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {byChampion.map((c) => (
              <Box
                component="li"
                key={c.champion}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: `${space[4]}px`,
                  paddingBlock: `${space[3]}px`,
                  borderBottom: `1px solid ${color.rule}`,
                }}
              >
                <Typography sx={{ fontSize: 14, color: color.textHi, flex: 1, minWidth: 0 }}>
                  {c.champion}
                </Typography>
                <Typography variant="caption" sx={{ width: 64, textAlign: 'right' }}>
                  {c.games} games
                </Typography>
                <Typography sx={{ fontSize: 13, whiteSpace: 'nowrap', width: 52, textAlign: 'right' }}>
                  <Box component="span" sx={{ color: color.win }}>{c.wins}</Box>
                  <Box component="span" sx={{ color: color.textLo }}>–</Box>
                  <Box component="span" sx={{ color: color.loss }}>{c.games - c.wins}</Box>
                </Typography>
                <RecordBar winRate={c.winRate} />
                <Typography sx={{ fontSize: 13, color: color.textHi, width: 40, textAlign: 'right' }}>
                  {c.winRate.toFixed(0)}%
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </Box>

      <Box component="section">
        <SectionHeading trailing={`${Math.min(shown, recent.length)} of ${recent.length}`}>
          Match history
        </SectionHeading>

        {recent.length === 0 ? (
          <EmptyState
            title="No matches recorded yet."
            detail="Fetch your match history from the rail on the left."
          />
        ) : (
          <>
            {/* The old page showed ten identical mini-cards carrying champion,
                result and KDA — and dropped the date, the opponent and the role,
                all of which the API already returns. */}
            <Box sx={{ overflowX: 'auto' }}>
              <Table sx={{ minWidth: 760, tableLayout: 'fixed' }}>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ width: 96 }}>Date</TableCell>
                    <TableCell>Champion</TableCell>
                    <TableCell>Opponent</TableCell>
                    <TableCell sx={{ width: 64 }}>Result</TableCell>
                    <TableCell align="right" sx={{ width: 92 }}>K / D / A</TableCell>
                    <TableCell align="right" sx={{ width: 76 }}>CS/min</TableCell>
                    <TableCell align="right" sx={{ width: 72 }}>Length</TableCell>
                    <TableCell sx={{ width: 84 }}>Role</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recent.slice(0, shown).map((m) => (
                    <TableRow key={m.match_id}>
                      <TableCell sx={{ color: color.textLo, whiteSpace: 'nowrap' }}>
                        {m.game_creation ? new Date(m.game_creation).toLocaleDateString() : '—'}
                      </TableCell>
                      <TableCell sx={{ color: color.textHi }}>{m.champion}</TableCell>
                      <TableCell sx={{ color: color.text }}>{m.opponent_champion || '—'}</TableCell>
                      <TableCell sx={{ color: m.win ? color.win : color.loss, fontWeight: 500 }}>
                        {m.win ? 'Win' : 'Loss'}
                      </TableCell>
                      <TableCell align="right">
                        {m.kda.kills} / {m.kda.deaths} / {m.kda.assists}
                      </TableCell>
                      <TableCell align="right">{m.cs_per_min.toFixed(1)}</TableCell>
                      <TableCell align="right">{formatHMSFromMinutes(m.game_duration)}</TableCell>
                      <TableCell sx={{ color: color.textLo }}>{m.team_position || '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            {shown < recent.length && (
              <Button
                variant="outlined"
                onClick={() => setShown((n) => n + PAGE)}
                sx={{ marginTop: `${space[5]}px` }}
              >
                Show {Math.min(PAGE, recent.length - shown)} more
              </Button>
            )}
          </>
        )}
      </Box>
    </>
  );
};

export default ProfilePage;
