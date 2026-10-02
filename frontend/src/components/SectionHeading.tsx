import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { color, space } from '../theme/tokens';

interface SectionHeadingProps {
  children: React.ReactNode;
  /** Right-hand slot for a count, a filter summary, or a control. */
  trailing?: React.ReactNode;
  as?: 'h2' | 'h3';
}

/**
 * A letterspaced label sitting on a rule.
 *
 * This is what replaced card titles. A section does not need a box around it to
 * be a section — a mark and a line are enough, and they cost no nesting.
 */
const SectionHeading: React.FC<SectionHeadingProps> = ({ children, trailing, as = 'h2' }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: `${space[4]}px`,
      paddingBottom: `${space[2]}px`,
      borderBottom: `1px solid ${color.rule}`,
      marginBottom: `${space[4]}px`,
    }}
  >
    <Typography component={as} variant="overline" sx={{ color: color.textLo }}>
      {children}
    </Typography>
    {trailing && (
      <Typography variant="caption" sx={{ color: color.textLo, flexShrink: 0 }}>
        {trailing}
      </Typography>
    )}
  </Box>
);

export default SectionHeading;
