import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { color, size, space } from '../theme/tokens';

/**
 * Says what is absent and what would change it. No illustration — an empty
 * table is a fact to explain, not a hole to decorate.
 */
const EmptyState: React.FC<{ title: string; detail?: string; action?: React.ReactNode }> = ({
  title,
  detail,
  action,
}) => (
  <Box sx={{ paddingBlock: `${space[6]}px`, maxWidth: size.prose }}>
    <Typography sx={{ fontSize: 14, fontWeight: 500, color: color.textHi }}>{title}</Typography>
    {detail && (
      <Typography variant="body2" sx={{ color: color.textLo, marginTop: `${space[2]}px` }}>
        {detail}
      </Typography>
    )}
    {action && <Box sx={{ marginTop: `${space[4]}px` }}>{action}</Box>}
  </Box>
);

export default EmptyState;
