// Per-tab, per-account report cache. Permanent history still requires explicit saving.
const KEY = "talentmatch.analysis";
export function readAnalysisSession(owner) {
  try {
    const value = JSON.parse(sessionStorage.getItem(KEY));
    if (owner == null || value?.owner !== owner || !value.result?.components ||
        !Array.isArray(value.result?.gaps) || !value.result?.recommendations ||
        !Number.isFinite(value.result?.score)) return null;
    return value;
  } catch { return null; }
}
export function writeAnalysisSession(owner, value) {
  try {
    if (owner != null && value.result)
      sessionStorage.setItem(KEY, JSON.stringify({ ...value, owner }));
    return true;
  } catch { return false; }
}
export function clearAnalysisSession() {
  try { sessionStorage.removeItem(KEY); } catch { /* Storage may be disabled. */ }
}
