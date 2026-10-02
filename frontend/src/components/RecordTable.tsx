import React from 'react';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { color, size, space } from '../theme/tokens';
import RecordBar from './RecordBar';

export interface RecordRow {
  champion: string;
  games: number;
  wins: number;
  losses: number;
  win_rate: number;
  /** Wilson lower bound the backend computes. Named `confidence` in the API. */
  confidence?: number;
}

/**
 * Head-to-head records, shared by the matchup dialog and the champion view so
 * both read the same way.
 *
 * "Adjusted" is the Wilson lower bound. The API calls the field `confidence`,
 * but it is a win-rate floor, not a confidence percentage — showing the raw
 * figure alone is how a single 1–0 game used to be presented as a 100% matchup.
 */
const RecordTable: React.FC<{
  rows: RecordRow[];
  nameHeading: string;
  emptyMessage: string;
  showCaption?: boolean;
}> = ({ rows, nameHeading, emptyMessage, showCaption = true }) => {
  if (rows.length === 0) {
    return (
      <Typography variant="body2" sx={{ color: color.textLo }}>
        {emptyMessage}
      </Typography>
    );
  }

  return (
    <>
      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ minWidth: 420, tableLayout: 'fixed' }}>
          <TableHead>
            <TableRow>
              <TableCell>{nameHeading}</TableCell>
              <TableCell align="right" sx={{ width: 68 }}>
                Record
              </TableCell>
              <TableCell sx={{ width: 136 }}>Win rate</TableCell>
              <TableCell align="right" sx={{ width: 84 }}>
                Adjusted
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.champion}>
                <TableCell sx={{ color: color.textHi }}>{r.champion}</TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Box component="span" sx={{ color: color.win }}>
                    {r.wins}
                  </Box>
                  <Box component="span" sx={{ color: color.textLo }}>
                    –
                  </Box>
                  <Box component="span" sx={{ color: color.loss }}>
                    {r.losses}
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: `${space[2]}px` }}>
                    <Box component="span" sx={{ width: 38, textAlign: 'right', color: color.textHi }}>
                      {r.win_rate.toFixed(0)}%
                    </Box>
                    <RecordBar winRate={r.win_rate} width={48} />
                  </Box>
                </TableCell>
                <TableCell align="right" sx={{ color: color.text }}>
                  {typeof r.confidence === 'number' ? `${r.confidence.toFixed(0)}%` : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      {showCaption && (
        <Typography
          variant="caption"
          sx={{ display: 'block', marginTop: `${space[3]}px`, maxWidth: size.prose }}
        >
          Adjusted is the lower bound of a 95% interval on the win rate, so a 1–0 record does not
          outrank a 6–4 one. Rows are ordered by it.
        </Typography>
      )}
    </>
  );
};

export default RecordTable;
