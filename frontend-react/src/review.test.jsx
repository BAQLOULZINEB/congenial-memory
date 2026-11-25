import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { analyzeDocuments } from "./api";
import { demoExamples } from "./demo";
const auth = vi.hoisted(() => ({ id: null }));
vi.mock("./auth/context/AuthContext", () => ({
  useAuth: () => ({ utilisateur: auth.id == null ? null : { id: auth.id, nom: "Test" }, deconnexion: vi.fn() }),
}));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal()),
  analyzeDocuments: vi.fn(),
}));

const result = {
  score: 50,
  components: Object.fromEntries(
    ["hard_skills", "experience", "education", "soft_skills"].map((key) => [
      key,
      {
        score: key === "hard_skills" ? 50 : null,
        explanation: "Critère vérifiable.",
      },
    ]),
  ),
  effective_weights: {
    hard_skills: 1,
    experience: 0,
    education: 0,
    soft_skills: 0,
  },
  gaps: [
    {
      skill: "Python",
      status: "Couvert",
      category: "hard_skills",
      required: true,
      evidence: "Projet Python.",
    },
  ],
  recommendations: {
    summary: "Résultat de la candidature soumise.",
    source: "local",
    strengths: [],
    priorities: [],
    actions: [],
    rewrites: [],
  },
  timings_ms: { total: 100 },
  warnings: ["Vérifier les preuves."],
  embedding_model: "test-model",
  cv: { sections: { profile: "Profil envoyé." } },
  job: { sections: { profile: "Offre envoyée." } },
};

function deferred() {
  let resolve;
  const promise = new Promise((complete) => {
    resolve = complete;
  });
  return { promise, resolve };
}

function startPendingDemo() {
  const pending = deferred();
  analyzeDocuments.mockReturnValue(pending.promise);
  render(
    <MemoryRouter initialEntries={["/analyse"]}>
      <App />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Utiliser un exemple" }));
  fireEvent.click(
    screen.getByRole("button", { name: "Découvrir mon adéquation" }),
  );
  return pending;
}

beforeEach(() => {
  auth.id = null;
  sessionStorage.clear();
  vi.clearAllMocks();
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ status: "ready" }) }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Independent result provenance review", () => {
  it("restores a completed report after remount for the same account only", async () => {
    auth.id = 42;
    const pending = startPendingDemo();
    await act(async () => pending.resolve(result));
    await screen.findByText("Résultat de la candidature soumise.");
    cleanup();
    render(<MemoryRouter initialEntries={["/resultats"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Résultat de la candidature soumise.")).toBeInTheDocument();
    expect(screen.getByText(/candidature de démonstration/i)).toBeInTheDocument();
    cleanup();
    auth.id = 43;
    render(<MemoryRouter initialEntries={["/resultats"]}><App /></MemoryRouter>);
    expect(await screen.findByText("Votre premier bilan vous attend.")).toBeInTheDocument();
  });
  it("cycles all examples, fills both documents, and wraps back to the first", () => {
    render(<MemoryRouter initialEntries={["/analyse"]}><App /></MemoryRouter>);
    for (let i = 0; i <= demoExamples.length; i++) {
      fireEvent.click(screen.getByRole("button", { name: i === 0 ? "Utiliser un exemple" : /Autre exemple/ }));
      const expected = demoExamples[i % demoExamples.length];
      expect(screen.getByRole("textbox", { name: "Texte du CV" })).toHaveValue(expected.cv);
      expect(screen.getByRole("textbox", { name: "Texte de l’offre" })).toHaveValue(expected.job);
    }
  });
  it("marks a completed old request stale when settings change while it runs", async () => {
    const pending = startPendingDemo();
    expect(analyzeDocuments).toHaveBeenCalledOnce();
    fireEvent.click(
      screen.getByRole("link", { name: "Paramètres", exact: true }),
    );
    fireEvent.click(
      screen.getByRole("checkbox", { name: "Utiliser le modèle de langage" }),
    );
    await act(async () => pending.resolve(result));
    expect(
      await screen.findByText(/ce bilan correspond au dernier envoi/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/candidature de démonstration/i),
    ).toBeInTheDocument();
  });

  it("keeps the submitted demo label after the current draft is edited", async () => {
    const pending = startPendingDemo();
    await act(async () => pending.resolve(result));
    await screen.findByRole("heading", {
      name: "Voici ce qui vous rapproche du poste.",
    });
    fireEvent.click(screen.getByRole("link", { name: "Nouvelle analyse" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Texte du CV" }), {
      target: {
        value: "Un autre parcours professionnel avec Python, SQL et Docker.",
      },
    });
    fireEvent.click(screen.getByRole("link", { name: /Mes résultats/ }));
    expect(
      screen.getByText(/candidature de démonstration/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/ce bilan correspond au dernier envoi/i),
    ).toBeInTheDocument();
  });

  it("keeps a newer request active when a cancelled older request finishes", async () => {
    const oldRequest = startPendingDemo();
    fireEvent.click(screen.getByRole("button", { name: "Annuler" }));
    const newRequest = deferred();
    analyzeDocuments.mockReturnValue(newRequest.promise);
    fireEvent.click(screen.getByRole("button", { name: "Découvrir mon adéquation" }));
    expect(analyzeDocuments).toHaveBeenCalledTimes(2);
    await act(async () => oldRequest.resolve(result));
    expect(screen.getByRole("button", { name: "Analyse en cours…" })).toBeDisabled();
    expect(analyzeDocuments.mock.calls[1][4].aborted).toBe(false);
    const newResult = { ...result, recommendations: { ...result.recommendations, summary: "Nouvelle analyse correcte." } };
    await act(async () => newRequest.resolve(newResult));
    expect(await screen.findByText("Nouvelle analyse correcte.")).toBeInTheDocument();
    expect(screen.queryByText("Résultat de la candidature soumise.")).not.toBeInTheDocument();
  });

  it("does not publish a response that arrives after cancellation", async () => {
    const pending = startPendingDemo();
    const signal = analyzeDocuments.mock.calls[0][4];
    fireEvent.click(screen.getByRole("button", { name: "Annuler" }));
    expect(signal.aborted).toBe(true);
    await act(async () => pending.resolve(result));
    fireEvent.click(screen.getByRole("link", { name: /Mes résultats/ }));
    await waitFor(() =>
      expect(
        screen.getByRole("heading", {
          name: "Votre premier bilan vous attend.",
        }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.queryByText("Résultat de la candidature soumise."),
    ).not.toBeInTheDocument();
  });
});
