import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { color, font, space } from '../theme/tokens';

export interface Stat {
  label: string;
  value: React.ReactNode;
  /** Smaller text under the value — a denominator, a unit, a caveat. */
  note?: string;
}

/**
 * Figures as a definition list.
 *
 * Each of these used to be a Paper inside a CardContent inside a Card. They are
 * four numbers; they need a label, a value and some space, not three boxes.
 */
const StatList: React.FC<{ stats: Stat[]; columns?: number }> = ({ stats, columns = 4 }) => (
  <Box
    component="dl"
    sx={{
      display: 'grid',
      gridTemplateColumns: {
        xs: 'repeat(2, minmax(0, 1fr))',
        sm: `repeat(${Math.min(columns, 3)}, minmax(0, 1fr))`,
        md: `repeat(${columns}, minmax(0, 1fr))`,
      },
      gap: `${space[5]}px ${space[4]}px`,
      margin: 0,
    }}
  >
    {stats.map((s) => (
      <Box key={s.label} sx={{ minWidth: 0 }}>
        <Box component="dt">
          <Typography variant="overline" sx={{ color: color.textLo }}>
            {s.label}
          </Typography>
        </Box>
        <Box component="dd" sx={{ margin: 0, marginTop: `${space[1]}px` }}>
          <Typography
            sx={{
              fontFamily: font.ui,
              fontSize: 20,
              fontWeight: 500,
              lineHeight: 1.1,
              color: color.textHi,
            }}
          >
            {s.value}
          </Typography>
          {s.note && (
            <Typography variant="caption" sx={{ display: 'block', marginTop: `${space[1]}px` }}>
              {s.note}
            </Typography>
          )}
        </Box>
      </Box>
    ))}
  </Box>
);

export default StatList;
