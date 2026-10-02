import React from 'react';
import Box from '@mui/material/Box';
import { color } from '../theme/tokens';

/**
 * Win rate as a proportional rule.
 *
 * The old table printed a red pill on every row of a list that was, by
 * definition, entirely losing matchups — so the colour separated nothing. A bar
 * encodes the magnitude, which is the part that actually differs between rows.
 */
const RecordBar: React.FC<{ winRate: number; width?: number }> = ({ winRate, width = 56 }) => {
  const pct = Math.max(0, Math.min(100, winRate));
  return (
    <Box
      aria-hidden="true"
      sx={{
        width,
        height: 4,
        flexShrink: 0,
        backgroundColor: color.ink600,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          width: `${pct}%`,
          height: '100%',
          backgroundColor: pct >= 50 ? color.win : color.loss,
        }}
      />
    </Box>
  );
};

export default RecordBar;
