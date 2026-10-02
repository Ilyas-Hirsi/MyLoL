import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useDifficultMatchupsFull } from '../hooks/useApi';
import { formatKDA } from '../utils/helpers';
import { color, size, space } from '../theme/tokens';
import PageHeader from '../components/PageHeader';
import SectionHeading from '../components/SectionHeading';
import LoadingBar from '../components/LoadingBar';
import EmptyState from '../components/EmptyState';
import RecordBar from '../components/RecordBar';
import MatchupDetail from '../components/MatchupDetail';
import ChampionRecord from '../components/ChampionRecord';

const ROLES = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT'];
const GAME_MODES = [
  'Ranked Solo/Duo',
  'Ranked Flex',
  'ARAM',
  'Clash',
  'URF',
  'One for All',
  'Nexus Blitz',
  'Ultimate Spellbook',
  'Arena',
];

/** Below this many games a win rate is noise, and the row says so. */
const THIN_SAMPLE = 5;

interface Matchup {
  champion: string;
  games_played: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_kda: { kills: number; deaths: number; assists: number };
  avg_cs_per_min: number;
  avg_damage_per_min: number;
}

type View = 'opponents' | 'champions';

const MatchupsPage: React.FC = () => {
  const [view, setView] = useState<View>('opponents');
  const [champion, setChampion] = useState('');
  const [role, setRole] = useState('');
  const [gameMode, setGameMode] = useState('');
  const [opponent, setOpponent] = useState('');
  const [detailOpen, setDetailOpen] = useState(false);

  const { data, isLoading, isFetching, error } = useDifficultMatchupsFull(role, gameMode);

  const matchups: Matchup[] = data?.difficult_matchups ?? [];
  const analysed: number = data?.total_analyzed ?? 0;

  const openDetail = (champion: string) => {
    setOpponent(champion);
    setDetailOpen(true);
  };

  const filtersApplied = Boolean(role || gameMode);

  return (
    <>
      {isFetching && <LoadingBar label="Loading matchups" />}

      <PageHeader
        title="Matchups"
        description={
          view === 'opponents'
            ? 'Opponents you lose to more than you beat, ranked by how badly.'
            : 'Your record on one champion, and the opponents it wins and loses into.'
        }
      />

      {/* The same question from two sides, so it is one screen with two views
          rather than two screens. A full tab pattern: roles, ids, and the
          arrow-key navigation the pattern requires — half of it would be worse
          than none, because it would promise keyboard behaviour it lacks. */}
      <Box
        role="tablist"
        aria-label="Matchup view"
        onKeyDown={(e) => {
          if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
          e.preventDefault();
          const next: View = view === 'opponents' ? 'champions' : 'opponents';
          setView(next);
          document.getElementById(`tab-${next}`)?.focus();
        }}
        sx={{ display: 'flex', gap: `${space[5]}px`, marginBottom: `${space[5]}px` }}
      >
        {([
          ['opponents', 'By opponent'],
          ['champions', 'By your champion'],
        ] as Array<[View, string]>).map(([key, label]) => (
          <Box
            key={key}
            component="button"
            type="button"
            role="tab"
            id={`tab-${key}`}
            aria-selected={view === key}
            aria-controls={`panel-${key}`}
            tabIndex={view === key ? 0 : -1}
            onClick={() => setView(key)}
            sx={{
              background: 'none',
              border: 0,
              padding: 0,
              paddingBottom: `${space[2]}px`,
              font: 'inherit',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              color: view === key ? color.textHi : color.textLo,
              borderBottom: `2px solid ${view === key ? color.gold : 'transparent'}`,
              transition: 'color var(--motion-control), border-color var(--motion-control)',
              '&:hover': { color: color.textHi },
            }}
          >
            {label}
          </Box>
        ))}
      </Box>

      <Box role="tabpanel" id="panel-champions" aria-labelledby="tab-champions" hidden={view !== 'champions'}>
        {view === 'champions' && <ChampionRecord champion={champion} onChange={setChampion} />}
      </Box>

      <Box role="tabpanel" id="panel-opponents" aria-labelledby="tab-opponents" hidden={view !== 'opponents'}>
      {view === 'opponents' && (
      <>
      {/* A toolbar, not a card. The old page put these two selects in a Card and
          then repeated their values below as "Role Filter: All Roles" tiles. */}
      <Box
        component="section"
        aria-label="Filters"
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: `${space[3]}px`,
          paddingBottom: `${space[5]}px`,
        }}
      >
        <TextField
          select
          label="Role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          size="small"
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All roles</MenuItem>
          {ROLES.map((r) => (
            <MenuItem key={r} value={r}>
              {r}
            </MenuItem>
          ))}
        </TextField>

        <TextField
          select
          label="Game mode"
          value={gameMode}
          onChange={(e) => setGameMode(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All modes</MenuItem>
          {GAME_MODES.map((m) => (
            <MenuItem key={m} value={m}>
              {m}
            </MenuItem>
          ))}
        </TextField>

        {filtersApplied && (
          <Button
            variant="text"
            onClick={() => {
              setRole('');
              setGameMode('');
            }}
          >
            Clear filters
          </Button>
        )}
      </Box>

      <Box component="section">
        <SectionHeading
          trailing={
            isLoading
              ? 'Loading…'
              : `${matchups.length} of ${analysed} opponents analysed`
          }
        >
          Losing matchups
        </SectionHeading>

        {error && (
          <Typography role="alert" variant="body2" sx={{ color: color.loss }}>
            Could not load matchups. Check the backend is running, then reload.
          </Typography>
        )}

        {!error && !isLoading && matchups.length === 0 && (
          <EmptyState
            title="No losing matchups in this filter."
            detail={
              filtersApplied
                ? 'Either you have too few games under these filters, or you are winning every matchup in them.'
                : 'Once enough games are recorded, the opponents beating you will be listed here.'
            }
            action={
              filtersApplied ? (
                <Button
                  variant="outlined"
                  onClick={() => {
                    setRole('');
                    setGameMode('');
                  }}
                >
                  Clear filters
                </Button>
              ) : undefined
            }
          />
        )}

        {matchups.length > 0 && (
          // Wide data scrolls inside its own container; the page never scrolls
          // sideways.
          <Box sx={{ overflowX: 'auto' }}>
            <Table sx={{ minWidth: 720, tableLayout: 'fixed' }}>
              <TableHead>
                <TableRow>
                  <TableCell>Opponent</TableCell>
                  <TableCell align="right" sx={{ width: 76 }}>Record</TableCell>
                  <TableCell sx={{ width: 210 }}>Win rate</TableCell>
                  <TableCell align="right" sx={{ width: 76 }}>KDA</TableCell>
                  <TableCell align="right" sx={{ width: 84 }}>CS/min</TableCell>
                  <TableCell align="right" sx={{ width: 92 }}>Dmg/min</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {matchups.map((m) => {
                  const thin = m.games_played < THIN_SAMPLE;
                  return (
                    <TableRow
                      key={m.champion}
                      onClick={() => openDetail(m.champion)}
                      sx={{
                        cursor: 'pointer',
                        height: size.row,
                        transition: 'background-color var(--motion-control)',
                        '&:hover': { backgroundColor: color.ink700 },
                        '&:focus-within': { backgroundColor: color.ink700 },
                      }}
                    >
                      <TableCell>
                        {/* A real button carries the keyboard affordance and the
                            accessible name; the row click is just a convenience
                            for pointers, and the button's click bubbles to it. */}
                        <Box
                          component="button"
                          type="button"
                          aria-label={`Your record against ${m.champion}`}
                          sx={{
                            background: 'none',
                            border: 0,
                            padding: 0,
                            font: 'inherit',
                            fontWeight: 500,
                            color: color.textHi,
                            cursor: 'pointer',
                          }}
                        >
                          {m.champion}
                        </Box>
                      </TableCell>

                      {/* W–L is the game count: 0–4 is four games. Printing
                          "4g" beside it said the same thing twice. */}
                      <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                        <Box component="span" sx={{ color: color.win }}>{m.wins}</Box>
                        <Box component="span" sx={{ color: color.textLo }}>–</Box>
                        <Box component="span" sx={{ color: color.loss }}>{m.losses}</Box>
                      </TableCell>

                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: `${space[2]}px` }}>
                          <Box component="span" sx={{ color: color.textHi, width: 36, textAlign: 'right' }}>
                            {m.win_rate.toFixed(0)}%
                          </Box>
                          <RecordBar winRate={m.win_rate} />
                          {thin && (
                            <Typography variant="caption" sx={{ color: color.textLo, whiteSpace: 'nowrap' }}>
                              thin sample
                            </Typography>
                          )}
                        </Box>
                      </TableCell>

                      <TableCell align="right">
                        {formatKDA(m.avg_kda.kills, m.avg_kda.deaths, m.avg_kda.assists)}
                      </TableCell>
                      <TableCell align="right">{m.avg_cs_per_min.toFixed(1)}</TableCell>
                      <TableCell align="right">{m.avg_damage_per_min.toFixed(0)}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Box>
        )}
      </Box>

      </>
      )}
      </Box>

      {opponent && (
        <MatchupDetail
          opponent={opponent}
          open={detailOpen}
          onClose={() => setDetailOpen(false)}
          role={role || undefined}
          gameMode={gameMode || undefined}
        />
      )}
    </>
  );
};

export default MatchupsPage;
