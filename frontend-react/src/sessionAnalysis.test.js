import { afterEach, expect, it, vi } from "vitest";
import { readAnalysisSession, writeAnalysisSession, clearAnalysisSession } from "./sessionAnalysis";
import { effacerJeton } from "./auth/api";
afterEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); });
const snapshot = { result: { score: 42, components: {}, gaps: [], recommendations: {} }, savedId: "saved", resultDemo: true };
it("restores the last report only for its owner and clears it on logout", () => {
  writeAnalysisSession(1, snapshot);
  expect(readAnalysisSession(1)).toEqual({ ...snapshot, owner: 1 });
  expect(readAnalysisSession(2)).toBeNull();
  expect(readAnalysisSession(null)).toBeNull();
  effacerJeton();
  expect(readAnalysisSession(1)).toBeNull();
});
it("handles malformed or unavailable browser storage without breaking analysis", () => {
  sessionStorage.setItem("talentmatch.analysis", "broken");
  expect(readAnalysisSession(1)).toBeNull();
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Quota"); });
  expect(writeAnalysisSession(1, snapshot)).toBe(false);
  clearAnalysisSession();
});
