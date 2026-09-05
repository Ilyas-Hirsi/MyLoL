import { createTheme } from '@mui/material/styles';
import type { Shadows } from '@mui/material/styles';
import { color, font, motion, radius, shadow, size, space, type } from './tokens';

const [displaySize, displayLh] = type.display;
const [titleSize, titleLh] = type.title;
const [bodySize, bodyLh] = type.body;
const [uiSize, uiLh] = type.ui;
const [labelSize, labelLh] = type.label;

/** Tokens as CSS custom properties, for the parts of the UI written in plain CSS. */
const cssVars = {
  '--ink-900': color.ink900,
  '--ink-800': color.ink800,
  '--ink-700': color.ink700,
  '--ink-600': color.ink600,
  '--rule': color.rule,
  '--rule-strong': color.ruleStrong,
  '--text-hi': color.textHi,
  '--text': color.text,
  '--text-lo': color.textLo,
  '--gold': color.gold,
  '--gold-hi': color.goldHi,
  '--gold-dim': color.goldDim,
  '--win': color.win,
  '--loss': color.loss,
  '--font-ui': font.ui,
  '--font-display': font.display,
  '--rail': `${size.rail}px`,
  '--page': `${size.page}px`,
  '--control-h': `${size.control}px`,
  '--row-h': `${size.row}px`,
  '--motion-control': motion.control,
};

const serif = (fontSize: number, lineHeight: number, fontWeight = 600) => ({
  fontFamily: font.display,
  fontWeight,
  fontSize,
  lineHeight,
  letterSpacing: '-0.005em',
});

const theme = createTheme({
  palette: {
    mode: 'dark',
    // Gold is the only accent in the system. `secondary` is deliberately a
    // neutral so no component can quietly reach for a second one.
    primary: { main: color.gold, dark: color.goldDim, light: color.goldHi, contrastText: color.ink900 },
    secondary: { main: color.ruleStrong, contrastText: color.textHi },
    success: { main: color.win },
    error: { main: color.loss },
    warning: { main: color.gold },
    info: { main: color.textLo },
    background: { default: color.ink900, paper: color.ink800 },
    text: { primary: color.textHi, secondary: color.text, disabled: color.textLo },
    divider: color.rule,
  },

  shape: { borderRadius: radius.control },

  // No shadows. Elevation is a background step or a hairline; the dialog is the
  // one exception and sets its own in the MuiDialog override below.
  shadows: Array(25).fill('none') as unknown as Shadows,

  typography: {
    fontFamily: font.ui,
    fontSize: bodySize,
    h1: serif(34, 1.1),
    h2: serif(displaySize, displayLh),
    h3: serif(24, 1.2),
    h4: serif(titleSize, titleLh),
    h5: serif(17, 1.3),
    h6: { fontFamily: font.ui, fontWeight: 600, fontSize: bodySize, lineHeight: 1.35, letterSpacing: '0.01em' },
    subtitle1: { fontSize: bodySize, fontWeight: 500, lineHeight: 1.4 },
    subtitle2: { fontSize: uiSize, fontWeight: 600, lineHeight: 1.4 },
    body1: { fontSize: bodySize, lineHeight: bodyLh },
    body2: { fontSize: uiSize, lineHeight: uiLh },
    caption: { fontSize: labelSize, lineHeight: 1.4, color: color.textLo },
    // The section mark: a letterspaced label sitting above a rule.
    overline: {
      fontSize: labelSize,
      lineHeight: labelLh,
      fontWeight: 600,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    },
    button: { fontSize: uiSize, fontWeight: 500, letterSpacing: '0.01em', textTransform: 'none' },
  },

  components: {
    MuiCssBaseline: {
      styleOverrides: {
        ':root': cssVars,

        body: {
          // Every figure in the app aligns on a column and does not jitter when
          // data refreshes. The most product-specific decision in the system.
          fontVariantNumeric: 'tabular-nums',
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
        },

        // One visible focus treatment, gold, everywhere.
        ':focus-visible': {
          outline: `2px solid ${color.gold}`,
          outlineOffset: 2,
        },

        '::selection': { background: color.goldDim, color: color.textHi },

        '@media (prefers-reduced-motion: reduce)': {
          '*, *::before, *::after': {
            animationDuration: '0.01ms !important',
            animationIterationCount: '1 !important',
            transitionDuration: '0.01ms !important',
            scrollBehavior: 'auto !important',
          },
        },
      },
    },

    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          // MUI's dark mode paints a translucent white gradient over Paper to
          // fake elevation. Off — the system has no gradients.
          backgroundImage: 'none',
          borderRadius: radius.none,
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: radius.none,
          border: `1px solid ${color.rule}`,
        },
      },
    },

    MuiButton: {
      defaultProps: { disableRipple: true },
      styleOverrides: {
        root: {
          borderRadius: radius.control,
          minHeight: size.control,
          paddingInline: space[3],
          transition: `background-color ${motion.control}, border-color ${motion.control}, color ${motion.control}`,
        },
        contained: {
          '&:hover': { backgroundColor: color.goldHi },
        },
        outlined: {
          borderColor: color.ruleStrong,
          color: color.textHi,
          '&:hover': { borderColor: color.gold, backgroundColor: 'transparent' },
        },
        text: {
          color: color.text,
          '&:hover': { color: color.textHi, backgroundColor: color.ink700 },
        },
      },
    },

    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: radius.control,
          backgroundColor: color.ink800,
          transition: `border-color ${motion.control}`,
          '& .MuiOutlinedInput-notchedOutline': { borderColor: color.rule },
          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: color.ruleStrong },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: color.gold, borderWidth: 1 },
        },
        input: { fontSize: uiSize },
      },
    },

    MuiInputLabel: {
      styleOverrides: {
        root: { fontSize: uiSize, color: color.textLo, '&.Mui-focused': { color: color.gold } },
      },
    },

    MuiMenu: {
      styleOverrides: {
        paper: { border: `1px solid ${color.rule}`, borderRadius: radius.control },
      },
    },

    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontSize: uiSize,
          minHeight: size.control,
          '&.Mui-selected': { backgroundColor: color.ink600 },
        },
      },
    },

    // Square, not a pill — a chip here is a data label, not a tag.
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: radius.control, fontSize: labelSize, fontWeight: 600, height: 20 },
        label: { paddingInline: space[2] },
      },
    },

    MuiDivider: {
      styleOverrides: { root: { borderColor: color.rule } },
    },

    MuiTableCell: {
      styleOverrides: {
        root: { borderBottom: `1px solid ${color.rule}`, fontSize: uiSize },
        head: {
          fontSize: labelSize,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: color.textLo,
          borderBottom: `1px solid ${color.ruleStrong}`,
        },
      },
    },

    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: radius.control,
          border: `1px solid ${color.ruleStrong}`,
          boxShadow: shadow.dialog,
          backgroundImage: 'none',
        },
      },
    },

    MuiLink: {
      defaultProps: { underline: 'hover' },
      styleOverrides: {
        root: { color: color.gold, textUnderlineOffset: '0.2em' },
      },
    },

    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: color.ink600,
          border: `1px solid ${color.rule}`,
          borderRadius: radius.control,
          fontSize: labelSize,
          color: color.textHi,
        },
      },
    },
  },
});

export default theme;
