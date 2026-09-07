import React from 'react';
import LinearProgress from '@mui/material/LinearProgress';
import { color } from '../theme/tokens';

/**
 * A 2px rule across the top of the viewport while something is in flight.
 *
 * This replaces the centred spinners the app used to show. A spinner in the
 * middle of the page blanks the content it replaces; a bar at the edge leaves
 * whatever is already on screen readable while the next data arrives.
 */
const LoadingBar: React.FC<{ label?: string }> = ({ label = 'Loading' }) => (
  <LinearProgress
    aria-label={label}
    sx={{
      position: 'fixed',
      insetInline: 0,
      top: 0,
      zIndex: (t) => t.zIndex.drawer + 2,
      height: 2,
      backgroundColor: 'transparent',
      '& .MuiLinearProgress-bar': { backgroundColor: color.gold },
      // Under reduced motion the bar holds still and reads as a state marker
      // rather than an animation.
      '@media (prefers-reduced-motion: reduce)': {
        '& .MuiLinearProgress-bar': {
          backgroundColor: color.goldDim,
          transform: 'none !important',
          animation: 'none !important',
        },
      },
    }}
  />
);

export default LoadingBar;
