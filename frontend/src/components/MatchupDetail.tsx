import React from 'react';
import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import { useMatchupDetails } from '../hooks/useApi';
import { formatKDA } from '../utils/helpers';
import { color, font, space } from '../theme/tokens';
import LoadingBar from './LoadingBar';
import SectionHeading from './SectionHeading';
import StatList from './StatList';
import RecordBar from './RecordBar';
import RecordTable from './RecordTable';

interface MatchupDetailProps {
  opponent: string;
  open: boolean;
  onClose: () => void;
  role?: string;
  gameMode?: string;
}

const Record: React.FC<{ wins: number; losses: number }> = ({ wins, losses }) => (
  <Box component="span">
    <Box component="span" sx={{ color: color.win }}>
      {wins}
    </Box>
    <Box component="span" sx={{ color: color.textLo }}>
      –
    </Box>
    <Box component="span" sx={{ color: color.loss }}>
      {losses}
    </Box>
  </Box>
);

/** "Ranked Solo/Duo 3 · ARAM 1" — counts read fine as text and cost no chips. */
const Distribution: React.FC<{ label: string; data: Record<string, number> }> = ({ label, data }) => {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  return (
    <Box>
      <Typography variant="overline" sx={{ color: color.textLo, display: 'block' }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ color: color.text, marginTop: `${space[1]}px` }}>
        {entries.length === 0
          ? '—'
          : entries.map(([k, v], i) => (
              <React.Fragment key={k}>
                {i > 0 && <Box component="span" sx={{ color: color.textLo }}> · </Box>}
                {k} <Box component="span" sx={{ color: color.textLo }}>{v}</Box>
              </React.Fragment>
            ))}
      </Typography>
    </Box>
  );
};

const MatchupDetail: React.FC<MatchupDetailProps> = ({ opponent, open, onClose, role, gameMode }) => {
  const { data, isLoading, error } = useMatchupDetails(opponent, role, gameMode);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      aria-labelledby="matchup-detail-title"
    >
      <DialogTitle
        id="matchup-detail-title"
        sx={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          gap: `${space[3]}px`,
          fontFamily: font.display,
          fontWeight: 600,
          fontSize: 20,
          paddingBottom: `${space[3]}px`,
          borderBottom: `1px solid ${color.ruleStrong}`,
        }}
      >
        <Box component="span">
          <Box component="span" sx={{ color: color.textLo }}>vs </Box>
          {opponent}
        </Box>
        <IconButton
          onClick={onClose}
          aria-label="Close"
          size="small"
          sx={{ color: color.textLo, alignSelf: 'center' }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ paddingTop: `${space[5]}px !important` }}>
        {isLoading && <LoadingBar label={`Loading your record against ${opponent}`} />}

        {error && (
          <Typography role="alert" variant="body2" sx={{ color: color.loss }}>
            Could not load this matchup. Close and try again.
          </Typography>
        )}

        {data && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: `${space[7]}px` }}>
            <Box>
              <Typography sx={{ fontSize: 14, color: color.text }}>
                <Record wins={data.wins} losses={data.losses} /> in {data.games}{' '}
                {data.games === 1 ? 'game' : 'games'} — {data.win_rate}% win rate
              </Typography>
              <Box sx={{ marginTop: `${space[3]}px` }}>
                <RecordBar winRate={data.win_rate} width={200} />
              </Box>
            </Box>

            <Box>
              <SectionHeading as="h3">Your averages in this matchup</SectionHeading>
              <StatList
                columns={5}
                stats={[
                  {
                    label: 'KDA',
                    value: formatKDA(data.avg_kda.kills, data.avg_kda.deaths, data.avg_kda.assists),
                    note: `${data.avg_kda.kills} / ${data.avg_kda.deaths} / ${data.avg_kda.assists}`,
                  },
                  { label: 'CS / min', value: data.avg_cs_per_min },
                  { label: 'Gold / min', value: data.avg_gold_per_min },
                  { label: 'Damage / min', value: data.avg_damage_per_min },
                  { label: 'Game length', value: `${data.avg_game_duration_min}m` },
                ]}
              />
            </Box>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                gap: `${space[5]}px`,
              }}
            >
              <Distribution label="By role" data={data.role_distribution} />
              <Distribution label="By mode" data={data.game_mode_distribution} />
            </Box>

            <Box>
              {/* Deliberately not "your best champions": the list is every
                  champion taken into this matchup, and calling a 0–4 record
                  "best" is how the old UI ended up recommending a champion
                  that had never won. */}
              <SectionHeading as="h3" trailing={`${data.best_champions.length} played`}>
                Champions you have taken into {opponent}
              </SectionHeading>

              <RecordTable
                rows={data.best_champions}
                nameHeading="Champion"
                emptyMessage={`No other champion has faced ${opponent} in this filter.`}
              />
            </Box>

            <Box>
              <SectionHeading as="h3">Recent games</SectionHeading>
              <Box sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ minWidth: 640 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Champion</TableCell>
                      <TableCell>Result</TableCell>
                      <TableCell align="right">K / D / A</TableCell>
                      <TableCell align="right">CS/min</TableCell>
                      <TableCell align="right">Dmg/min</TableCell>
                      <TableCell align="right">Length</TableCell>
                      <TableCell>Role</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.recent_matches.map((m) => (
                      <TableRow key={m.match_id}>
                        <TableCell sx={{ color: color.textLo, whiteSpace: 'nowrap' }}>
                          {m.date ? new Date(m.date).toLocaleDateString() : '—'}
                        </TableCell>
                        <TableCell sx={{ color: color.textHi }}>{m.champion}</TableCell>
                        <TableCell sx={{ color: m.win ? color.win : color.loss, fontWeight: 500 }}>
                          {m.win ? 'Win' : 'Loss'}
                        </TableCell>
                        <TableCell align="right">
                          {m.kda.kills} / {m.kda.deaths} / {m.kda.assists}
                        </TableCell>
                        <TableCell align="right">{m.cs_per_min}</TableCell>
                        <TableCell align="right">{m.damage_to_champs_per_min}</TableCell>
                        <TableCell align="right">{m.game_duration_min}m</TableCell>
                        <TableCell sx={{ color: color.textLo }}>{m.role || '—'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            </Box>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default MatchupDetail;
