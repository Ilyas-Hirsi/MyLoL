/**
 * Design tokens — the single source of truth for the interface.
 *
 * These values are consumed by `theme/index.ts`, which builds the MUI theme and
 * also emits them as CSS custom properties on :root so plain CSS can reach them.
 * Nothing else in the app should hardcode a colour or a type size.
 */

/**
 * One accent, two semantics, everything else neutral.
 *
 * The ground is a cool near-black and the text is a warm off-white; the mismatch
 * is deliberate and reads as ink on stock rather than grey on grey. Gold is the
 * only accent — selection, focus, current nav. Win/loss are muted because they
 * appear inside dense lists where saturated red and green fight the text.
 *
 * Contrast against ink900 / ink800 / ink700, all WCAG AA:
 *   textHi 15.16 14.13 12.95   text 10.13 9.44 8.65   textLo 5.64 5.26 4.82
 *   gold    7.82  7.28  6.67   win   5.87 5.47 5.01   loss   5.69 5.30 4.86
 */
export const color = {
  ink900: '#0E1116', // page ground
  ink800: '#141922', // raised surface
  ink700: '#1B212C', // row hover / stripe
  ink600: '#222A36', // pressed / selected row
  rule: '#262E3A', // hairlines
  ruleStrong: '#39424F', // section rules
  textHi: '#E8E6E1',
  text: '#B9BEC7',
  textLo: '#858D99', // captions, denominators
  gold: '#C9A227',
  goldHi: '#E0B93A', // hover
  goldDim: '#6E5A18', // borders, inactive marks
  win: '#4E9E7E',
  loss: '#CE7468',
} as const;

/**
 * Spectral is a low-contrast text serif drawn for screens — it carries the
 * record-book voice without being a display face. Archivo is a squarish grotesk
 * with a high x-height that holds at 12–13px. Loaded in index.html.
 */
export const font = {
  ui: "'Archivo', 'Helvetica Neue', Arial, sans-serif",
  display: "'Spectral', Georgia, 'Times New Roman', serif",
} as const;

/** Five sizes, each with one job. `[size, lineHeight]` in px / unitless. */
export const type = {
  display: [30, 1.15],
  title: [20, 1.25],
  figureLg: [30, 1],
  figure: [20, 1],
  body: [14, 1.55],
  ui: [13, 1.4],
  label: [11, 1.2],
} as const;

/** 4px base. */
export const space = {
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 24,
  6: 32,
  7: 48,
  8: 64,
} as const;

/**
 * Data surfaces are square. Controls get 2px. Fully round is reserved for the
 * avatar, because it is a portrait.
 */
export const radius = {
  none: 0,
  control: 2,
  round: 999,
} as const;

export const size = {
  rail: 200, // nav rail width
  page: 1180, // page measure; tables may exceed it and scroll
  prose: '62ch',
  control: 34,
  controlTouch: 40, // below the `sm` breakpoint
  row: 44, // table row, doubling as the touch target
} as const;

/**
 * The only shadow in the system. A dialog genuinely floats above the page;
 * everything else separates with a background step or a hairline.
 */
export const shadow = {
  dialog: '0 12px 32px rgba(0, 0, 0, 0.5)',
} as const;

export const motion = {
  control: '120ms cubic-bezier(0.2, 0, 0.2, 1)',
  dialog: '160ms cubic-bezier(0.2, 0, 0.2, 1)',
} as const;
