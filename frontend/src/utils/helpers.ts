// Format KDA ratio
export const formatKDA = (kills: number, deaths: number, assists: number): string => {
  const kda = deaths === 0 ? kills + assists : (kills + assists) / deaths;
  return kda.toFixed(2);
};

// Format duration given minutes (possibly fractional) into HH:MM:SS
export const formatHMSFromMinutes = (minutes: number): string => {
  const totalSeconds = Math.max(0, Math.round(minutes * 60));
  const hours = Math.floor(totalSeconds / 3600);
  const mins = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  const hh = hours.toString();
  const mm = mins.toString().padStart(2, '0');
  const ss = secs.toString().padStart(2, '0');
  return hours > 0 ? `${hh}:${mm}:${ss}` : `${mm}:${ss}`;
};

// Format an ISO timestamp as a short relative age, e.g. "3h ago".
// Used for the last-sync marker, which is null until the first refresh runs.
export const formatRelativeTime = (iso: string): string => {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return 'unknown';

  const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (seconds < 60) return 'just now';

  const units: Array<[number, string]> = [
    [60, 'm'],
    [3600, 'h'],
    [86400, 'd'],
  ];
  for (let i = units.length - 1; i >= 0; i -= 1) {
    const [span, suffix] = units[i];
    if (seconds >= span) return `${Math.floor(seconds / span)}${suffix} ago`;
  }
  return 'just now';
};
