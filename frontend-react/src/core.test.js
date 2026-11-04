import { describe, expect, it, vi } from "vitest";
import { validateInputs, analyzeDocuments } from "./api";
import { csvReport, escapeHTML, htmlReport } from "./exports";
import { defaultWeights, demoCV, demoJob } from "./demo";

const doc = (text) => ({ mode: "text", text, file: null });
describe("Input validation and API contract", () => {
  it("accepts demo and rejects incomplete or incorrectly weighted input", () => {
    expect(
      validateInputs(doc(demoCV), doc(demoJob), defaultWeights),
    ).toBeNull();
    expect(validateInputs(doc("tiny"), doc(demoJob), defaultWeights)).toMatch(
      /30/,
    );
    expect(
      validateInputs(doc(demoCV), doc(demoJob), {
        ...defaultWeights,
        hard_skills: 60,
      }),
    ).toMatch(/100/);
    expect(
      validateInputs(
        { mode: "file", file: new File(["test"], "test.exe") },
        doc(demoJob),
        defaultWeights,
      ),
    ).toMatch(/PDF/);
  });
  it("sends only the selected input source and normalized weights", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue({ ok: true, json: async () => ({ score: 75 }) });
    const controller = new AbortController();
    await analyzeDocuments(
      { ...doc(demoCV), file: new File(["ignored"], "old.pdf") },
      doc(demoJob),
      defaultWeights,
      false,
      controller.signal,
    );
    const request = fetchMock.mock.calls[0][1];
    expect(request.body.get("cv_text")).toBe(demoCV);
    expect(request.body.has("cv_file")).toBe(false);
    expect(JSON.parse(request.body.get("weights")).hard_skills).toBe(0.5);
    expect(request.signal).toBe(controller.signal);
    fetchMock.mockRestore();
  });
});
describe("Safe exports", () => {
  it("escapes markup and spreadsheet formula prefixes", () => {
    expect(escapeHTML('<script>"&')).toBe("&lt;script&gt;&quot;&amp;");
    const report = csvReport({
      gaps: [
        {
          skill: "Python",
          status: "Couvert",
          required: true,
          evidence: '=HYPERLINK("bad")',
        },
      ],
    });
    expect(report).toContain("'=HYPERLINK");
  });
  it("creates printable standalone HTML without trusting model markup", () => {
    const result = {
      score: 80,
      gaps: [],
      components: {},
      effective_weights: {},
      recommendations: {
        summary: "<script>bad()</script>",
        actions: [],
        rewrites: [],
        source: "local",
      },
      warnings: [],
      embedding_model: "test",
      timings_ms: { total: 20 },
    };
    expect(htmlReport(result)).not.toContain("<script>");
    expect(htmlReport(result)).toContain("&lt;script&gt;");
    expect(htmlReport(result)).toContain("@media print");
  });
});
