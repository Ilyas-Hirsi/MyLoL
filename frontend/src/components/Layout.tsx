import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import MenuIcon from '@mui/icons-material/Menu';
import { useAuth } from '../contexts/AuthContext';
import { useRefreshUserData } from '../hooks/useApi';
import { formatRelativeTime } from '../utils/helpers';
import { color, font, radius, size, space } from '../theme/tokens';

const NAV = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Matchups', to: '/matchups' },
  { label: 'Profile', to: '/profile' },
];

const MOBILE_BAR_H = 48;

/** The favicon glyph: a rank mark, three bars of descending width. */
const Mark: React.FC = () => (
  <Box
    component="svg"
    viewBox="0 0 32 32"
    aria-hidden="true"
    sx={{ width: 18, height: 18, flexShrink: 0, display: 'block' }}
  >
    <rect x="6" y="7" width="20" height="4" fill={color.gold} />
    <rect x="6" y="14" width="13" height="4" fill={color.gold} />
    <rect x="6" y="21" width="8" height="4" fill={color.gold} />
  </Box>
);

/**
 * The rail.
 *
 * Text-only navigation: three destinations with unambiguous names do not need
 * icons, and dropping them removes a row of decoration. The current item is
 * marked with a gold rule on the leading edge; `NavLink` supplies
 * `aria-current="page"` on its own.
 *
 * The rail shares the page ground rather than sitting on its own surface, so
 * the only thing dividing them is a hairline.
 */
const RailContent: React.FC<{ onNavigate?: () => void }> = ({ onNavigate }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const refresh = useRefreshUserData();

  const handleRefresh = () => {
    refresh.mutate(undefined, { onSettled: onNavigate });
  };

  const handleSignOut = () => {
    logout();
    navigate('/login');
    onNavigate?.();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', paddingBlock: `${space[5]}px` }}>
      {/* A masthead rather than a lockup: "League Analytics" will not fit on one
          line at this rail width, so the mark sits above it instead of fighting
          a two-line wrap beside it. */}
      <Box sx={{ paddingInline: `${space[5]}px`, marginBottom: `${space[6]}px` }}>
        <Mark />
        <Typography
          sx={{
            fontFamily: font.display,
            fontWeight: 600,
            fontSize: 19,
            lineHeight: 1.15,
            color: color.textHi,
            marginTop: `${space[2]}px`,
          }}
        >
          League
          <br />
          Analytics
        </Typography>
      </Box>

      <Box component="nav" aria-label="Sections">
        <Box component="ul" sx={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {NAV.map((item) => (
            <Box component="li" key={item.to}>
              <Box
                component={NavLink}
                to={item.to}
                onClick={onNavigate}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  minHeight: size.row,
                  paddingInline: `${space[5]}px`,
                  // The leading rule is always present so the label never shifts
                  // between states; only its colour changes.
                  borderLeft: `2px solid transparent`,
                  color: color.textLo,
                  fontSize: 13,
                  fontWeight: 500,
                  textDecoration: 'none',
                  transition: 'color var(--motion-control), border-color var(--motion-control)',
                  '&:hover': { color: color.textHi },
                  '&.active': { color: color.textHi, borderLeftColor: color.gold },
                }}
              >
                {item.label}
              </Box>
            </Box>
          ))}
        </Box>
      </Box>

      <Box sx={{ flex: 1 }} />

      <Box
        sx={{
          paddingInline: `${space[5]}px`,
          paddingTop: `${space[4]}px`,
          marginTop: `${space[4]}px`,
          borderTop: `1px solid ${color.rule}`,
        }}
      >
        <Typography sx={{ fontSize: 13, fontWeight: 500, color: color.textHi }}>
          {user?.riot_id}
          <Box component="span" sx={{ color: color.textLo }}>
            #{user?.tag}
          </Box>
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', marginTop: `${space[1]}px` }}>
          {user?.last_updated ? `Synced ${formatRelativeTime(user.last_updated)}` : 'Not yet synced'}
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginTop: `${space[3]}px` }}>
          <Button
            variant="text"
            onClick={handleRefresh}
            disabled={refresh.isPending}
            sx={{ paddingInline: 0, minWidth: 0, justifyContent: 'flex-start' }}
          >
            {refresh.isPending ? 'Fetching matches…' : 'Fetch new matches'}
          </Button>
          <Button
            variant="text"
            onClick={handleSignOut}
            sx={{ paddingInline: 0, minWidth: 0, justifyContent: 'flex-start' }}
          >
            Sign out
          </Button>
        </Box>

        {refresh.isError && (
          <Typography variant="caption" role="alert" sx={{ display: 'block', color: color.loss }}>
            Could not reach Riot. Try again in a moment.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

const Layout: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const closeDrawer = () => setDrawerOpen(false);

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Box
        component="a"
        href="#main"
        sx={{
          position: 'absolute',
          left: `${space[3]}px`,
          top: -100,
          zIndex: (t) => t.zIndex.drawer + 3,
          padding: `${space[2]}px ${space[3]}px`,
          backgroundColor: color.gold,
          color: color.ink900,
          borderRadius: `${radius.control}px`,
          fontSize: 13,
          fontWeight: 600,
          textDecoration: 'none',
          '&:focus': { top: `${space[3]}px` },
        }}
      >
        Skip to content
      </Box>

      {/* Mobile only. On wider screens the rail is always visible and the page
          owns its own title, so there is no persistent bar taking vertical space. */}
      <Box
        component="header"
        sx={{
          display: { xs: 'flex', md: 'none' },
          alignItems: 'center',
          gap: `${space[2]}px`,
          position: 'sticky',
          top: 0,
          zIndex: (t) => t.zIndex.appBar,
          height: MOBILE_BAR_H,
          paddingInline: `${space[2]}px`,
          backgroundColor: color.ink900,
          borderBottom: `1px solid ${color.rule}`,
        }}
      >
        <IconButton
          onClick={() => setDrawerOpen(true)}
          aria-label="Open navigation"
          sx={{ color: color.text, width: size.controlTouch, height: size.controlTouch }}
        >
          <MenuIcon fontSize="small" />
        </IconButton>
        <Mark />
        <Typography sx={{ fontFamily: font.display, fontWeight: 600, fontSize: 15, color: color.textHi }}>
          League Analytics
        </Typography>
      </Box>

      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={closeDrawer}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: size.rail + 40,
            backgroundColor: color.ink900,
            borderRight: `1px solid ${color.rule}`,
          },
        }}
      >
        <RailContent onNavigate={closeDrawer} />
      </Drawer>

      <Box
        sx={{
          display: { xs: 'none', md: 'block' },
          position: 'fixed',
          insetBlock: 0,
          left: 0,
          width: size.rail,
          borderRight: `1px solid ${color.rule}`,
          overflowY: 'auto',
        }}
      >
        <RailContent />
      </Box>

      <Box
        component="main"
        id="main"
        tabIndex={-1}
        sx={{
          marginLeft: { xs: 0, md: `${size.rail}px` },
          paddingInline: { xs: `${space[4]}px`, md: `${space[6]}px` },
          paddingBlock: { xs: `${space[5]}px`, md: `${space[6]}px` },
          outline: 'none',
        }}
      >
        <Box sx={{ maxWidth: size.page, marginInline: 'auto' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
