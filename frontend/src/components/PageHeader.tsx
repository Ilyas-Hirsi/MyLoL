import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { color, size, space } from '../theme/tokens';

interface PageHeaderProps {
  title: string;
  /** One line saying what this screen answers. Omit it rather than pad it. */
  description?: string;
  /** Right-aligned controls that act on the whole page. */
  actions?: React.ReactNode;
}

/**
 * The single h1 on every screen.
 *
 * The old shell printed the page name twice — once in the app bar and again in
 * the page body — so the app bar is gone on desktop and the page owns its title.
 */
const PageHeader: React.FC<PageHeaderProps> = ({ title, description, actions }) => (
  <Box
    component="header"
    sx={{
      display: 'flex',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      gap: `${space[4]}px`,
      flexWrap: 'wrap',
      paddingBottom: `${space[4]}px`,
      marginBottom: `${space[6]}px`,
      borderBottom: `1px solid ${color.ruleStrong}`,
    }}
  >
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="h2" component="h1" sx={{ color: color.textHi }}>
        {title}
      </Typography>
      {description && (
        <Typography
          variant="body2"
          sx={{ color: color.textLo, marginTop: `${space[2]}px`, maxWidth: size.prose }}
        >
          {description}
        </Typography>
      )}
    </Box>
    {actions && <Box sx={{ display: 'flex', gap: `${space[2]}px`, flexShrink: 0 }}>{actions}</Box>}
  </Box>
);

export default PageHeader;
