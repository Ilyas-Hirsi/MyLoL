import React from 'react';
import Box from '@mui/material/Box';
import { color } from '../theme/tokens';

/**
 * The product mark: three bars of descending width, a rank.
 * Shared by the nav rail and the account-entry screen, and mirrored by
 * public/favicon.svg.
 */
const Mark: React.FC<{ size?: number }> = ({ size = 18 }) => (
  <Box
    component="svg"
    viewBox="0 0 32 32"
    aria-hidden="true"
    sx={{ width: size, height: size, flexShrink: 0, display: 'block' }}
  >
    <rect x="6" y="7" width="20" height="4" fill={color.gold} />
    <rect x="6" y="14" width="13" height="4" fill={color.gold} />
    <rect x="6" y="21" width="8" height="4" fill={color.gold} />
  </Box>
);

export default Mark;
